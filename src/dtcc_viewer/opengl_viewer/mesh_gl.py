import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.gui import GuiParameters, GuiParametersMesh
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.utils import MeshShading, BoundingBox

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


class MeshGL:
    """Represents a 3D mesh in OpenGL and provides methods for rendering.

    This class handles the rendering of mesh data using OpenGL. It provides methods to
    set up the rendering environment, binding and rendering with a range of different
    shaders, and perform the necessary transformations camera interaction, perspective
    projection and other features needed for visualization.

    Attributes
    ----------
    VAO_triangels : int
        OpenGL Vertex attribut object for triangles.
    VBO_triangels : int
        OpenGL Vertex buffer object for triangles.
    EBO_triangels : int
        OpenGL Element buffer object for triangles.
    VAO_edge : int
        OpenGL Vertex attribut object for wireframe edges.
    VBO_edge : int
        OpenGL Vertex buffer object for wireframe edges.
    EBO_edge : int
        OpenGL Element buffer object for wireframe edges.
    guip : GuiParametersMesh
        Information used by the GUI.
    vertices : np.ndarray
        Array containing vertex information (x, y, z, r, g, b, nx, ny, nz).
    face_indices : np.ndarray
        Array containing face indices.
    edge_indices : np.ndarray
        Array containing edge indices.
    shader_lines : int
        Shader program for the lines.
    mloc_lines : int
        Uniform location for model matrix for lines.
    vloc_lines : int
        Uniform location for view matrix for lines.
    ploc_lines : int
        Uniform location for projection matrix for lines.
    cb_loc_lines : int
        Uniform location for color_by variable for lines.
    shader_ambient : int
        Shader program for ambient mesh rendering.
    mloc_ambient : int
        Uniform location for model matrix for ambient rendering.
    ploc_ambient : int
        Uniform location for projection matrix for ambient rendering.
    vloc_ambient : int
        Uniform location for view matrix for ambient rendering.
    cb_loc_ambient : int
        Uniform location for color_by variable for ambient rendering.
    shader_diffuse : int
        Shader program for diffuse mesh rendering.
    mloc_diffuse : int
        Uniform location for model matrix for diffuse rendering.
    ploc_diffuse : int
        Uniform location for projection matrix for diffuse rendering.
    vloc_diffuse : int
        Uniform location for view matrix for diffuse rendering.
    cb_loc_diffuse : int
        Uniform location for color_by variable for diffuse rendering.
    lc_loc_diffuse : int
        Uniform location for light color for diffuse rendering.
    lp_loc_diffuse : int
        Uniform location for light position for diffuse rendering.
    vp_loc_diffuse : int
        Uniform location for view position for diffuse rendering.
    shader_shadows : int
        Shader program for rendering of diffuse mesh with shadow map.
    mloc_shadows : int
        Uniform location for model matrix for diffuse shadow rendering.
    ploc_shadows : int
        Uniform location for projection matrix for diffuse shadow rendering.
    vloc_shadows : int
        Uniform location for view matrix for diffuse shadow rendering.
    cb_loc_shadows : int
        Uniform location for color_by variable for diffuse shadow rendering.
    lc_loc_shadows : int
        Uniform location for light color for diffuse shadow rendering.
    lp_loc_shadows : int
        Uniform location for light position for diffuse shadow rendering.
    vp_loc_shadows : int
        Uniform location for view position for diffuse shadow rendering.
    lsm_loc_shadows : int
        Uniform location for light space matrix for diffuse shadow rendering.
    shader_shadow_map : int
        Shader program for rendering of the shadow map to the frame buffer.
    mloc_shadow_map : int
        Uniform location for model matrix for shadow map rendering.
    lsm_loc_shadow_map : int
        Uniform location for light space matrix for shadow map rendering.
    diameter_xy : float
        Size of the model as diameter.
    radius_xy : float
        Size of model as radius.
    light_position : np.ndarray
        Position of light that casts shadows [1 x 3].
    light_color : np.ndarray
        Color of scene light [1 x 3].
    loop_counter : int
        Loop counter for animation of scene light source.
    FBO : int
        OpenGL Frame Buffer Objects.
    depth_map : int
        Depth map identifier.
    shadow_map_resolution : int
        Resolution of the shadow map, same in x and y.
    border_color : np.ndarray
        Color for the border of the shadow map.
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
    face_indices: np.ndarray  # [n_faces x 3] each row has three vertex indices
    edge_indices: np.ndarray  # [n_edges x 2] each row has

    bb: np.ndarray  # Bounding box [xmin, xmax, ymin, ymax, zmin, zmax]
    bb_local: BoundingBox
    bb_global: BoundingBox

    shader_lines: int  # Shader program for the lines
    mloc_lines: int  # Uniform location for model matrix for lines
    vloc_lines: int  # Uniform location for view matrix for lines
    ploc_lines: int  # Uniform location for projection matrix for lines
    cb_loc_lines: int  # Uniform location for color_by variable for lines
    cp_locs_lines: [int]  # Uniform locations for clip plane distance x,y,z

    shader_ambient: int  # Shader program for ambient mesh rendering
    mloc_ambient: int  # Uniform location for model matrix for ambient rendering
    ploc_ambient: int  # Uniform location for projection matrix for ambient rendering
    vloc_ambient: int  # Uniform location for view matrix for ambient rendering
    cb_loc_ambient: int  # Uniform location for color_by variable for ambient rendering
    cp_locs_ambient: [int]  # Uniform locations for clip plane distance x,y,z

    shader_diffuse: int  # Shader program for diffuse mesh renderi
    mloc_diffuse: int  # Uniform location for model matrix for diffuse rendering
    ploc_diffuse: int  # Uniform location for projection matrix for diffuse rendering
    vloc_diffuse: int  # Uniform location for view matrix for diffuse rendering
    cb_loc_diffuse: int  # Uniform location for color_by variable for diffuse rendering
    lc_loc_diffuse: int  # Uniform location for light color for diffuse rendering
    lp_loc_diffuse: int  # Uniform location for light position for diffuse rendering
    vp_loc_diffuse: int  # Uniform location for view position for diffuse rendering
    cp_locs_diffuse: [int]  # Uniform locations for clip plane distance x,y,z

    shader_shadows: int  # Shader program for rendering of diffuse mesh with shadow map
    mloc_shadows: int  # Uniform location for model matrix for diffuse shadow rendering
    ploc_shadows: int  # Uniform location for projection matrix for diffuse shadow rendering
    vloc_shadows: int  # Uniform location for view matrix for diffuse shadow rendering
    cb_loc_shadows: int  # Uniform location for color_by variable for diffuse shadow rendering
    lc_loc_shadows: int  # Uniform location for light color for diffuse shadow rendering
    lp_loc_shadows: int  # Uniform location for light position for diffuse shadow rendering
    vp_loc_shadows: int  # Uniform location for view position for diffuse shadow rendering
    lsm_loc_shadows: int  # Uniform location for light space matrix for diffuse shadow rendering
    cp_locs_shadows: [int]  # Uniform locations for clip plane distance x,y,z

    shader_shadow_map: int  # Shader program for rendering of the shadow map to the frame buffer
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

    def __init__(self, mesh_data: MeshData):
        """Initialize the MeshGL object with vertex, face, and edge information.

        Parameters
        ----------
        mesh_data : MeshData
            Instance of the MeshData class with vertices, edge indices, face indices.
        """

        self.guip = GuiParametersMesh(mesh_data.name)

        self.vertices = mesh_data.vertices
        self.face_indices = mesh_data.face_indices
        self.edge_indices = mesh_data.edge_indices

        self.cp_locs_lines = [0, 0, 0]
        self.cp_locs_ambient = [0, 0, 0]
        self.cp_locs_diffuse = [0, 0, 0]
        self.cp_locs_shadows = [0, 0, 0]

        self.bb_local = mesh_data.bb_local
        self.bb_global = mesh_data.bb_global

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
        size = len(self.edge_indices) * 4
        self.EBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_edge)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.edge_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Color
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
        size = len(self.face_indices) * 4  # Size in bytes
        self.EBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_triangels)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.face_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Color
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
        glGenTextures(1, self.FBO)

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
        self._bind_vao_lines()
        self.shader_lines = compileProgram(
            compileShader(vertex_shader_lines, GL_VERTEX_SHADER),
            compileShader(fragment_shader_lines, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader_lines)

        self.mloc_lines = glGetUniformLocation(self.shader_lines, "model")
        self.vloc_lines = glGetUniformLocation(self.shader_lines, "view")
        self.ploc_lines = glGetUniformLocation(self.shader_lines, "project")
        self.cb_loc_lines = glGetUniformLocation(self.shader_lines, "color_by")

        self.cp_locs_lines[0] = glGetUniformLocation(self.shader_lines, "clip_x")
        self.cp_locs_lines[1] = glGetUniformLocation(self.shader_lines, "clip_y")
        self.cp_locs_lines[2] = glGetUniformLocation(self.shader_lines, "clip_z")

    def _create_shader_ambient(self) -> None:
        """Create shader for ambient shading."""
        self._bind_vao_triangels()
        self.shader_ambient = compileProgram(
            compileShader(vertex_shader_ambient, GL_VERTEX_SHADER),
            compileShader(fragment_shader_ambient, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_ambient)

        self.mloc_ambient = glGetUniformLocation(self.shader_ambient, "model")
        self.vloc_ambient = glGetUniformLocation(self.shader_ambient, "view")
        self.ploc_ambient = glGetUniformLocation(self.shader_ambient, "project")
        self.cb_loc_ambient = glGetUniformLocation(self.shader_ambient, "color_by")
        self.cp_locs_ambient[0] = glGetUniformLocation(self.shader_ambient, "clip_x")
        self.cp_locs_ambient[1] = glGetUniformLocation(self.shader_ambient, "clip_y")
        self.cp_locs_ambient[2] = glGetUniformLocation(self.shader_ambient, "clip_z")

    def _create_shader_diffuse(self) -> None:
        """Create shader for diffuse shading."""
        self._bind_vao_triangels()
        self.shader_diffuse = compileProgram(
            compileShader(vertex_shader_diffuse, GL_VERTEX_SHADER),
            compileShader(fragment_shader_diffuse, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_diffuse)

        self.mloc_diffuse = glGetUniformLocation(self.shader_diffuse, "model")
        self.vloc_diffuse = glGetUniformLocation(self.shader_diffuse, "view")
        self.ploc_diffuse = glGetUniformLocation(self.shader_diffuse, "project")
        self.cb_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "color_by")

        self.lc_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "light_color")
        self.lp_loc_diffuse = glGetUniformLocation(
            self.shader_diffuse, "light_position"
        )
        self.vp_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "view_position")

        self.cp_locs_diffuse[0] = glGetUniformLocation(self.shader_diffuse, "clip_x")
        self.cp_locs_diffuse[1] = glGetUniformLocation(self.shader_diffuse, "clip_y")
        self.cp_locs_diffuse[2] = glGetUniformLocation(self.shader_diffuse, "clip_z")

    def _create_shader_shadows(self) -> None:
        """Create shader for shading with shadows."""
        self._bind_vao_triangels()
        self.shader_shadows = compileProgram(
            compileShader(vertex_shader_shadows, GL_VERTEX_SHADER),
            compileShader(fragment_shader_shadows, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shadows)

        self.mloc_shadows = glGetUniformLocation(self.shader_shadows, "model")
        self.vloc_shadows = glGetUniformLocation(self.shader_shadows, "view")
        self.ploc_shadows = glGetUniformLocation(self.shader_shadows, "project")
        self.cb_loc_shadows = glGetUniformLocation(self.shader_shadows, "color_by")
        self.lc_loc_shadows = glGetUniformLocation(self.shader_shadows, "light_color")
        self.lp_loc_shadows = glGetUniformLocation(
            self.shader_shadows, "light_position"
        )
        self.vp_loc_shadows = glGetUniformLocation(self.shader_shadows, "view_position")
        self.lsm_loc_shadows = glGetUniformLocation(
            self.shader_shadows, "light_space_matrix"
        )

        self.cp_locs_shadows[0] = glGetUniformLocation(self.shader_shadows, "clip_x")
        self.cp_locs_shadows[1] = glGetUniformLocation(self.shader_shadows, "clip_y")
        self.cp_locs_shadows[2] = glGetUniformLocation(self.shader_shadows, "clip_z")

    def _create_shader_shadow_map(self) -> None:
        """Create shader for rendering shadow map."""
        self.shader_shadow_map = compileProgram(
            compileShader(vertex_shader_shadow_map, GL_VERTEX_SHADER),
            compileShader(fragment_shader_shadow_map, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shadow_map)

        self.mloc_shadow_map = glGetUniformLocation(self.shader_shadow_map, "model")
        self.lsm_loc_shadow_map = glGetUniformLocation(
            self.shader_shadow_map, "light_space_matrix"
        )

    def render_lines(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render wireframe lines of the mesh.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """

        self._bind_shader_lines()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.mloc_lines, 1, GL_FALSE, move)
        glUniformMatrix4fv(self.vloc_lines, 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ploc_lines, 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_lines, color_by)

        self._lines_draw_call()
        self._unbind_shader()

    def render_ambient(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render the mesh with ambient shading.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._bind_shader_ambient()

        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()

        glUniformMatrix4fv(self.mloc_ambient, 1, GL_FALSE, move)
        glUniformMatrix4fv(self.vloc_ambient, 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ploc_ambient, 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_ambient, color_by)

        self._triangles_draw_call()
        self._unbind_shader()

    def render_diffuse(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render the mesh with diffuse shading.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._bind_shader_diffuse()
        self.light_position = self._calc_light_position()

        # MVP calcs
        move = interaction.camera.get_move_matrix()
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.mloc_diffuse, 1, GL_FALSE, move)
        glUniformMatrix4fv(self.vloc_diffuse, 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ploc_diffuse, 1, GL_FALSE, proj)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_diffuse, color_by)

        view_pos = interaction.camera.camera_pos
        glUniform3fv(self.vp_loc_shadows, 1, view_pos)

        # Set light uniforms
        glUniform3fv(self.lc_loc_diffuse, 1, self.light_color)
        glUniform3fv(self.lp_loc_diffuse, 1, self.light_position)

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
        self._render_shadow_map(interaction)
        self._render_model_with_shadows(interaction, gguip)

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
        glUseProgram(self.shader_shadow_map)
        glUniformMatrix4fv(
            self.lsm_loc_shadow_map, 1, GL_FALSE, self.light_space_matrix
        )

        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_shadow_map, 1, GL_FALSE, translation)

        glViewport(0, 0, self.shadow_map_resolution, self.shadow_map_resolution)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)

        # Only clearing depth buffer since there is no color attachement
        glClear(GL_DEPTH_BUFFER_BIT)

        self._triangles_draw_call()

    def _render_model_with_shadows(
        self, interaction: Interaction, gguip: GuiParameters
    ) -> None:
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
        glUseProgram(self.shader_shadows)

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.mloc_shadows, 1, GL_FALSE, move)
        glUniformMatrix4fv(self.ploc_shadows, 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.vloc_shadows, 1, GL_FALSE, view)

        self.set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_diffuse, color_by)

        # Set light uniforms
        glUniform3fv(self.lc_loc_shadows, 1, self.light_color)
        glUniform3fv(self.vp_loc_shadows, 1, interaction.camera.camera_pos)
        glUniform3fv(self.lp_loc_shadows, 1, self.light_position)

        glUniformMatrix4fv(self.lsm_loc_shadows, 1, GL_FALSE, self.light_space_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)

        self._triangles_draw_call()
        self._unbind_shader()

    def _triangles_draw_call(self):
        """Bind the vertex array object and calling draw function for triangles"""
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    def _lines_draw_call(self):
        """Bind the vertex array object and calling draw function for lines"""
        self._bind_vao_lines()
        glDrawElements(GL_LINES, len(self.edge_indices), GL_UNSIGNED_INT, None)
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
        glUseProgram(self.shader_lines)

    def _bind_shader_ambient(self) -> None:
        """Bind the shader for basic shading."""
        glUseProgram(self.shader_ambient)

    def _bind_shader_diffuse(self) -> None:
        """Bind the shader for diffuse shading."""
        glUseProgram(self.shader_diffuse)

    def _bind_shader_shadows(self) -> None:
        """Bind the shader for shading with shadows."""
        glUseProgram(self.shader_shadows)

    def _bind_shader_shadow_map(self) -> None:
        """Bind the shader for rendering shadow map."""
        glUseProgram(self.shader_shadow_map)

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

    def set_clipping_uniforms(self, gguip: GuiParameters):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        if self.guip.mesh_shading == MeshShading.wireframe:
            glUniform1f(self.cp_locs_lines[0], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.cp_locs_lines[1], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.cp_locs_lines[2], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.shaded_ambient:
            glUniform1f(self.cp_locs_ambient[0], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.cp_locs_ambient[1], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.cp_locs_ambient[2], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.shaded_diffuse:
            glUniform1f(self.cp_locs_diffuse[0], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.cp_locs_diffuse[1], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.cp_locs_diffuse[2], (zdom * gguip.clip_dist[2]))
        elif self.guip.mesh_shading == MeshShading.shaded_shadows:
            glUniform1f(self.cp_locs_shadows[0], (xdom * gguip.clip_dist[0]))
            glUniform1f(self.cp_locs_shadows[1], (ydom * gguip.clip_dist[1]))
            glUniform1f(self.cp_locs_shadows[2], (zdom * gguip.clip_dist[2]))
