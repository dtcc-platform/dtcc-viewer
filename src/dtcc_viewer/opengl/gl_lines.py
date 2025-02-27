import math
import glfw
import numpy as np
import time
from pprint import pp
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from string import Template
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.data_wrapper import LinesDataWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.parameters import GuiParametersLines, GuiParametersGlobal
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper
from dtcc_viewer.opengl.gl_object import GlObject

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


class GlLines(GlObject):
    """A class for rendering road networks using OpenGL.

    This class handles the rendering of road networks using OpenGL.
    It provides methods to set up the rendering environment, bind shaders,
    and perform the necessary transformations for visualization.

    Attributes
    ----------
    vertices : np.ndarray
        All vertices in the road network.
    line_indices : np.ndarray
        Line indices for roads [[2 x n_roads],].
    guip : GuiParametersLines
        GUI parameters for the lines.
    name : str
        Name of the line string.
    n_vertices : int
        Number of vertices.
    n_lines : int
        Number of lines.
    bb_local : BoundingBox
        Local bounding box.
    bb_global : BoundingBox
        Global bounding box.
    uniform_locs : dict
        Uniform locations for the shader program.
    shader : int
        Shader program.
    model_loc : int
        Uniform location for model matrix.
    view_loc : int
        Uniform location for view matrix.
    project_loc : int
        Uniform location for projection matrix.
    color_by_loc : int
        Uniform location for color by variable.
    scale_loc : int
        Uniform location for scaling parameter.
    cp_locs : list[int]
        Uniform location for clipping plane [x,y,z].
    VAO : int
        Vertex array object.
    VBO : int
        Vertex buffer object.
    EBO : int
        Element buffer object.
    """

    vertices: np.ndarray  # All vertices in the road network
    line_indices: np.ndarray  #  Line indices for roads [[2 x n_roads],]
    guip: GuiParametersLines
    name: str  # Name of the line string

    n_vertices: int  # Number of vertices
    n_lines: int  # Number of lines

    bb_local: BoundingBox
    bb_global: BoundingBox

    uniform_locs: dict  # Uniform locations for the shader program
    shader: int  # Shader program

    model_loc: int  # Uniform location for model matrix
    view_loc: int  # Uniform location for view matrix
    project_loc: int  # Uniform location for projection matrix
    color_by_loc: int  # Uniform location for color by variable
    scale_loc: int  # Uniform location for scaling parameter
    cp_locs: list[int]  # Uniform location for clipping plane [x,y,z]

    VAO: int  # Vertex array object
    VBO: int  # Vertex buffer object
    EBO: int  # Element buffer object

    def __init__(self, wrapper: LineStringWrapper, draw_colors: bool = True):
        """Initialize the RoadNetworkGL object and set up rendering.

        Parameters
        ----------
        wrapper : LineStringWrapper
            Wrapper for line string data.
        draw_colors : bool, optional
            Whether to draw colors (default is True).
        """

        self.vertices = wrapper.vertices
        self.line_indices = wrapper.indices
        self.name = wrapper.name
        self.data_wrapper = wrapper.data_wrapper

        self.n_vertices = len(self.vertices) // 6
        self.n_lines = len(self.line_indices) // 2

        self.shader: int
        self.uniform_locs = {}

        data_mat_dict = self.data_wrapper.data_mat_dict
        data_min_max = self.data_wrapper.data_min_max
        self.guip = GuiParametersLines(wrapper.name, data_mat_dict, data_min_max)
        self.bb_local = wrapper.bb_local
        self.bb_global = wrapper.bb_global

        self.texture_slot = None
        self.texture_idx = None

        self.guip.color = draw_colors

    def _create_textures(self) -> None:
        """Create textures for data."""
        self._create_data_texture()

    def _create_geometry(self) -> None:
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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Texel indices
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        # Id
        glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(20))

        glBindVertexArray(0)

    def _create_shaders(self) -> None:
        """Create and compile the shader program."""

        self._bind_vao()

        vertex_shader = vertex_shader_lines
        fragment_shader = fragment_shader_lines

        vertex_shader = Template(vertex_shader).substitute(
            color_map_0=color_map_turbo,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_rainbow,
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
        self.uniform_locs["color_inv"] = glGetUniformLocation(self.shader, "color_inv")
        self.uniform_locs["clip_x"] = glGetUniformLocation(self.shader, "clip_x")
        self.uniform_locs["clip_y"] = glGetUniformLocation(self.shader, "clip_y")
        self.uniform_locs["clip_z"] = glGetUniformLocation(self.shader, "clip_z")
        self.uniform_locs["cmap_idx"] = glGetUniformLocation(self.shader, "cmap_idx")
        self.uniform_locs["data_idx"] = glGetUniformLocation(self.shader, "data_idx")
        self.uniform_locs["data_min"] = glGetUniformLocation(self.shader, "data_min")
        self.uniform_locs["data_max"] = glGetUniformLocation(self.shader, "data_max")
        self.uniform_locs["data_tex"] = glGetUniformLocation(self.shader, "data_tex")

    def render(self, action: Action) -> None:
        """Render lines.

        Parameters
        ----------
        action : Action
            The action containing camera and GUI parameters.
        """

        self._bind_vao()
        self._bind_shader()
        self._bind_data_texture()

        # MVP Calculations
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.uniform_locs["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uniform_locs["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uniform_locs["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(action.gguip)

        glUniform1i(self.uniform_locs["color_by"], int(self.guip.color))
        glUniform1i(self.uniform_locs["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uniform_locs["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uniform_locs["data_idx"], self.guip.data_idx)
        glUniform1f(self.uniform_locs["data_min"], self.guip.data_min)
        glUniform1f(self.uniform_locs["data_max"], self.guip.data_max)
        glUniform1i(self.uniform_locs["data_tex"], self.texture_idx)

        glDrawElements(GL_LINES, len(self.line_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()
        self._unbind_data_texture()

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

    def _set_clipping_uniforms(self, gguip: GuiParametersGlobal):
        """Set the clipping uniforms for the shader program.

        Parameters
        ----------
        gguip : GuiParametersGlobal
            Global GUI parameters.
        """
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        glUniform1f(self.uniform_locs["clip_x"], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.uniform_locs["clip_y"], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.uniform_locs["clip_z"], (zdom * gguip.clip_dist[2]))
