import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.gui import GuiParameters, GuiParametersMesh

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
    """Represents a 3D mesh in OpenGL and provides methods for rendering with different shaders.

    Attributes
    ----------
    guip : GuiParametersMesh
        Information used by the GUI.
    vertices : np.ndarray
        Array containing vertex information (x, y, z, r, g, b, nx, ny, nz).
    face_indices : np.ndarray
        Array containing face indices.
    edge_indices : np.ndarray
        Array containing edge indices.
    """

    guip: GuiParametersMesh  # Information used by the Gui
    vertices: np.ndarray  # [n_vertices x 9] each row has (x, y, z, r, g, b, nx, ny, nz)
    face_indices: np.ndarray  # [n_faces x 3] each row has three vertex indices
    edge_indices: np.ndarray  # [n_edges x 2] each row has

    def __init__(
        self, name: str, vertices: np.ndarray, faces: np.ndarray, edges: np.ndarray
    ):
        """Initialize the MeshGL object with vertex, face, and edge information.

        Parameters
        ----------
        name : str
            The name of the mesh.
        vertices : np.ndarray
            Array containing vertex information (x, y, z, r, g, b, nx, ny, nz).
        faces : np.ndarray
            Array containing face indices.
        edges : np.ndarray
            Array containing edge indices.
        """
        self.guip = GuiParametersMesh(name)

        self.vertices = vertices
        self.face_indices = faces
        self.edge_indices = edges

        self._calc_model_scale()
        self._create_lines()
        self._create_triangels()
        self._create_shadow_map()
        self._create_shader_lines()
        self._create_shader_basic()
        self._create_shader_diffuse()
        self._create_shader_shadows()
        self._create_shader_shadow_map()
        self._set_constats()

    # Utility functions
    def _calc_model_scale(self) -> None:
        """Calculate the model scale from vertex positions."""
        xmin = self.vertices[0::3].min()
        xmax = self.vertices[0::3].max()
        ymin = self.vertices[1::3].min()
        ymax = self.vertices[1::3].max()

        xdom = xmax - xmin
        ydom = ymax - ymin

        self.diameter_xy = math.sqrt(xdom * xdom + ydom * ydom)
        self.radius_xy = self.diameter_xy / 2.0

    def _set_constats(self) -> None:
        """Set constant values like light position and color."""
        self.light_position = np.array([500.0, 500.0, 400.0], dtype=np.float32)
        self.light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.loop_counter = 120

    # Setup geometry
    def _create_triangels(self) -> None:
        """Set up vertex and element buffers for triangle rendering."""
        # ----------------- TRIANGLES for shaded display ------------------#

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO_triangels = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_triangels)

        # Vertex buffer
        self.VBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_triangels)
        glBufferData(
            GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW
        )  # Second argument is nr of bytes

        # Element buffer
        self.EBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_triangels)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            len(self.face_indices) * 4,
            self.face_indices,
            GL_STATIC_DRAW,
        )

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

    def _create_lines(self) -> None:
        """Set up vertex and element buffers for wireframe rendering."""
        # -------------- EDGES for wireframe display ---------------- #
        self.VAO_edge = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_edge)

        # Vertex buffer
        self.VBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_edge)
        glBufferData(
            GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW
        )  # Second argument is nr of bytes

        self.EBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_edge)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            len(self.edge_indices) * 4,
            self.edge_indices,
            GL_STATIC_DRAW,
        )

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        glBindVertexArray(0)

    # Setup frambuffer for shadow map
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
        border_color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_map, 0
        )
        glDrawBuffer(
            GL_NONE
        )  # Disable drawing to the color attachements since we only care about the depth
        glReadBuffer(GL_NONE)  # We don't want to read color attachements either
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # Setup shaders
    def _create_shader_lines(self) -> None:
        """Create shader for wireframe rendering."""
        self._bind_vao_lines()
        self.shader_lines = compileProgram(
            compileShader(vertex_shader_lines, GL_VERTEX_SHADER),
            compileShader(fragment_shader_lines, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader_lines)

        self.mloc_lines = glGetUniformLocation(self.shader_lines, "model")
        self.ploc_lines = glGetUniformLocation(self.shader_lines, "project")
        self.vloc_lines = glGetUniformLocation(self.shader_lines, "view")
        self.cb_loc_lines = glGetUniformLocation(self.shader_lines, "color_by")

    def _create_shader_basic(self) -> None:
        """Create shader for basic shading."""
        self._bind_vao_triangels()
        self.shader_ambient = compileProgram(
            compileShader(vertex_shader_ambient, GL_VERTEX_SHADER),
            compileShader(fragment_shader_ambient, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_ambient)

        self.mloc_ambient = glGetUniformLocation(self.shader_ambient, "model")
        self.ploc_ambient = glGetUniformLocation(self.shader_ambient, "project")
        self.vloc_ambient = glGetUniformLocation(self.shader_ambient, "view")
        self.cb_loc_ambient = glGetUniformLocation(self.shader_ambient, "color_by")

    def _create_shader_diffuse(self) -> None:
        """
        Create shader for diffuse shading.
        """
        self._bind_vao_triangels()
        self.shader_diffuse = compileProgram(
            compileShader(vertex_shader_diffuse, GL_VERTEX_SHADER),
            compileShader(fragment_shader_diffuse, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_diffuse)

        self.mloc_diffuse = glGetUniformLocation(self.shader_diffuse, "model")
        self.ploc_diffuse = glGetUniformLocation(self.shader_diffuse, "project")
        self.vloc_diffuse = glGetUniformLocation(self.shader_diffuse, "view")
        self.cb_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "color_by")

        self.oc_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "object_color")
        self.lc_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "light_color")
        self.lp_loc_diffuse = glGetUniformLocation(
            self.shader_diffuse, "light_position"
        )
        self.vp_loc_diffuse = glGetUniformLocation(self.shader_diffuse, "view_position")

    def _create_shader_shadows(self) -> None:
        """Create shader for shading with shadows."""
        self._bind_vao_triangels()
        self.shader_shadows = compileProgram(
            compileShader(vertex_shader_shadows, GL_VERTEX_SHADER),
            compileShader(fragment_shader_shadows, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_shadows)

        self.mloc_shadows = glGetUniformLocation(self.shader_shadows, "model")
        self.ploc_shadows = glGetUniformLocation(self.shader_shadows, "project")
        self.vloc_shadows = glGetUniformLocation(self.shader_shadows, "view")
        self.cb_loc_shadows = glGetUniformLocation(self.shader_shadows, "color_by")
        self.oc_loc_shadows = glGetUniformLocation(self.shader_shadows, "object_color")
        self.lc_loc_shadows = glGetUniformLocation(self.shader_shadows, "light_color")
        self.lp_loc_shadows = glGetUniformLocation(
            self.shader_shadows, "light_position"
        )
        self.vp_loc_shadows = glGetUniformLocation(self.shader_shadows, "view_position")
        self.lsm_loc_shadows = glGetUniformLocation(
            self.shader_shadows, "light_space_matrix"
        )

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

    # Private render functions
    def _render_shadow_map(self, interaction: Interaction) -> None:
        """Render the shadow map.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        # first pass: Capture shadow map
        rad = self.radius_xy
        if self.guip.animate_light:
            self.loop_counter += 1

        rot_step = self.loop_counter / 120.0
        self.light_position = np.array(
            [
                math.sin(rot_step) * rad,
                math.cos(rot_step) * rad,
                abs(math.sin(rot_step / 2.0)) * 0.7 * rad,
            ],
            dtype=np.float32,
        )

        light_projection = pyrr.matrix44.create_orthogonal_projection(
            -rad, rad, -rad, rad, 0.1, 1.25 * self.diameter_xy, dtype=np.float32
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

        # Drawcall
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    def _render_model_with_shadows(self, interaction: Interaction) -> None:
        """Render the model with shadows.

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

        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_shadows, 1, GL_FALSE, translation)

        # Camera input
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_shadows, 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.vloc_shadows, 1, GL_FALSE, view)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_diffuse, color_by)

        # Set light uniforms
        glUniform3fv(self.lc_loc_shadows, 1, self.light_color)
        glUniform3fv(self.vp_loc_shadows, 1, interaction.camera.camera_pos)
        glUniform3fv(self.lp_loc_shadows, 1, self.light_position)

        glUniformMatrix4fv(self.lsm_loc_shadows, 1, GL_FALSE, self.light_space_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)

        # Drawcall
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    # Render mesh fancy shadows
    def render_shadows(self, interaction: Interaction) -> None:
        """Render the mesh with shadows.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._render_shadow_map(interaction)
        self._render_model_with_shadows(interaction)

    # Render mesh fancy
    def render_diffuse(self, interaction: Interaction) -> None:
        """Render the mesh with diffuse shading.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._bind_vao_triangels()
        self._bind_shader_fancy()

        rad = self.radius_xy

        if self.guip.animate_light:
            self.loop_counter += 1

        rot_step = self.loop_counter / 120.0
        self.light_position = np.array(
            [
                math.sin(rot_step) * rad,
                math.cos(rot_step) * rad,
                abs(math.sin(rot_step / 2.0)) * 0.7 * rad,
            ],
            dtype=np.float32,
        )

        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_diffuse, 1, GL_FALSE, move)

        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.vloc_diffuse, 1, GL_FALSE, view)

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_diffuse, 1, GL_FALSE, projection)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_diffuse, color_by)

        view_pos = interaction.camera.camera_pos
        glUniform3fv(self.vp_loc_shadows, 1, view_pos)

        # Set light uniforms
        glUniform3fv(self.lc_loc_diffuse, 1, self.light_color)
        glUniform3fv(self.lp_loc_diffuse, 1, self.light_position)

        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

    # Render mesh basic
    def render_ambient(self, interaction: Interaction) -> None:
        """Render the mesh with ambient shading.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """
        self._bind_vao_triangels()
        self._bind_shader_basic()

        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_ambient, 1, GL_FALSE, move)

        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.vloc_ambient, 1, GL_FALSE, view)

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_ambient, 1, GL_FALSE, projection)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_ambient, color_by)

        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

    # Render mesh lines
    def render_lines(self, interaction: Interaction) -> None:
        """Render wireframe lines of the mesh.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """

        self._bind_vao_lines()
        self._bind_shader_lines()

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_lines, 1, GL_FALSE, projection)

        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.vloc_lines, 1, GL_FALSE, view)

        color_by = int(self.guip.color_mesh)
        glUniform1i(self.cb_loc_lines, color_by)

        glDrawElements(GL_LINES, len(self.edge_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

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

    def _bind_shader_fancy_shadows(self) -> None:
        """Bind the shader for shading with shadows."""
        glUseProgram(self.shader_shadows)

    def _bind_shader_fancy(self) -> None:
        """Bind the shader for diffuse shading."""
        glUseProgram(self.shader_diffuse)

    def _bind_shader_basic(self) -> None:
        """Bind the shader for basic shading."""
        glUseProgram(self.shader_ambient)

    def _bind_shader_shadow_map(self) -> None:
        """Bind the shader for rendering shadow map."""
        glUseProgram(self.shader_shadow_map)

    def _unbind_shader(self) -> None:
        """Unbind the currently bound shader."""
        glUseProgram(0)
