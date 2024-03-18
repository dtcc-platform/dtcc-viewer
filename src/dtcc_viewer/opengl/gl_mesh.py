import numpy as np
import pyrr
import time
from pprint import pp
from string import Template
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl.interaction import Action
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.utils import Shading, BoundingBox
from dtcc_viewer.opengl.environment import Environment
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import Submeshes
from dtcc_viewer.opengl.wrp_data import MeshDataWrapper

from dtcc_viewer.opengl.parameters import (
    GuiParameters,
    GuiParametersMesh,
    GuiParametersModel,
)

from dtcc_viewer.shaders.shaders_mesh_shadows import (
    vertex_shader_shadows,
    fragment_shader_shadows,
    vertex_shader_shadow_map,
    fragment_shader_shadow_map,
)

from dtcc_viewer.shaders.shaders_mesh_diffuse import (
    vertex_shader_diffuse,
    fragment_shader_diffuse,
)

from dtcc_viewer.shaders.shaders_mesh_ambient import (
    vertex_shader_ambient,
    fragment_shader_ambient,
)

from dtcc_viewer.shaders.shaders_lines import (
    vertex_shader_lines,
    fragment_shader_lines,
)

from dtcc_viewer.shaders.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)


class GlMesh:
    """Represents a 3D mesh in OpenGL and provides methods for rendering.

    This class handles the rendering of mesh data using OpenGL. It provides methods to
    set up the rendering environment, binding and rendering with a range of different
    shaders, and perform the necessary transformations camera interaction, perspective
    projection and other features needed for visualization.

    """

    # Mesh based parameters
    VAO_triangels: int  # OpenGL Vertex attribut object for triangles
    VBO_triangels: int  # OpenGL Vertex buffer object for triangles
    EBO_triangels: int  # OpenGL Element buffer object for triangles
    VAO_edge: int  # OpenGL Vertex attribut object for wireframe edges
    VBO_edge: int  # OpenGL Vertex buffer object for wireframe edges
    EBO_edge: int  # OpenGL Element buffer object for wireframe edges

    guip: GuiParametersMesh  # Information used by the Gui
    vertices: (
        np.ndarray
    )  # [n_vertices x 10] each row (x, y, z, r, g, b, nx, ny, nz, id)
    faces: np.ndarray  # [n_faces x 3] each row has three vertex indices
    edges: np.ndarray  # [n_edges x 2] each row has

    n_vertices: int  # Number of vertices
    n_faces: int  # Number of faces

    bb: np.ndarray  # Bounding box [xmin, xmax, ymin, ymax, zmin, zmax]
    bb_local: BoundingBox
    bb_global: BoundingBox

    uloc_line: dict  # Uniform locations for the lines shader
    uloc_ambi: dict  # Uniform locations for the ambient shader
    uloc_diff: dict  # Uniform locations for the diffuse shader
    uloc_shdw: dict  # Uniform locations for the shadow shader
    uloc_shmp: dict  # Uniform locations for the shadow shader

    shader_line: int  # Shader program for the lines
    shader_ambi: int  # Shader program for ambient mesh rendering
    shader_diff: int  # Shader program for diffuse mesh rendering
    shader_shdw: int  # Shader program for rendering of diffuse mesh with shadow map
    shader_shmp: int  # Shader program for rendering of diffuse mesh with shadow map

    # Scene based parameters
    diameter_xy: float  # Size of the model as diameter
    radius_xy: float  # Size of model as radius
    light_position: np.ndarray  # position of light that casts shadows [1 x 3]
    light_color: np.ndarray  # color of scene light [1 x 3]
    loop_counter: int  # loop counter for animation of scene light source

    submeshes: Submeshes  # Defines clickable objects and their metadata in the mesh

    cast_shadows: bool  # If the mesh should cast shadows
    recieve_shadows: bool  # If the mesh should recieve shadows

    data_texture: int  # Texture for data
    data_wrapper: MeshDataWrapper  # Data wrapper for the mesh
    texture_slot: int  # GL_TEXTURE0, GL_TEXTURE1, etc.
    texture_int: int  # Texture index 0 for GL_TEXTURE0, 1 for GL_TEXTURE1, etc.

    def __init__(self, mesh_wrapper: MeshWrapper):
        """Initialize the MeshGL object with vertex, face, and edge information."""

        self.name = mesh_wrapper.name
        self.vertices = mesh_wrapper.vertices
        self.faces = mesh_wrapper.faces
        self.edges = mesh_wrapper.edges
        self.submeshes = mesh_wrapper.submeshes
        self.data_wrapper = mesh_wrapper.data_wrapper

        self.n_vertices = len(self.vertices) // 9
        self.n_faces = len(self.faces) // 3

        data_mat_dict = self.data_wrapper.data_mat_dict
        data_val_caps = self.data_wrapper.data_value_caps
        self.guip = GuiParametersMesh(self.name, data_mat_dict, data_val_caps)

        self.cast_shadows = True
        self.recieve_shadows = True

        self.bb_local = mesh_wrapper.bb_local
        self.bb_global = mesh_wrapper.bb_global

        self.uloc_line = {}
        self.uloc_ambi = {}
        self.uloc_diff = {}
        self.uloc_shdw = {}
        self.uloc_shmp = {}

        self.texture_slot = None
        self.texture_int = None

    def preprocess(self):
        self._create_textures()
        self._create_geometry()
        self._create_shaders()

    def get_vertex_ids(self):
        return self.vertices[8::9]

    def get_average_vertex_position(self, indices):
        if np.max(indices) > self.n_vertices or np.min(indices) < 0:
            warning("Index out of bounds")
            return None

        x = self.vertices[indices * 9 + 0]
        y = self.vertices[indices * 9 + 1]
        z = self.vertices[indices * 9 + 2]

        avrg_pt = np.array([np.mean(x), np.mean(y), np.mean(z)])
        pts = np.column_stack((x, y, z))
        radius = np.max(np.linalg.norm(pts - avrg_pt, axis=1))

        return avrg_pt, radius

    def _create_textures(self) -> None:
        self._create_data_texture()

    def _create_data_texture(self) -> None:
        """Create texture for data."""

        self.data_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

        # Configure texture filtering and wrapping options
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        width = self.data_wrapper.col_count
        height = self.data_wrapper.row_count
        key = self.data_wrapper.get_keys()[0]
        default_data = self.data_wrapper.data_mat_dict[key]

        # Transfer data to the texture
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_R32F,
            width,
            height,
            0,
            GL_RED,
            GL_FLOAT,
            default_data,
        )

    def _create_geometry(self) -> None:
        """Set up vertex and element buffers for mesh rendering."""
        self._create_lines()
        self._create_triangels()

    def _create_lines(self) -> None:
        """Set up vertex and element buffers for wireframe rendering."""
        # -------------- EDGES for wireframe display ---------------- #
        self.VAO_edge = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_edge)

        # Vertex buffer
        size = len(self.vertices) * 4
        self.VBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_edge)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.edges) * 4
        self.EBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_edge)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.edges, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Texel indices
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        # Ignoring normals and id's

        glBindVertexArray(0)

    def _create_triangels(self) -> None:
        """Set up vertex and element buffers for mesh rendering."""
        # ----------------- TRIANGLES for shaded display ------------------#

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO_triangels = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_triangels)

        # Vertex buffer
        size = len(self.vertices) * 4  # Size in bytes
        self.VBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_triangels)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.faces) * 4  # Size in bytes
        self.EBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_triangels)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.faces, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Texel indices for texture sampling
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        # Normals
        glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(20))

        # Id for clickability
        glEnableVertexAttribArray(3)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(32))

        glBindVertexArray(0)

    def _create_shaders(self) -> None:
        """Create shaders for mesh rendering."""
        self._create_shader_lines()
        self._create_shader_ambient()
        self._create_shader_diffuse()
        self._create_shader_shadow_map()
        self._create_shader_shadows()

    def _create_shader_lines(self) -> None:
        """Create shader for wireframe rendering."""

        vertex_shader = vertex_shader_lines
        fragment_shader = fragment_shader_lines

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_rainbow,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_turbo,
            color_map_4=color_map_viridis,
        )

        self._bind_vao_lines()
        self.shader_line = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader_line)

        self.uloc_line["model"] = glGetUniformLocation(self.shader_line, "model")
        self.uloc_line["view"] = glGetUniformLocation(self.shader_line, "view")
        self.uloc_line["project"] = glGetUniformLocation(self.shader_line, "project")
        self.uloc_line["color_by"] = glGetUniformLocation(self.shader_line, "color_by")
        self.uloc_line["color_inv"] = glGetUniformLocation(
            self.shader_line, "color_inv"
        )
        self.uloc_line["clip_x"] = glGetUniformLocation(self.shader_line, "clip_x")
        self.uloc_line["clip_y"] = glGetUniformLocation(self.shader_line, "clip_y")
        self.uloc_line["clip_z"] = glGetUniformLocation(self.shader_line, "clip_z")
        self.uloc_line["cmap_idx"] = glGetUniformLocation(self.shader_line, "cmap_idx")
        self.uloc_line["data_idx"] = glGetUniformLocation(self.shader_line, "data_idx")
        self.uloc_line["data_min"] = glGetUniformLocation(self.shader_line, "data_min")
        self.uloc_line["data_max"] = glGetUniformLocation(self.shader_line, "data_max")
        self.uloc_line["data_tex"] = glGetUniformLocation(self.shader_line, "data_tex")

    def _create_shader_ambient(self) -> None:
        """Create shader for ambient shading."""

        vertex_shader = vertex_shader_ambient
        fragment_shader = fragment_shader_ambient

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_rainbow,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_turbo,
            color_map_4=color_map_viridis,
        )

        self._bind_vao_triangels()
        self.shader_ambi = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_ambi)

        self.uloc_ambi["model"] = glGetUniformLocation(self.shader_ambi, "model")
        self.uloc_ambi["view"] = glGetUniformLocation(self.shader_ambi, "view")
        self.uloc_ambi["project"] = glGetUniformLocation(self.shader_ambi, "project")
        self.uloc_ambi["color_by"] = glGetUniformLocation(self.shader_ambi, "color_by")
        self.uloc_ambi["color_inv"] = glGetUniformLocation(
            self.shader_ambi, "color_inv"
        )
        self.uloc_ambi["clip_x"] = glGetUniformLocation(self.shader_ambi, "clip_x")
        self.uloc_ambi["clip_y"] = glGetUniformLocation(self.shader_ambi, "clip_y")
        self.uloc_ambi["clip_z"] = glGetUniformLocation(self.shader_ambi, "clip_z")
        self.uloc_ambi["cmap_idx"] = glGetUniformLocation(self.shader_ambi, "cmap_idx")
        self.uloc_ambi["data_idx"] = glGetUniformLocation(self.shader_ambi, "data_idx")
        self.uloc_ambi["data_min"] = glGetUniformLocation(self.shader_ambi, "data_min")
        self.uloc_ambi["data_max"] = glGetUniformLocation(self.shader_ambi, "data_max")
        self.uloc_ambi["data_tex"] = glGetUniformLocation(self.shader_ambi, "data_tex")
        self.uloc_ambi["picked_id"] = glGetUniformLocation(
            self.shader_ambi, "picked_id"
        )

    def _create_shader_diffuse(self) -> None:
        """Create shader for diffuse shading."""

        vertex_shader = vertex_shader_diffuse
        fragment_shader = fragment_shader_diffuse

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_rainbow,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_turbo,
            color_map_4=color_map_viridis,
        )

        self._bind_vao_triangels()
        self.shader_diff = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_diff)

        self.uloc_diff["model"] = glGetUniformLocation(self.shader_diff, "model")
        self.uloc_diff["view"] = glGetUniformLocation(self.shader_diff, "view")
        self.uloc_diff["project"] = glGetUniformLocation(self.shader_diff, "project")
        self.uloc_diff["color_by"] = glGetUniformLocation(self.shader_diff, "color_by")
        self.uloc_diff["color_inv"] = glGetUniformLocation(
            self.shader_diff, "color_inv"
        )

        self.uloc_diff["light_color"] = glGetUniformLocation(
            self.shader_diff, "light_color"
        )
        self.uloc_diff["light_pos"] = glGetUniformLocation(
            self.shader_diff, "light_pos"
        )
        self.uloc_diff["view_pos"] = glGetUniformLocation(self.shader_diff, "view_pos")

        self.uloc_diff["clip_x"] = glGetUniformLocation(self.shader_diff, "clip_x")
        self.uloc_diff["clip_y"] = glGetUniformLocation(self.shader_diff, "clip_y")
        self.uloc_diff["clip_z"] = glGetUniformLocation(self.shader_diff, "clip_z")
        self.uloc_diff["cmap_idx"] = glGetUniformLocation(self.shader_diff, "cmap_idx")
        self.uloc_diff["data_idx"] = glGetUniformLocation(self.shader_diff, "data_idx")
        self.uloc_diff["data_min"] = glGetUniformLocation(self.shader_diff, "data_min")
        self.uloc_diff["data_max"] = glGetUniformLocation(self.shader_diff, "data_max")
        self.uloc_diff["data_tex"] = glGetUniformLocation(self.shader_diff, "data_tex")
        self.uloc_diff["picked_id"] = glGetUniformLocation(
            self.shader_diff, "picked_id"
        )

    def _create_shader_shadow_map(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader_shmp = compileProgram(
            compileShader(vertex_shader_shadow_map, GL_VERTEX_SHADER),
            compileShader(fragment_shader_shadow_map, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shmp)

        self.uloc_shmp["model"] = glGetUniformLocation(self.shader_shmp, "model")
        self.uloc_shmp["lsm"] = glGetUniformLocation(self.shader_shmp, "lsm")

    def _create_shader_shadows(self) -> None:
        """Create shader for shading with shadows."""

        vertex_shader = vertex_shader_shadows
        fragment_shader = fragment_shader_shadows

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_rainbow,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_turbo,
            color_map_4=color_map_viridis,
        )

        self._bind_vao_triangels()
        self.shader_shdw = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shdw)

        self.uloc_shdw["model"] = glGetUniformLocation(self.shader_shdw, "model")
        self.uloc_shdw["view"] = glGetUniformLocation(self.shader_shdw, "view")
        self.uloc_shdw["project"] = glGetUniformLocation(self.shader_shdw, "project")
        self.uloc_shdw["color_by"] = glGetUniformLocation(self.shader_shdw, "color_by")
        self.uloc_shdw["color_inv"] = glGetUniformLocation(
            self.shader_shdw, "color_inv"
        )
        self.uloc_shdw["clip_x"] = glGetUniformLocation(self.shader_shdw, "clip_x")
        self.uloc_shdw["clip_y"] = glGetUniformLocation(self.shader_shdw, "clip_y")
        self.uloc_shdw["clip_z"] = glGetUniformLocation(self.shader_shdw, "clip_z")
        self.uloc_shdw["cmap_idx"] = glGetUniformLocation(self.shader_shdw, "cmap_idx")
        self.uloc_shdw["data_idx"] = glGetUniformLocation(self.shader_shdw, "data_idx")
        self.uloc_shdw["data_min"] = glGetUniformLocation(self.shader_shdw, "data_min")
        self.uloc_shdw["data_max"] = glGetUniformLocation(self.shader_shdw, "data_max")
        self.uloc_shdw["data_tex"] = glGetUniformLocation(self.shader_shdw, "data_tex")
        self.uloc_shdw["light_pos"] = glGetUniformLocation(
            self.shader_shdw, "light_pos"
        )
        self.uloc_shdw["view_pos"] = glGetUniformLocation(self.shader_shdw, "view_pos")
        self.uloc_shdw["light_color"] = glGetUniformLocation(
            self.shader_shdw, "light_color"
        )
        self.uloc_shdw["lsm"] = glGetUniformLocation(self.shader_shdw, "lsm")
        self.uloc_shdw["picked_id"] = glGetUniformLocation(
            self.shader_shdw, "picked_id"
        )

    def _update_data_texture(self):
        index = self.guip.data_idx
        key = self.data_wrapper.get_keys()[index]
        width = self.data_wrapper.col_count
        height = self.data_wrapper.row_count
        data = self.data_wrapper.data_mat_dict[key]
        tic = time.perf_counter()

        self._bind_data_texture()
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RED, GL_FLOAT, data)
        self._unbind_data_texture()

        toc = time.perf_counter()
        info(f"Data texture updated. Time elapsed: {toc - tic:0.4f} seconds")

    def update_color_data(self):
        if self.guip.update_data_tex:
            self._update_data_texture()
            self.guip.update_data_tex = False

    def update_color_caps(self):
        if self.guip.update_caps:
            self.guip.calc_data_min_max()
            self.guip.update_caps = False

    def render_lines(
        self,
        action: Action,
        env: Environment,
        gguip: GuiParameters,
        mguip: GuiParametersModel,
        ws_pass=0,
    ):
        """Render wireframe lines of the mesh.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._bind_shader_lines()
        self._bind_data_texture()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = action.camera.get_view_matrix()
        proj = action.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_line["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_line["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_line["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(gguip, mguip, ws_pass)

        glUniform1i(self.uloc_line["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_line["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_line["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_line["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_line["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_line["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_line["data_tex"], self.texture_int)

        self._lines_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def render_ambient(
        self,
        action: Action,
        gguip: GuiParameters,
        mguip: GuiParametersModel,
    ) -> None:
        """Render the mesh with ambient shading."""
        self._bind_shader_ambient()
        self._bind_data_texture()

        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = action.camera.get_view_matrix()
        proj = action.camera.get_perspective_matrix()

        glUniformMatrix4fv(self.uloc_ambi["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_ambi["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_ambi["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(gguip, mguip)

        glUniform1i(self.uloc_ambi["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_ambi["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_ambi["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_ambi["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_ambi["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_ambi["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_ambi["picked_id"], action.picked_id)
        glUniform1i(self.uloc_ambi["data_tex"], self.texture_int)

        self.triangles_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def render_diffuse(
        self,
        action: Action,
        env: Environment,
        gguip: GuiParameters,
        mguip: GuiParametersModel,
        ws_pass=0,
    ):
        """Render the mesh with diffuse shading."""
        self._bind_shader_diffuse()
        self._bind_data_texture()

        # MVP calcs
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix()
        proj = action.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_diff["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_diff["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_diff["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(gguip, mguip, ws_pass)

        glUniform1i(self.uloc_diff["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_diff["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_diff["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_diff["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_diff["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_diff["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_diff["picked_id"], action.picked_id)
        glUniform1i(self.uloc_diff["data_tex"], self.texture_int)

        view_pos = action.camera.position
        glUniform3fv(self.uloc_diff["view_pos"], 1, view_pos)

        # Set light uniforms
        glUniform3fv(self.uloc_diff["light_color"], 1, env.light_col)
        glUniform3fv(self.uloc_diff["light_pos"], 1, env.light_pos)

        self.triangles_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def render_wireshaded(
        self,
        action: Action,
        env: Environment,
        gguip: GuiParameters,
        mguip: GuiParametersModel,
    ) -> None:
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        self.render_diffuse(action, env, gguip, mguip, ws_pass=1)
        glDisable(GL_POLYGON_OFFSET_FILL)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        self.render_lines(action, env, gguip, mguip, ws_pass=2)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def render_shadows_pass1(self, lsm: np.ndarray):
        glUseProgram(self.shader_shmp)
        glUniformMatrix4fv(self.uloc_shmp["lsm"], 1, GL_FALSE, lsm)
        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.uloc_shmp["model"], 1, GL_FALSE, translation)
        self.triangles_draw_call()

    def render_shadows_pass2(
        self,
        action: Action,
        env: Environment,
        gguip: GuiParameters,
        mguip: GuiParametersModel,
        lsm: np.ndarray,
    ) -> None:
        # Setup uniforms for rendering with shadows
        self._bind_shader_shadows()
        self._bind_data_texture()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = action.camera.get_view_matrix()
        proj = action.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_shdw["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_shdw["project"], 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.uloc_shdw["view"], 1, GL_FALSE, view)

        self._set_clipping_uniforms(gguip, mguip)

        glUniform1i(self.uloc_shdw["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_shdw["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_shdw["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_shdw["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_shdw["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_shdw["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_shdw["picked_id"], action.picked_id)
        glUniform1i(self.uloc_shdw["data_tex"], self.texture_int)

        # Set light uniforms
        glUniform3fv(self.uloc_shdw["view_pos"], 1, action.camera.position)
        glUniform3fv(self.uloc_shdw["light_color"], 1, env.light_col)
        glUniform3fv(self.uloc_shdw["light_pos"], 1, env.light_pos)

        # Set light space matrix
        glUniformMatrix4fv(self.uloc_shdw["lsm"], 1, GL_FALSE, lsm)

        self.triangles_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def triangles_draw_call(self):
        """Bind the vertex array object and calling draw function for triangles"""
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.faces), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    def _lines_draw_call(self):
        """Bind the vertex array object and calling draw function for lines"""
        self._bind_vao_lines()
        glDrawElements(GL_LINES, len(self.edges), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    def _bind_data_texture(self):
        """Bind the data texture."""
        glActiveTexture(self.texture_slot)
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

    def _bind_vao_triangels(self) -> None:
        """Bind the vertex array object for triangle rendering."""
        glBindVertexArray(self.VAO_triangels)

    def _bind_vao_lines(self) -> None:
        """Bind the vertex array object for wireframe rendering."""
        glBindVertexArray(self.VAO_edge)

    def _unbind_data_texture(self):
        """Unbind the currently bound data texture."""
        glActiveTexture(self.texture_slot)
        glBindTexture(GL_TEXTURE_2D, 0)

    def _unbind_vao(self) -> None:
        """Unbind the currently bound vertex array object."""
        glBindVertexArray(0)

    def _bind_shader_lines(self) -> None:
        """Bind the shader for wireframe rendering."""
        glUseProgram(self.shader_line)

    def _bind_shader_ambient(self) -> None:
        """Bind the shader for basic shading."""
        glUseProgram(self.shader_ambi)

    def _bind_shader_diffuse(self) -> None:
        """Bind the shader for diffuse shading."""
        glUseProgram(self.shader_diff)

    def _bind_shader_shadows(self) -> None:
        """Bind the shader for shading with shadows."""
        glUseProgram(self.shader_shdw)

    def _unbind_shader(self) -> None:
        """Unbind the currently bound shader."""
        glUseProgram(0)

    def _set_clipping_uniforms(
        self, gguip: GuiParameters, mguip: GuiParametersModel, ws_pass: int = 0
    ):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        if mguip.shading == Shading.wireframe or ws_pass == 2:
            glUniform1f(self.uloc_line["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_line["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_line["clip_z"], (zdom * gguip.clip_dist[2]))
        elif mguip.shading == Shading.ambient:
            glUniform1f(self.uloc_ambi["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_ambi["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_ambi["clip_z"], (zdom * gguip.clip_dist[2]))
        elif mguip.shading == Shading.diffuse or ws_pass == 1:
            glUniform1f(self.uloc_diff["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_diff["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_diff["clip_z"], (zdom * gguip.clip_dist[2]))
        elif mguip.shading == Shading.shadows:
            glUniform1f(self.uloc_shdw["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_shdw["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_shdw["clip_z"], (zdom * gguip.clip_dist[2]))
