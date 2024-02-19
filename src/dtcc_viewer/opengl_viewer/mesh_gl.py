import math
import glfw
import numpy as np
import pyrr
from pprint import pp
from string import Template
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.gui import GuiParameters, GuiParametersMesh
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper
from dtcc_viewer.opengl_viewer.utils import MeshShading, BoundingBox
from dtcc_viewer.opengl_viewer.utils import color_to_id, id_to_color
from dtcc_viewer.logging import info, warning

from dtcc_viewer.opengl_viewer.shaders_mesh_shadows import (
    vertex_shader_shadows,
    fragment_shader_shadows,
    vertex_shader_shadow_map,
    fragment_shader_shadow_map,
)

from dtcc_viewer.opengl_viewer.shaders_debug import (
    vertex_shader_debug_shadows,
    fragment_shader_debug_shadows,
    vertex_shader_debug_picking,
    fragment_shader_debug_picking,
)

from dtcc_viewer.opengl_viewer.shaders_mesh_diffuse import (
    vertex_shader_diffuse,
    fragment_shader_diffuse,
)

from dtcc_viewer.opengl_viewer.shaders_mesh_ambient import (
    vertex_shader_ambient,
    fragment_shader_ambient,
)

from dtcc_viewer.opengl_viewer.shaders_lines import (
    vertex_shader_lines,
    fragment_shader_lines,
)

from dtcc_viewer.opengl_viewer.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)

from dtcc_viewer.opengl_viewer.shaders_mesh_picking import (
    vertex_shader_picking,
    fragment_shader_picking,
)


class MeshGL:
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
    VAO_debug: int  # OpenGL Vertex attribut object for debug quad
    VBO_debug: int  # OpenGL Vertex buffer object for debug quad
    EBO_debug: int  # OpenGL Element buffer object for debug quad

    guip: GuiParametersMesh  # Information used by the Gui
    vertices: np.ndarray  # [n_vertices x 9] each row has (x, y, z, r, g, b, nx, ny, nz)
    faces: np.ndarray  # [n_faces x 3] each row has three vertex indices
    edges: np.ndarray  # [n_edges x 2] each row has

    bb: np.ndarray  # Bounding box [xmin, xmax, ymin, ymax, zmin, zmax]
    bb_local: BoundingBox
    bb_global: BoundingBox

    uloc_line: dict  # Uniform locations for the lines shader
    uloc_ambi: dict  # Uniform locations for the ambient shader
    uloc_diff: dict  # Uniform locations for the diffuse shader
    uloc_shdw: dict  # Uniform locations for the shadow shader
    uloc_shmp: dict  # Uniform locations for the shadow map shader
    uloc_dbsh: dict  # Uniform locations for redering the shadow map on a quad
    uloc_dbpi: dict  # Uniform locations for rendering picking texture on a quad
    uloc_pick: dict  # Uniform locations for the picking shader

    shader_line: int  # Shader program for the lines
    shader_ambi: int  # Shader program for ambient mesh rendering
    shader_diff: int  # Shader program for diffuse mesh rendering
    shader_shdw: int  # Shader program for rendering of diffuse mesh with shadow map
    shader_shmp: int  # Shader program for rendering of the shadow map to the frame buffer
    shader_dbsh: int  # Shader program for debug rendering of the shadow map to a quad
    shader_dbpi: int  # Shader program for debug rendering of picking texture to a quad
    shader_pick: int  # Shader program for picking

    quad_vertices: np.ndarray  # Vertices for the debug quad
    quad_indices: np.ndarray  # Indices for the debug quad

    # Scene based parameters
    diameter_xy: float  # Size of the model as diameter
    radius_xy: float  # Size of model as radius
    light_position: np.ndarray  # position of light that casts shadows [1 x 3]
    light_color: np.ndarray  # color of scene light [1 x 3]
    loop_counter: int  # loop counter for animation of scene light source

    FBO_shadows: int  # OpenGL Frame Buffer Objects
    depth_map: int  # Depth map identifier
    shadow_map_resolution: int  # Resolution of the shadow map, same in x and y.
    border_color: np.ndarray  # color for the border of the shadow map

    def __init__(self, mesh_wrapper: MeshWrapper):
        """Initialize the MeshGL object with vertex, face, and edge information."""

        self.name = mesh_wrapper.name
        self.vertices = mesh_wrapper.vertices
        self.faces = mesh_wrapper.faces
        self.edges = mesh_wrapper.edges

        self.dict_data = mesh_wrapper.dict_data
        self.guip = GuiParametersMesh(self.name, mesh_wrapper.shading, self.dict_data)

        self.uloc_line = {}
        self.uloc_ambi = {}
        self.uloc_diff = {}
        self.uloc_shdw = {}
        self.uloc_shmp = {}
        self.uloc_dbsh = {}
        self.uloc_pick = {}

        self.bb_local = mesh_wrapper.bb_local
        self.bb_global = mesh_wrapper.bb_global

        self._calc_model_scale()
        self._create_lines()
        self._create_triangels()
        self._create_debug_quad()
        self._create_shadow_map()
        self._create_shader_lines()
        self._create_shader_ambient()
        self._create_shader_diffuse()
        self._create_shader_shadows()
        self._create_shader_shadow_map()
        self._create_shader_picking()
        self._create_shader_debug_shadows()
        self._create_shader_debug_picking()
        self._set_constats()

        self.picked_id = -1

    def _calc_model_scale(self) -> None:
        """Calculate the model scale from vertex positions."""

        xdom = self.bb_local.xdom
        ydom = self.bb_local.ydom

        if self.bb_global is not None:
            xdom = self.bb_global.xdom
            ydom = self.bb_global.ydom

        self.diameter_xy = math.sqrt(xdom * xdom + ydom * ydom)
        self.radius_xy = self.diameter_xy / 2.0

    def _set_constats(self) -> None:
        """Set constant values like light position and color."""
        self.light_position = np.array([500.0, 500.0, 400.0], dtype=np.float32)
        self.light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.loop_counter = 120

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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(0))

        # Data for color calculations
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(12))

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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(0))

        # Data for color calculations
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(12))

        # Normals
        glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(24))

        # Id for clickability
        glEnableVertexAttribArray(3)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(36))

        glBindVertexArray(0)

    def _create_debug_quad(self) -> None:
        tex_min = 0
        tex_max = 1

        self.quad_vertices = [
            -1.0,
            -1.0,
            tex_min,
            tex_min,
            1.0,
            -1.0,
            tex_max,
            tex_min,
            -1.0,
            1.0,
            tex_min,
            tex_max,
            1.0,
            -1.0,
            tex_max,
            tex_min,
            -1.0,
            1.0,
            tex_min,
            tex_max,
            1.0,
            1.0,
            tex_max,
            tex_max,
        ]
        self.quad_indices = [
            0,
            1,
            2,
            3,
            4,
            5,
        ]

        self.quad_vertices = np.array(self.quad_vertices, dtype=np.float32)
        self.quad_indices = np.array(self.quad_indices, dtype=np.uint32)

        self.VAO_debug = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_debug)

        # Vertex buffer
        size = len(self.quad_vertices) * 4  # Size in bytes
        self.VBO_debug = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_debug)
        glBufferData(GL_ARRAY_BUFFER, size, self.quad_vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.quad_indices) * 4  # Size in bytes
        self.EBO_debug = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_debug)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.quad_indices, GL_STATIC_DRAW)

        # Position (x, y)
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))

        # Texture coordinates (x, y)
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))

    def _create_shadow_map(self) -> None:
        """Set up framebuffer and texture for shadow map rendering."""
        # Frambuffer for the shadow map
        self.FBO_shadows = glGenFramebuffers(1)

        # Creating a texture which will be used as the framebuffers depth buffer
        self.depth_map = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        self.shadow_map_resolution = 1024 * 8
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_DEPTH_COMPONENT,
            self.shadow_map_resolution,
            self.shadow_map_resolution,
            0,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
            None,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        self.border_color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, self.border_color)

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_shadows)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_map, 0
        )
        # Disable drawing to the color attachements since we only care about the depth
        glDrawBuffer(GL_NONE)

        # We don't want to read color attachements either
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def create_picking_fbo(self, interaction: Interaction) -> None:
        window_w = interaction.fbuf_width
        window_h = interaction.fbuf_height

        self.FBO_picking = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_picking)  # Bind our frame buffer

        self.pick_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.pick_texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, window_w, window_h, 0, GL_RGB, GL_FLOAT, None
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)  # Unbind our texture
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.pick_texture, 0
        )

        RBO = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, RBO)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, window_w, window_h)
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, RBO
        )

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
            print("Framebuffer for picking is complete")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Unbind our frame buffer

        pass

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
        self.uloc_line["clip_x"] = glGetUniformLocation(self.shader_line, "clip_x")
        self.uloc_line["clip_y"] = glGetUniformLocation(self.shader_line, "clip_y")
        self.uloc_line["clip_z"] = glGetUniformLocation(self.shader_line, "clip_z")
        self.uloc_line["cmap_idx"] = glGetUniformLocation(self.shader_line, "cmap_idx")
        self.uloc_line["data_idx"] = glGetUniformLocation(self.shader_line, "data_idx")
        self.uloc_line["data_min"] = glGetUniformLocation(self.shader_line, "data_min")
        self.uloc_line["data_max"] = glGetUniformLocation(self.shader_line, "data_max")

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
        self.uloc_ambi["clip_x"] = glGetUniformLocation(self.shader_ambi, "clip_x")
        self.uloc_ambi["clip_y"] = glGetUniformLocation(self.shader_ambi, "clip_y")
        self.uloc_ambi["clip_z"] = glGetUniformLocation(self.shader_ambi, "clip_z")
        self.uloc_ambi["cmap_idx"] = glGetUniformLocation(self.shader_ambi, "cmap_idx")
        self.uloc_ambi["data_idx"] = glGetUniformLocation(self.shader_ambi, "data_idx")
        self.uloc_ambi["data_min"] = glGetUniformLocation(self.shader_ambi, "data_min")
        self.uloc_ambi["data_max"] = glGetUniformLocation(self.shader_ambi, "data_max")
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
        self.uloc_diff["picked_id"] = glGetUniformLocation(
            self.shader_diff, "picked_id"
        )

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
        self.uloc_shdw["clip_x"] = glGetUniformLocation(self.shader_shdw, "clip_x")
        self.uloc_shdw["clip_y"] = glGetUniformLocation(self.shader_shdw, "clip_y")
        self.uloc_shdw["clip_z"] = glGetUniformLocation(self.shader_shdw, "clip_z")
        self.uloc_shdw["cmap_idx"] = glGetUniformLocation(self.shader_shdw, "cmap_idx")
        self.uloc_shdw["data_idx"] = glGetUniformLocation(self.shader_shdw, "data_idx")
        self.uloc_shdw["data_min"] = glGetUniformLocation(self.shader_shdw, "data_min")
        self.uloc_shdw["data_max"] = glGetUniformLocation(self.shader_shdw, "data_max")
        self.uloc_shdw["light_pos"] = glGetUniformLocation(
            self.shader_shdw, "light_pos"
        )
        self.uloc_shdw["view_pos"] = glGetUniformLocation(self.shader_shdw, "view_pos")
        self.uloc_shdw["light_color"] = glGetUniformLocation(
            self.shader_shdw, "light_color"
        )
        self.uloc_shdw["lsm"] = glGetUniformLocation(
            self.shader_shdw, "light_space_matrix"
        )
        self.uloc_shdw["picked_id"] = glGetUniformLocation(
            self.shader_shdw, "picked_id"
        )

    def _create_shader_shadow_map(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader_shmp = compileProgram(
            compileShader(vertex_shader_shadow_map, GL_VERTEX_SHADER),
            compileShader(fragment_shader_shadow_map, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shmp)

        self.uloc_shmp["model"] = glGetUniformLocation(self.shader_shmp, "model")
        self.uloc_shmp["lsm"] = glGetUniformLocation(
            self.shader_shmp, "light_space_matrix"
        )

    def _create_shader_debug_shadows(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader_dbsh = compileProgram(
            compileShader(vertex_shader_debug_shadows, GL_VERTEX_SHADER),
            compileShader(fragment_shader_debug_shadows, GL_FRAGMENT_SHADER),
        )

    def _create_shader_picking(self) -> None:
        """Create shader for picking."""

        self.shader_pick = compileProgram(
            compileShader(vertex_shader_picking, GL_VERTEX_SHADER),
            compileShader(fragment_shader_picking, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_pick)

        self.uloc_pick["model"] = glGetUniformLocation(self.shader_pick, "model")
        self.uloc_pick["project"] = glGetUniformLocation(self.shader_pick, "project")
        self.uloc_pick["view"] = glGetUniformLocation(self.shader_pick, "view")

    def _create_shader_debug_picking(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader_dbpi = compileProgram(
            compileShader(vertex_shader_debug_picking, GL_VERTEX_SHADER),
            compileShader(fragment_shader_debug_picking, GL_FRAGMENT_SHADER),
        )

    def _update_color_caps(self):
        if self.guip.update_caps:
            self.guip.calc_data_min_max()
            self.guip.update_caps = False

    def render_lines(self, interaction: Interaction, gguip: GuiParameters, ws_pass=0):
        """Render wireframe lines of the mesh.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._update_color_caps()
        self._bind_shader_lines()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_line["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_line["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_line["project"], 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip, ws_pass)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_line["color_by"], color_by)
        glUniform1i(self.uloc_line["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_line["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_line["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_line["data_max"], self.guip.data_max)

        self._lines_draw_call()
        self._unbind_shader()

    def render_ambient(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render the mesh with ambient shading.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._update_color_caps()
        self._bind_shader_ambient()

        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()

        glUniformMatrix4fv(self.uloc_ambi["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_ambi["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_ambi["project"], 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_ambi["color_by"], color_by)
        glUniform1i(self.uloc_ambi["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_ambi["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_ambi["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_ambi["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_ambi["picked_id"], self.picked_id)

        self._triangles_draw_call()
        self._unbind_shader()

    def render_diffuse(self, interaction: Interaction, gguip: GuiParameters, ws_pass=0):
        """Render the mesh with diffuse shading.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._update_color_caps()
        self._bind_shader_diffuse()
        self.light_position = self._calc_light_position()

        # MVP calcs
        move = interaction.camera.get_move_matrix()
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_diff["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_diff["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_diff["project"], 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip, ws_pass)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_diff["color_by"], color_by)
        glUniform1i(self.uloc_diff["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_diff["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_diff["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_diff["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_diff["picked_id"], self.picked_id)

        view_pos = interaction.camera.camera_pos
        glUniform3fv(self.uloc_diff["view_pos"], 1, view_pos)

        # Set light uniforms
        glUniform3fv(self.uloc_diff["light_color"], 1, self.light_color)
        glUniform3fv(self.uloc_diff["light_pos"], 1, self.light_position)

        self._triangles_draw_call()
        self._unbind_shader()

    def render_shadows(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Generates a shadow map and renders the mesh with shadows by sampling that
        shadow map.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._update_color_caps()
        self._render_shadow_map(interaction)

        if interaction.show_shadow_texture:
            self._render_debug_shadows(interaction)
        else:
            self._render_shadows(interaction, gguip)

    def render_wireshaded(self, interaction: Interaction, gguip: GuiParameters) -> None:
        self._update_color_caps()
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.0, 1.0)
        self.render_diffuse(interaction, gguip, ws_pass=1)
        glDisable(GL_POLYGON_OFFSET_FILL)

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        self.render_lines(interaction, gguip, ws_pass=2)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def evaluate_picking(self, interaction: Interaction) -> None:
        self._draw_picking_texture(interaction)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        x = interaction.picked_x
        y = interaction.picked_y

        # print(x, y, interaction.width, interaction.height)

        data = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        picked_id_new = color_to_id(data)

        if picked_id_new == self.picked_id:
            self.picked_id = -1
        else:
            self.picked_id = picked_id_new
            # print(self.picked_id)

        interaction.picking = False

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _draw_picking_texture(self, keyaction: Interaction) -> None:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Camera input
        move = keyaction.camera.get_move_matrix()
        view = keyaction.camera.get_view_matrix()
        proj = keyaction.camera.get_perspective_matrix()

        # Picking pass
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_picking)
        glEnable(GL_DEPTH_TEST)
        # glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_pick)

        glUniformMatrix4fv(self.uloc_pick["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_pick["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_pick["project"], 1, GL_FALSE, proj)

        # Render to the picking texture
        self._triangles_draw_call()

    def render_pick_texture(self, keyaction: Interaction, gguip: GuiParameters) -> None:
        self._draw_picking_texture(keyaction)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Apply the picking texture to the debug quad which spans th whole screen.
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.shader_dbpi)  # Use the debug picking shader
        glBindVertexArray(self.VAO_debug)
        glBindTexture(GL_TEXTURE_2D, self.pick_texture)

        # Draw the quad
        self._debug_quad_draw_call()
        glEnable(GL_DEPTH_TEST)

    def _render_shadow_map(self, interaction: Interaction) -> None:
        """Render a shadow map to the frame buffer.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        # first pass: Capture shadow map
        rad = self.radius_xy

        self.light_position = self._calc_light_position()

        far = 1.25 * self.diameter_xy
        light_projection = pyrr.matrix44.create_orthogonal_projection(
            -rad, rad, -rad, rad, 0.1, far, dtype=np.float32
        )
        look_target = np.array([0, 0, 0], dtype=np.float32)
        global_up = np.array([0, 0, 1], dtype=np.float32)
        light_view = pyrr.matrix44.create_look_at(
            self.light_position, look_target, global_up, dtype=np.float32
        )
        self.light_space_matrix = pyrr.matrix44.multiply(light_view, light_projection)
        glUseProgram(self.shader_shmp)
        glUniformMatrix4fv(self.uloc_shmp["lsm"], 1, GL_FALSE, self.light_space_matrix)
        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.uloc_shmp["model"], 1, GL_FALSE, translation)

        glViewport(0, 0, self.shadow_map_resolution, self.shadow_map_resolution)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_shadows)

        # Only clearing depth buffer since there is no color attachement
        glClear(GL_DEPTH_BUFFER_BIT)

        self._triangles_draw_call()

    def _render_debug_shadows(self, interaction: Interaction) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, interaction.fbuf_width, interaction.fbuf_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_dbsh)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        self._debug_quad_draw_call()

    def _render_shadows(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render the model with shadows by sampling the shadow map frame buffer.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        # Second pass: Render objects with the shadow map computed in the first pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Setting default buffer
        glViewport(0, 0, interaction.fbuf_width, interaction.fbuf_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_shdw)

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_shdw["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_shdw["project"], 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.uloc_shdw["view"], 1, GL_FALSE, view)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_shdw["color_by"], color_by)
        glUniform1i(self.uloc_shdw["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uloc_shdw["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_shdw["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_shdw["data_max"], self.guip.data_max)
        glUniform1i(self.uloc_shdw["picked_id"], self.picked_id)

        # Set light uniforms
        glUniform3fv(self.uloc_shdw["light_color"], 1, self.light_color)
        glUniform3fv(self.uloc_shdw["view_pos"], 1, interaction.camera.camera_pos)
        glUniform3fv(self.uloc_shdw["light_pos"], 1, self.light_position)

        # Set light space matrix
        glUniformMatrix4fv(self.uloc_shdw["lsm"], 1, GL_FALSE, self.light_space_matrix)

        # Bind the shadow map texture so that it can be sampled in the shader
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)

        self._triangles_draw_call()
        self._unbind_shader()

    def _debug_quad_draw_call(self) -> None:
        glBindVertexArray(self.VAO_debug)
        glDrawElements(GL_TRIANGLES, len(self.quad_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    def _triangles_draw_call(self):
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
        """Bind the shader for basic shading."""
        glUseProgram(self.shader_ambi)

    def _bind_shader_diffuse(self) -> None:
        """Bind the shader for diffuse shading."""
        glUseProgram(self.shader_diff)

    def _bind_shader_shadows(self) -> None:
        """Bind the shader for shading with shadows."""
        glUseProgram(self.shader_shdw)

    def _bind_shader_shadow_map(self) -> None:
        """Bind the shader for rendering shadow map."""
        glUseProgram(self.shader_shmp)

    def _unbind_shader(self) -> None:
        """Unbind the currently bound shader."""
        glUseProgram(0)

    def _calc_light_position(self) -> np.ndarray:
        """Calculate position animated position of light source which casts shadows."""
        if self.guip.animate_light:
            self.loop_counter += 1

        rot_step = self.loop_counter / 120.0
        x = math.sin(rot_step) * self.radius_xy
        y = math.cos(rot_step) * self.radius_xy
        z = abs(math.sin(rot_step / 2.0)) * 0.7 * self.radius_xy
        light_position = np.array([x, y, z], dtype=np.float32)

        return light_position

    def mvpc(self, mloc, vloc, ploc, cloc, color_by: int, interaction: Interaction):
        """Set move, view, project, color uniforms"""

        move = interaction.camera.get_move_matrix()
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(mloc, 1, GL_FALSE, move)
        glUniformMatrix4fv(vloc, 1, GL_FALSE, view)
        glUniformMatrix4fv(ploc, 1, GL_FALSE, proj)

        glUniform1i(cloc, color_by)

        pass

    def set_clipping_uniforms(self, gguip: GuiParameters, ws_pass: int = 0):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        if self.guip.mesh_shading == MeshShading.wireframe or ws_pass == 2:
            glUniform1f(self.uloc_line["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_line["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_line["clip_z"], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.ambient:
            glUniform1f(self.uloc_ambi["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_ambi["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_ambi["clip_z"], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.diffuse or ws_pass == 1:
            glUniform1f(self.uloc_diff["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_diff["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_diff["clip_z"], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.shadows:
            glUniform1f(self.uloc_shdw["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_shdw["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_shdw["clip_z"], (zdom * gguip.clip_dist[2]))
