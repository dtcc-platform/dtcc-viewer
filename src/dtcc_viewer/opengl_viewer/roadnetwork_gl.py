import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.pointcloud_wrapper import PointCloudWrapper
from dtcc_viewer.opengl_viewer.shaders_lines import (
    vertex_shader_lines,
    fragment_shader_lines,
)
from dtcc_viewer.opengl_viewer.gui import GuiParametersRN, GuiParameters
from dtcc_viewer.opengl_viewer.utils import BoundingBox
from dtcc_viewer.opengl_viewer.roadnetwork_wrapper import RoadNetworkWrapper


class RoadNetworkGL:
    """A class for rendering road networks using OpenGL.

    This class handles the rendering of road networks using OpenGL.
    It provides methods to set up the rendering environment, bind shaders,
    and perform the necessary transformations for visualization.
    """

    vertices: np.ndarray  # All vertices in the road network
    line_indices: np.ndarray  #  Line indices for roads [[2 x n_roads],]
    guip: GuiParametersRN

    bb_local: BoundingBox
    bb_global: BoundingBox

    model_loc: int  # Uniform location for model matrix
    view_loc: int  # Uniform location for view matrix
    project_loc: int  # Uniform location for projection matrix
    color_by_loc: int  # Uniform location for color by variable
    scale_loc: int  # Uniform location for scaling parameter
    cp_locs: [int]  # Uniform location for clipping plane [x,y,z]

    VAO: int  # Vertex array object
    VBO: int  # Vertex buffer object
    EBO: int  # Element buffer object

    def __init__(self, rn_data_obj: RoadNetworkWrapper):
        """Initialize the RoadNetworkGL object and set up rendering.

        Parameters
        ----------
        rn_data_obj : RoadNetworkData
            Instance of the PointCloudData calss with points, colors and pc size.
        """

        self.vertices = rn_data_obj.vertices
        self.line_indices = rn_data_obj.indices

        self.cp_locs = [0, 0, 0]
        self.guip = GuiParametersRN(rn_data_obj.name)
        self.bb_local = rn_data_obj.bb_local
        self.bb_global = rn_data_obj.bb_global

        self._calc_model_scale()
        self._create_lines()
        self._create_shader()

    def _calc_model_scale(self) -> None:
        """Calculate the model scale from vertex positions."""

        xdom = self.bb_local.xdom
        ydom = self.bb_local.ydom

        if self.bb_global is not None:
            xdom = self.bb_global.xdom
            ydom = self.bb_global.ydom

        self.diameter_xy = math.sqrt(xdom * xdom + ydom * ydom)
        self.radius_xy = self.diameter_xy / 2.0

    def _create_lines(self) -> None:
        """Set up vertex and element buffers for line rendering."""

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        size = len(self.vertices) * 4
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.line_indices) * 4
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.line_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def render(self, interaction: Interaction, gguip: GuiParameters) -> None:
        """Render roads as lines in the road network.

        Parameters
        ----------
        interaction : Interaction
            The Interaction object containing camera and user interaction information.
        """

        self._bind_shader()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, move)
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, view)
        glUniformMatrix4fv(self.project_loc, 1, GL_FALSE, proj)

        self._set_clipping_uniforms(gguip)

        color_by = int(self.guip.color_rn)
        glUniform1i(self.color_by_loc, color_by)

        self._bind_vao()
        glDrawElements(GL_LINES, len(self.line_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

        self._unbind_shader()

    def _create_shader(self) -> None:
        """Create and compile the shader program."""

        self._bind_vao()

        self.shader = compileProgram(
            compileShader(vertex_shader_lines, GL_VERTEX_SHADER),
            compileShader(fragment_shader_lines, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader)

        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.project_loc = glGetUniformLocation(self.shader, "project")
        self.color_by_loc = glGetUniformLocation(self.shader, "color_by")
        # self.scale_loc = glGetUniformLocation(self.shader, "scale")

        self.cp_locs[0] = glGetUniformLocation(self.shader, "clip_x")
        self.cp_locs[1] = glGetUniformLocation(self.shader, "clip_y")
        self.cp_locs[2] = glGetUniformLocation(self.shader, "clip_z")

    def _bind_shader(self) -> None:
        """Bind the shader program."""
        glUseProgram(self.shader)

    def _unbind_shader(self) -> None:
        """Unbind the shader program."""
        glUseProgram(0)

    def _bind_vao(self) -> None:
        """Bind the Vertex Array Object (VAO)."""
        glBindVertexArray(self.VAO)

    def _unbind_vao(self) -> None:
        """Unbind the currently bound vertex array object."""
        glBindVertexArray(0)

    def _set_clipping_uniforms(self, gguip: GuiParameters):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        glUniform1f(self.cp_locs[0], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.cp_locs[1], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.cp_locs[2], (zdom * gguip.clip_dist[2]))
