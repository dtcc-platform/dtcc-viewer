import numpy as np
import pyrr
import time
from pprint import pp
from string import Template
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.utils import Shading, BoundingBox
from dtcc_viewer.opengl.environment import Environment
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.data_wrapper import MeshDataWrapper
from dtcc_viewer.opengl.gl_object import GlObject

from dtcc_viewer.opengl.parameters import (
    GuiParametersGlobal,
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

from dtcc_viewer.shaders.shaders_mesh_lines import (
    vertex_shader_lines,
    fragment_shader_lines,
)

from dtcc_viewer.shaders.shaders_mesh_normals import (
    vertex_shader_normals,
    geometry_shader_vertexnormals,
    geometry_shader_facenormals,
    fragment_shader_normals,
)

from dtcc_viewer.shaders.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)


class GlMesh(GlObject):
    """Represents a 3D mesh in OpenGL and provides methods for rendering.

    This class handles the rendering of mesh data using OpenGL. It provides methods to
    set up the rendering environment, binding and rendering with a range of different
    shaders, and perform the necessary transformations camera interaction, perspective
    and orthographic projection and other features needed for visualization.

    The GlMesh class has a setup with VAO, VBO, EBO, vertices and indices in a array
    called faces for rendering triangles with a range of different shaders. There is
    also an other setup of VAO, VBO, EBO for using the same vertices and rendering
    lines where the indices are stored in an array called edges.

    Attributes
    ----------
    VAO_triangels : int
        OpenGL Vertex attribut object for triangles
    VBO_triangels : int
        OpenGL Vertex buffer object for triangles
    EBO_triangels : int
        OpenGL Element buffer object for triangles
    VAO_edge : int
        OpenGL Vertex attribut object for wireframe edges
    VBO_edge : int
        OpenGL Vertex buffer object for wireframe edges
    EBO_edge : int
        OpenGL Element buffer object for wireframe edges
    guip : GuiParametersMesh
        Information used by the Gui
    vertices : np.ndarray
        1D array of vertices with the structure  [x, y, z, tx, ty, nx, ny, nz, id, ...]
    faces : np.ndarray
        1D array vertex of indices. Each face has 3 unique vertices [f1_v1, f1_v2, f1_v3, f2_v1, ...]
    edges : np.ndarray
        1D array of vertex indices. Each edge has 2 unique vertices [e1_v1, e1_v2, e2_v1, ...]
    n_vertices : int
        Number of vertices
    n_faces : int
        Number of faces
    n_edges : int
        Number of edges
    bb_local : BoundingBox
        Bounding box for this particular mesh
    bb_global : BoundingBox
        Bounding box for the entire scene
    uloc_line : dict
        Uniform locations for the lines shader
    uloc_ambi : dict
        Uniform locations for the ambient shader
    uloc_diff : dict
        Uniform locations for the diffuse shader
    uloc_shdw : dict
        Uniform locations for the shadow shader
    uloc_shmp : dict
        Uniform locations for the shadow shader
    uloc_fnor : dict
        Uniform locations for the face normals shader
    uloc_vnor : dict
        Uniform locations for the vertex normals shader
    shader_line : int
        Shader program for the lines
    shader_ambi : int
        Shader program for ambient mesh rendering
    shader_diff : int
        Shader program for diffuse mesh rendering
    shader_shdw : int
        Shader program for rendering of diffuse mesh with shadow map
    shader_shmp : int
        Shader program for rendering of diffuse mesh with shadow map
    shader_fnor : int
        Shader program for rendering face normals
    shader_vnor : int
        Shader program for rendering vertex normals
    diameter_xy : float
        Size of the model as diameter
    radius_xy : float
        Size of model as radius
    parts : Parts
        Defines clickable mesh parts and their attributes
    """

    VAO_triangels: int
    VBO_triangels: int
    EBO_triangels: int
    VAO_edge: int
    VBO_edge: int
    EBO_edge: int
    guip: GuiParametersMesh
    vertices: np.ndarray
    faces: np.ndarray
    edges: np.ndarray
    n_vertices: int
    n_faces: int
    n_edges: int
    bb_local: BoundingBox
    bb_global: BoundingBox
    uloc_line: dict
    uloc_ambi: dict
    uloc_diff: dict
    uloc_shdw: dict
    uloc_shmp: dict
    uloc_fnor: dict
    uloc_vnor: dict
    shader_line: int
    shader_ambi: int
    shader_diff: int
    shader_shdw: int
    shader_shmp: int
    shader_fnor: int
    shader_vnor: int
    diameter_xy: float
    radius_xy: float
    parts: Parts
    cast_shadows: bool
    receive_shadows: bool

    def __init__(self, mesh_wrapper: MeshWrapper):
        """Initialize the MeshGL object with vertex, face, and edge information."""

        self.name = mesh_wrapper.name
        self.vertices = mesh_wrapper.vertices
        self.faces = mesh_wrapper.faces
        self.edges = mesh_wrapper.edges
        self.parts = mesh_wrapper.parts
        self.data_wrapper = mesh_wrapper.data_wrapper

        # 9 data points per vertex: [x, y, z, tx, ty, nx, ny, nz, id]
        self.n_vertices = len(self.vertices) // 9
        # 3 indices per face: [f1_v1, f1_v2, f1_v3]
        self.n_faces = len(self.faces) // 3
        # 2 indices per edge: [e1_v1, e1_v2]
        self.n_edges = len(self.edges) // 2

        data_mat_dict = self.data_wrapper.data_mat_dict
        data_min_max = self.data_wrapper.data_min_max
        self.guip = GuiParametersMesh(self.name, data_mat_dict, data_min_max)

        self.bb_local = mesh_wrapper.bb_local
        self.bb_global = mesh_wrapper.bb_global

        self.uloc_line = {}
        self.uloc_ambi = {}
        self.uloc_diff = {}
        self.uloc_shdw = {}
        self.uloc_shmp = {}
        self.uloc_fnor = {}
        self.uloc_vnor = {}

        self.texture_slot = None
        self.texture_idx = None

        self.cast_shadows = True
        self.receive_shadows = True

    def get_vertex_ids(self):
        """Get the vertex ids from the vertices array."""
        return self.vertices[8::9]

    def get_average_vertex_position(self, indices):
        """Get the average position of a set of vertices."""
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
        """Create textures for data."""
        self._create_data_texture()

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

        # Normals indices
        glEnableVertexAttribArray(2)  # 2 is the layout location for the vertex shader
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(20))

        # Ids
        glEnableVertexAttribArray(3)  # 2 is the layout location for the vertex shader
        glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(32))

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
        self._create_shader_normals()

    def _create_shader_lines(self) -> None:
        """Create shader for wireframe rendering."""

        vertex_shader = vertex_shader_lines
        fragment_shader = fragment_shader_lines

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_turbo,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_rainbow,
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
        self.uloc_line["picked_id"] = glGetUniformLocation(
            self.shader_line, "picked_id"
        )

    def _create_shader_ambient(self) -> None:
        """Create shader for ambient shading."""

        vertex_shader = vertex_shader_ambient
        fragment_shader = fragment_shader_ambient

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_turbo,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_rainbow,
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
            color_map_0=color_map_turbo,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_rainbow,
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
            color_map_0=color_map_turbo,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_rainbow,
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

    def _create_shader_normals(self) -> None:
        """Create shaders for rendering normals."""

        # Face normal shader
        self.shader_fnor = compileProgram(
            compileShader(vertex_shader_normals, GL_VERTEX_SHADER),
            compileShader(geometry_shader_facenormals, GL_GEOMETRY_SHADER),
            compileShader(fragment_shader_normals, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_fnor)

        self.uloc_fnor["model"] = glGetUniformLocation(self.shader_fnor, "model")
        self.uloc_fnor["view"] = glGetUniformLocation(self.shader_fnor, "view")
        self.uloc_fnor["project"] = glGetUniformLocation(self.shader_fnor, "project")
        self.uloc_fnor["clip_x"] = glGetUniformLocation(self.shader_fnor, "clip_x")
        self.uloc_fnor["clip_y"] = glGetUniformLocation(self.shader_fnor, "clip_y")
        self.uloc_fnor["clip_z"] = glGetUniformLocation(self.shader_fnor, "clip_z")

        # Vertex normal shader
        self.shader_vnor = compileProgram(
            compileShader(vertex_shader_normals, GL_VERTEX_SHADER),
            compileShader(geometry_shader_vertexnormals, GL_GEOMETRY_SHADER),
            compileShader(fragment_shader_normals, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_vnor)

        self.uloc_vnor["model"] = glGetUniformLocation(self.shader_vnor, "model")
        self.uloc_vnor["view"] = glGetUniformLocation(self.shader_vnor, "view")
        self.uloc_vnor["project"] = glGetUniformLocation(self.shader_vnor, "project")
        self.uloc_vnor["clip_x"] = glGetUniformLocation(self.shader_vnor, "clip_x")
        self.uloc_vnor["clip_y"] = glGetUniformLocation(self.shader_vnor, "clip_y")
        self.uloc_vnor["clip_z"] = glGetUniformLocation(self.shader_vnor, "clip_z")

    def render_wireframe(
        self,
        action: Action,
        env: Environment,
        mguip: GuiParametersModel,
        ws_pass=0,
    ):
        """Render wireframe lines of the mesh."""
        self._bind_shader_lines()
        self._bind_data_texture()

        # MVP Calculations
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.uloc_line["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_line["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_line["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(action.gguip, mguip, ws_pass)

        glUniform1i(self.uloc_line["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_line["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_line["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_line["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_line["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_line["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_line["picked_id"], action.picked_id)
        glUniform1i(self.uloc_line["data_tex"], self.texture_idx)

        self._lines_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def render_ambient(
        self,
        action: Action,
        mguip: GuiParametersModel,
    ) -> None:
        """Render the mesh with ambient shading."""
        self._bind_shader_ambient()
        self._bind_data_texture()

        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)

        glUniformMatrix4fv(self.uloc_ambi["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_ambi["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_ambi["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(action.gguip, mguip)

        glUniform1i(self.uloc_ambi["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_ambi["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_ambi["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_ambi["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_ambi["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_ambi["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_ambi["picked_id"], action.picked_id)
        glUniform1i(self.uloc_ambi["data_tex"], self.texture_idx)

        self.triangles_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def render_diffuse(
        self,
        action: Action,
        env: Environment,
        mguip: GuiParametersModel,
        ws_pass=0,
    ):
        """Render the mesh with diffuse shading."""
        self._bind_shader_diffuse()
        self._bind_data_texture()

        # MVP calcs
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.uloc_diff["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_diff["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_diff["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(action.gguip, mguip, ws_pass)

        glUniform1i(self.uloc_diff["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_diff["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_diff["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_diff["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_diff["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_diff["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_diff["picked_id"], action.picked_id)
        glUniform1i(self.uloc_diff["data_tex"], self.texture_idx)

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
        mguip: GuiParametersModel,
    ) -> None:
        """Render the mesh with wireframe and shaded rendering."""

        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        self.render_diffuse(action, env, mguip, ws_pass=1)
        glDisable(GL_POLYGON_OFFSET_FILL)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        self.render_wireframe(action, env, mguip, ws_pass=2)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def render_shadows_pass1(self, lsm: np.ndarray):
        """Render the shadow map for the mesh."""
        glUseProgram(self.shader_shmp)
        glUniformMatrix4fv(self.uloc_shmp["lsm"], 1, GL_FALSE, lsm)
        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.uloc_shmp["model"], 1, GL_FALSE, translation)
        self.triangles_draw_call()

    def render_shadows_pass2(
        self,
        action: Action,
        env: Environment,
        mguip: GuiParametersModel,
        lsm: np.ndarray,
    ) -> None:
        """Render the mesh with shadows by sampling the shadowmap."""

        # Setup uniforms for rendering with shadows
        self._bind_shader_shadows()
        self._bind_data_texture()

        # MVP Calculations
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.uloc_shdw["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_shdw["project"], 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.uloc_shdw["view"], 1, GL_FALSE, view)

        self._set_clipping_uniforms(action.gguip, mguip)

        glUniform1i(self.uloc_shdw["color_by"], int(self.guip.color))
        glUniform1i(self.uloc_shdw["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uloc_shdw["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_shdw["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_shdw["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_shdw["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_shdw["picked_id"], action.picked_id)
        glUniform1i(self.uloc_shdw["data_tex"], self.texture_idx)

        # Set light uniforms
        glUniform3fv(self.uloc_shdw["view_pos"], 1, action.camera.position)
        glUniform3fv(self.uloc_shdw["light_color"], 1, env.light_col)
        glUniform3fv(self.uloc_shdw["light_pos"], 1, env.light_pos)

        # Set light space matrix
        glUniformMatrix4fv(self.uloc_shdw["lsm"], 1, GL_FALSE, lsm)

        self.triangles_draw_call()
        self._unbind_shader()
        self._unbind_data_texture()

    def render_normals(self, action: Action) -> None:
        """Render face and vertex normals of the mesh."""
        if self.guip.show_fnormals:
            self._render_face_normals(action)

        if self.guip.show_vnormals:
            self._render_vertex_normals(action)

    def _render_face_normals(self, action: Action) -> None:
        """Render face normals of the mesh."""
        self._bind_shader_fnormals()
        model = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)

        glUniformMatrix4fv(self.uloc_fnor["model"], 1, GL_FALSE, model)
        glUniformMatrix4fv(self.uloc_fnor["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_fnor["project"], 1, GL_FALSE, proj)

        (xdom, ydom, zdom) = self._get_clip_domains()
        glUniform1f(self.uloc_fnor["clip_x"], (xdom * action.gguip.clip_dist[0]))
        glUniform1f(self.uloc_fnor["clip_y"], (ydom * action.gguip.clip_dist[1]))
        glUniform1f(self.uloc_fnor["clip_z"], (zdom * action.gguip.clip_dist[2]))

        self.triangles_draw_call()
        self._unbind_shader()

    def _render_vertex_normals(self, action: Action) -> None:
        """Render vertex normals of the mesh."""
        self._bind_shader_vnormals()
        model = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)

        glUniformMatrix4fv(self.uloc_vnor["model"], 1, GL_FALSE, model)
        glUniformMatrix4fv(self.uloc_vnor["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_vnor["project"], 1, GL_FALSE, proj)

        (xdom, ydom, zdom) = self._get_clip_domains()
        glUniform1f(self.uloc_fnor["clip_x"], (xdom * action.gguip.clip_dist[0]))
        glUniform1f(self.uloc_fnor["clip_y"], (ydom * action.gguip.clip_dist[1]))
        glUniform1f(self.uloc_fnor["clip_z"], (zdom * action.gguip.clip_dist[2]))

        self.triangles_draw_call()
        self._unbind_shader()

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

    def _bind_vao_triangels(self) -> None:
        """Bind the vertex array object for triangle rendering."""
        glBindVertexArray(self.VAO_triangels)

    def _bind_vao_lines(self) -> None:
        """Bind the vertex array object for wireframe rendering."""
        glBindVertexArray(self.VAO_edge)

    def _unbind_vao(self) -> None:
        """Unbind the currently bound vertex array object."""
        glBindVertexArray(0)

    def _bind_shader_lines(self) -> None:
        """Bind the shader for wireframe rendering."""
        glUseProgram(self.shader_line)

    def _bind_shader_ambient(self) -> None:
        """Bind the shader for ambient shading."""
        glUseProgram(self.shader_ambi)

    def _bind_shader_diffuse(self) -> None:
        """Bind the shader for diffuse shading."""
        glUseProgram(self.shader_diff)

    def _bind_shader_shadows(self) -> None:
        """Bind the shader for shading with shadows."""
        glUseProgram(self.shader_shdw)

    def _bind_shader_fnormals(self) -> None:
        """Bind the shader for face normals rendering."""
        glUseProgram(self.shader_fnor)

    def _bind_shader_vnormals(self) -> None:
        """Bind the shader for vertex normals rendering."""
        glUseProgram(self.shader_vnor)

    def _unbind_shader(self) -> None:
        """Unbind the currently bound shader."""
        glUseProgram(0)

    def _set_clipping_uniforms(
        self,
        gguip: GuiParametersGlobal,
        mguip: GuiParametersModel,
        ws_pass: int = 0,
    ):
        """Set the clipping uniforms for the shader."""
        (xdom, ydom, zdom) = self._get_clip_domains()

        if mguip.shading == Shading.WIREFRAME or ws_pass == 2:
            glUniform1f(self.uloc_line["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_line["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_line["clip_z"], (zdom * gguip.clip_dist[2]))
        elif mguip.shading == Shading.AMBIENT:
            glUniform1f(self.uloc_ambi["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_ambi["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_ambi["clip_z"], (zdom * gguip.clip_dist[2]))
        elif mguip.shading == Shading.DIFFUSE or ws_pass == 1:
            glUniform1f(self.uloc_diff["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_diff["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_diff["clip_z"], (zdom * gguip.clip_dist[2]))
        elif mguip.shading == Shading.SHADOWS_STATIC:
            glUniform1f(self.uloc_shdw["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_shdw["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_shdw["clip_z"], (zdom * gguip.clip_dist[2]))

    def _get_clip_domains(self):
        """Get the clip domains for the mesh."""
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])
        return xdom, ydom, zdom
