import math
import glfw
import copy
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
from dtcc_viewer.opengl_viewer.utils import fit_colors_to_faces
from dtcc_viewer.logging import info, warning
from dtcc_viewer.colors import calc_colors_rainbow
from dtcc_viewer.colors import color_maps

from dtcc_viewer.opengl_viewer.shaders_mesh_shadows import (
    vertex_shader_shadows,
    fragment_shader_shadows,
)
from dtcc_viewer.opengl_viewer.shaders_mesh_shadows import (
    vertex_shader_shadow_map,
    fragment_shader_shadow_map,
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

    guip: GuiParametersMesh  # Information used by the Gui
    vertices: np.ndarray  # [n_vertices x 9] each row has (x, y, z, r, g, b, nx, ny, nz)
    faces: np.ndarray  # [n_faces x 3] each row has three vertex indices
    edges: np.ndarray  # [n_edges x 2] each row has

    bb: np.ndarray  # Bounding box [xmin, xmax, ymin, ymax, zmin, zmax]
    bb_local: BoundingBox
    bb_global: BoundingBox

    uloc_lin: dict  # Uniform locations for the lines shader
    shader_lin: int  # Shader program for the lines

    uloc_amb: dict  # Uniform locations for the ambient shader
    shader_amb: int  # Shader program for ambient mesh rendering

    uloc_dif: dict  # Uniform locations for the diffuse shader
    shader_dif: int  # Shader program for diffuse mesh rendering

    uloc_sha: dict  # Uniform locations for the shadow shader
    shader_sha: int  # Shader program for rendering of diffuse mesh with shadow map

    shader_shm: int  # Shader program for rendering of the shadow map to the frame buffer
    uloc_shm: dict  # Uniform locations for the shadow map shader

    mloc_shadow_map: int  # Uniform location for model matrix for shadow map rendering
    lsm_loc_shadow_map: int  # Uniform location for light space matrix for shadow map rendering

    # Scene based parameters
    diameter_xy: float  # Size of the model as diameter
    radius_xy: float  # Size of model as radius
    light_position: np.ndarray  # position of light that casts shadows [1 x 3]
    light_color: np.ndarray  # color of scene light [1 x 3]
    loop_counter: int  # loop counter for animation of scene light source

    FBO: int  # OpenGL Frame Buffer Objects
    depth_map: int  # Depth map identifier
    shadow_map_resolution: int  # Resolution of the shadow map, same in x and y.
    border_color: np.ndarray  # color for the border of the shadow map

    def __init__(self, mesh_wrapper: MeshWrapper):
        """Initialize the MeshGL object with vertex, face, and edge information.

        Parameters
        ----------
        mesh_data : MeshData
            Instance of the MeshData class with vertices, edge indices, face indices.
        """
        self.name = mesh_wrapper.name
        self.vertices = mesh_wrapper.vertices
        self.faces = mesh_wrapper.faces
        self.edges = mesh_wrapper.edges

        self.dict_data = mesh_wrapper.dict_data
        self.guip = GuiParametersMesh(self.name, mesh_wrapper.shading, self.dict_data)

        self.uloc_lin = {}
        self.uloc_amb = {}
        self.uloc_dif = {}
        self.uloc_sha = {}
        self.uloc_shm = {}

        self.cp_locs_lines = [0, 0, 0]
        self.cp_locs_ambient = [0, 0, 0]
        self.cp_locs_diffuse = [0, 0, 0]
        self.cp_locs_shadows = [0, 0, 0]

        self.bb_local = mesh_wrapper.bb_local
        self.bb_global = mesh_wrapper.bb_global

        self._calc_model_scale()
        self._create_lines()
        self._create_triangels()
        self._create_shadow_map()
        self._create_shader_lines()
        self._create_shader_ambient()
        self._create_shader_diffuse()
        self._create_shader_shadows()
        self._create_shader_shadow_map()
        self._set_constats()

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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Data for color calculations
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

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

        # Data for color calculations
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        # Normals
        glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))

        glBindVertexArray(0)

    def _create_shadow_map(self) -> None:
        """Set up framebuffer and texture for shadow map rendering."""
        # Frambuffer for the shadow map
        self.FBO = glGenFramebuffers(1)

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

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_map, 0
        )
        glDrawBuffer(
            GL_NONE
        )  # Disable drawing to the color attachements since we only care about the depth
        glReadBuffer(GL_NONE)  # We don't want to read color attachements either
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

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
        self.shader_lin = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader_lin)

        self.uloc_lin["model"] = glGetUniformLocation(self.shader_lin, "model")
        self.uloc_lin["view"] = glGetUniformLocation(self.shader_lin, "view")
        self.uloc_lin["project"] = glGetUniformLocation(self.shader_lin, "project")
        self.uloc_lin["color_by"] = glGetUniformLocation(self.shader_lin, "color_by")
        self.uloc_lin["clip_x"] = glGetUniformLocation(self.shader_lin, "clip_x")
        self.uloc_lin["clip_y"] = glGetUniformLocation(self.shader_lin, "clip_y")
        self.uloc_lin["clip_z"] = glGetUniformLocation(self.shader_lin, "clip_z")
        self.uloc_lin["color_map"] = glGetUniformLocation(self.shader_lin, "color_map")
        self.uloc_lin["data_idx"] = glGetUniformLocation(self.shader_lin, "data_idx")
        self.uloc_lin["data_min"] = glGetUniformLocation(self.shader_lin, "data_min")
        self.uloc_lin["data_max"] = glGetUniformLocation(self.shader_lin, "data_max")

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
        self.shader_amb = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_amb)

        self.uloc_amb["model"] = glGetUniformLocation(self.shader_amb, "model")
        self.uloc_amb["view"] = glGetUniformLocation(self.shader_amb, "view")
        self.uloc_amb["project"] = glGetUniformLocation(self.shader_amb, "project")
        self.uloc_amb["color_by"] = glGetUniformLocation(self.shader_amb, "color_by")
        self.uloc_amb["clip_x"] = glGetUniformLocation(self.shader_amb, "clip_x")
        self.uloc_amb["clip_y"] = glGetUniformLocation(self.shader_amb, "clip_y")
        self.uloc_amb["clip_z"] = glGetUniformLocation(self.shader_amb, "clip_z")
        self.uloc_amb["color_map"] = glGetUniformLocation(self.shader_amb, "color_map")
        self.uloc_amb["data_idx"] = glGetUniformLocation(self.shader_amb, "data_idx")
        self.uloc_amb["data_min"] = glGetUniformLocation(self.shader_amb, "data_min")
        self.uloc_amb["data_max"] = glGetUniformLocation(self.shader_amb, "data_max")

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
        self.shader_dif = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_dif)

        self.uloc_dif["model"] = glGetUniformLocation(self.shader_dif, "model")
        self.uloc_dif["view"] = glGetUniformLocation(self.shader_dif, "view")
        self.uloc_dif["project"] = glGetUniformLocation(self.shader_dif, "project")
        self.uloc_dif["color_by"] = glGetUniformLocation(self.shader_dif, "color_by")
        self.uloc_dif["light_color"] = glGetUniformLocation(
            self.shader_dif, "light_color"
        )
        self.uloc_dif["light_pos"] = glGetUniformLocation(self.shader_dif, "light_pos")
        self.uloc_dif["view_pos"] = glGetUniformLocation(self.shader_dif, "view_pos")

        self.uloc_dif["clip_x"] = glGetUniformLocation(self.shader_dif, "clip_x")
        self.uloc_dif["clip_y"] = glGetUniformLocation(self.shader_dif, "clip_y")
        self.uloc_dif["clip_z"] = glGetUniformLocation(self.shader_dif, "clip_z")
        self.uloc_dif["color_map"] = glGetUniformLocation(self.shader_dif, "color_map")
        self.uloc_dif["data_idx"] = glGetUniformLocation(self.shader_dif, "data_idx")
        self.uloc_dif["data_min"] = glGetUniformLocation(self.shader_dif, "data_min")
        self.uloc_dif["data_max"] = glGetUniformLocation(self.shader_dif, "data_max")

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
        self.shader_sha = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_sha)

        self.uloc_sha["model"] = glGetUniformLocation(self.shader_sha, "model")
        self.uloc_sha["view"] = glGetUniformLocation(self.shader_sha, "view")
        self.uloc_sha["project"] = glGetUniformLocation(self.shader_sha, "project")
        self.uloc_sha["color_by"] = glGetUniformLocation(self.shader_sha, "color_by")
        self.uloc_sha["clip_x"] = glGetUniformLocation(self.shader_sha, "clip_x")
        self.uloc_sha["clip_y"] = glGetUniformLocation(self.shader_sha, "clip_y")
        self.uloc_sha["clip_z"] = glGetUniformLocation(self.shader_sha, "clip_z")
        self.uloc_sha["color_map"] = glGetUniformLocation(self.shader_sha, "color_map")
        self.uloc_sha["data_idx"] = glGetUniformLocation(self.shader_sha, "data_idx")
        self.uloc_sha["data_min"] = glGetUniformLocation(self.shader_sha, "data_min")
        self.uloc_sha["data_max"] = glGetUniformLocation(self.shader_sha, "data_max")
        self.uloc_sha["light_pos"] = glGetUniformLocation(self.shader_sha, "light_pos")
        self.uloc_sha["view_pos"] = glGetUniformLocation(self.shader_sha, "view_pos")
        self.uloc_sha["light_color"] = glGetUniformLocation(
            self.shader_sha, "light_color"
        )
        self.uloc_sha["lsm"] = glGetUniformLocation(
            self.shader_sha, "light_space_matrix"
        )

    def _create_shader_shadow_map(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader_shm = compileProgram(
            compileShader(vertex_shader_shadow_map, GL_VERTEX_SHADER),
            compileShader(fragment_shader_shadow_map, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shm)

        self.uloc_shm["model"] = glGetUniformLocation(self.shader_shm, "model")
        self.uloc_shm["lsm"] = glGetUniformLocation(
            self.shader_shm, "light_space_matrix"
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
        glUniformMatrix4fv(self.uloc_lin["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_lin["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_lin["project"], 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip, ws_pass)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_lin["color_by"], color_by)
        glUniform1i(self.uloc_lin["color_map"], self.guip.cmap_idx)
        glUniform1i(self.uloc_lin["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_lin["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_lin["data_max"], self.guip.data_max)

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

        glUniformMatrix4fv(self.uloc_amb["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_amb["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_amb["project"], 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_amb["color_by"], color_by)
        glUniform1i(self.uloc_amb["color_map"], self.guip.cmap_idx)
        glUniform1i(self.uloc_amb["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_amb["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_amb["data_max"], self.guip.data_max)

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
        glUniformMatrix4fv(self.uloc_dif["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_dif["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_dif["project"], 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip, ws_pass)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_dif["color_by"], color_by)
        glUniform1i(self.uloc_dif["color_map"], self.guip.cmap_idx)
        glUniform1i(self.uloc_dif["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_dif["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_dif["data_max"], self.guip.data_max)

        view_pos = interaction.camera.camera_pos
        glUniform3fv(self.uloc_dif["view_pos"], 1, view_pos)

        # Set light uniforms
        glUniform3fv(self.uloc_dif["light_color"], 1, self.light_color)
        glUniform3fv(self.uloc_dif["light_pos"], 1, self.light_position)

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
        glUseProgram(self.shader_shm)
        glUniformMatrix4fv(self.uloc_shm["lsm"], 1, GL_FALSE, self.light_space_matrix)
        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.uloc_shm["model"], 1, GL_FALSE, translation)

        glViewport(0, 0, self.shadow_map_resolution, self.shadow_map_resolution)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)

        # Only clearing depth buffer since there is no color attachement
        glClear(GL_DEPTH_BUFFER_BIT)

        self._triangles_draw_call()

    def _render_shadows(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render the model with shadows by sampling the shadow map frame buffer.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        # Second pass: Render objects with the shadow map computed in the first pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Setting default buffer
        glViewport(0, 0, interaction.width, interaction.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_sha)

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uloc_sha["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_sha["project"], 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.uloc_sha["view"], 1, GL_FALSE, view)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.uloc_sha["color_by"], color_by)
        glUniform1i(self.uloc_sha["color_map"], self.guip.cmap_idx)
        glUniform1i(self.uloc_sha["data_idx"], self.guip.data_idx)
        glUniform1f(self.uloc_sha["data_min"], self.guip.data_min)
        glUniform1f(self.uloc_sha["data_max"], self.guip.data_max)

        # Set light uniforms
        glUniform3fv(self.uloc_sha["light_color"], 1, self.light_color)
        glUniform3fv(self.uloc_sha["view_pos"], 1, interaction.camera.camera_pos)
        glUniform3fv(self.uloc_sha["light_pos"], 1, self.light_position)

        # Set light space matrix
        glUniformMatrix4fv(self.uloc_sha["lsm"], 1, GL_FALSE, self.light_space_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)

        self._triangles_draw_call()
        self._unbind_shader()

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
        glUseProgram(self.shader_lin)

    def _bind_shader_ambient(self) -> None:
        """Bind the shader for basic shading."""
        glUseProgram(self.shader_amb)

    def _bind_shader_diffuse(self) -> None:
        """Bind the shader for diffuse shading."""
        glUseProgram(self.shader_dif)

    def _bind_shader_shadows(self) -> None:
        """Bind the shader for shading with shadows."""
        glUseProgram(self.shader_sha)

    def _bind_shader_shadow_map(self) -> None:
        """Bind the shader for rendering shadow map."""
        glUseProgram(self.shader_shm)

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
            glUniform1f(self.uloc_lin["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_lin["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_lin["clip_z"], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.ambient:
            glUniform1f(self.uloc_amb["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_amb["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_amb["clip_z"], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.diffuse or ws_pass == 1:
            glUniform1f(self.uloc_dif["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_dif["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_dif["clip_z"], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.shadows:
            glUniform1f(self.uloc_sha["clip_x"], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.uloc_sha["clip_y"], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.uloc_sha["clip_z"], (zdom * gguip.clip_dist[2]))
