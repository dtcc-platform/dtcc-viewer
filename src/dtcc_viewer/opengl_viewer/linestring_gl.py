import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from string import Template
from dtcc_viewer.opengl_viewer.interaction import Action
from dtcc_viewer.opengl_viewer.pointcloud_wrapper import PointCloudWrapper
from dtcc_viewer.opengl_viewer.shaders_lines import (
    vertex_shader_lines,
    fragment_shader_lines,
)
from dtcc_viewer.opengl_viewer.parameters import GuiParametersLS, GuiParameters
from dtcc_viewer.opengl_viewer.utils import BoundingBox
from dtcc_viewer.opengl_viewer.roadnetwork_wrapper import RoadNetworkWrapper

from dtcc_viewer.opengl_viewer.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)


class LineStringGL:
    """A class for rendering road networks using OpenGL.

    This class handles the rendering of road networks using OpenGL.
    It provides methods to set up the rendering environment, bind shaders,
    and perform the necessary transformations for visualization.
    """

    vertices: np.ndarray  # All vertices in the road network
    line_indices: np.ndarray  #  Line indices for roads [[2 x n_roads],]
    guip: GuiParametersLS
    dict_data: dict

    bb_local: BoundingBox
    bb_global: BoundingBox

    uniform_locs: dict  # Uniform locations for the shader program
    shader: int  # Shader program

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
        """Initialize the RoadNetworkGL object and set up rendering."""

        self.vertices = rn_data_obj.vertices
        self.line_indices = rn_data_obj.indices
        self.dict_data = rn_data_obj.dict_data

        self.shader: int
        self.uniform_locs = {}

        self.guip = GuiParametersLS(rn_data_obj.name, self.dict_data)
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

        # Data
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def _create_shader(self) -> None:
        """Create and compile the shader program."""

        self._bind_vao()

        vertex_shader = vertex_shader_lines
        fragment_shader = fragment_shader_lines

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_rainbow,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_turbo,
            color_map_4=color_map_viridis,
        )

        self.shader = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader)

        self.uniform_locs["model"] = glGetUniformLocation(self.shader, "model")
        self.uniform_locs["view"] = glGetUniformLocation(self.shader, "view")
        self.uniform_locs["project"] = glGetUniformLocation(self.shader, "project")
        self.uniform_locs["color_by"] = glGetUniformLocation(self.shader, "color_by")
        self.uniform_locs["clip_x"] = glGetUniformLocation(self.shader, "clip_x")
        self.uniform_locs["clip_y"] = glGetUniformLocation(self.shader, "clip_y")
        self.uniform_locs["clip_z"] = glGetUniformLocation(self.shader, "clip_z")
        self.uniform_locs["cmap_idx"] = glGetUniformLocation(self.shader, "cmap_idx")
        self.uniform_locs["data_idx"] = glGetUniformLocation(self.shader, "data_idx")
        self.uniform_locs["data_min"] = glGetUniformLocation(self.shader, "data_min")
        self.uniform_locs["data_max"] = glGetUniformLocation(self.shader, "data_max")

    def update_color_caps(self):
        if self.guip.update_caps:
            self.guip.calc_data_min_max()
            self.guip.update_caps = False

    def render(self, interaction: Action, gguip: GuiParameters) -> None:
        """Render roads as lines in the road network."""

        self._bind_shader()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uniform_locs["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uniform_locs["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uniform_locs["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(gguip)

        glUniform1i(self.uniform_locs["color_by"], int(self.guip.color))
        glUniform1i(self.uniform_locs["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uniform_locs["data_idx"], self.guip.data_idx)
        glUniform1f(self.uniform_locs["data_min"], self.guip.data_min)
        glUniform1f(self.uniform_locs["data_max"], self.guip.data_max)

        self._bind_vao()
        glDrawElements(GL_LINES, len(self.line_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

        self._unbind_shader()

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

        glUniform1f(self.uniform_locs["clip_x"], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.uniform_locs["clip_y"], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.uniform_locs["clip_z"], (zdom * gguip.clip_dist[2]))
