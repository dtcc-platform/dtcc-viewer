import math
import glfw
import numpy as np
import time
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from string import Template
from dtcc_viewer.opengl.interaction import Action
from dtcc_viewer.opengl.wrp_data import LSDataWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.parameters import GuiParametersLS, GuiParameters
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_linestrings import LineStringsWrapper

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


class GlLineString:
    """A class for rendering road networks using OpenGL.

    This class handles the rendering of road networks using OpenGL.
    It provides methods to set up the rendering environment, bind shaders,
    and perform the necessary transformations for visualization.
    """

    vertices: np.ndarray  # All vertices in the road network
    line_indices: np.ndarray  #  Line indices for roads [[2 x n_roads],]
    guip: GuiParametersLS
    dict_data: dict
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

    data_texture: int  # Texture for data
    data_wrapper: LSDataWrapper  # Data wrapper for the mesh
    texture_slot: int  # GL_TEXTURE0, GL_TEXTURE1, etc.
    texture_int: int  # Texture index 0 for GL_TEXTURE0, 1 for GL_TEXTURE1, etc.

    def __init__(self, lss_wrapper: LineStringsWrapper):
        """Initialize the RoadNetworkGL object and set up rendering."""

        self.vertices = lss_wrapper.vertices
        self.line_indices = lss_wrapper.indices
        self.dict_data = lss_wrapper.dict_data
        self.name = lss_wrapper.name
        self.data_wrapper = lss_wrapper.data_wrapper

        self.n_vertices = len(self.vertices) // 9
        self.n_lines = len(self.line_indices) // 2

        self.shader: int
        self.uniform_locs = {}

        data_mat_dict = self.data_wrapper.data_mat_dict
        data_val_caps = self.data_wrapper.data_value_caps
        self.guip = GuiParametersLS(lss_wrapper.name, data_mat_dict, data_val_caps)
        self.bb_local = lss_wrapper.bb_local
        self.bb_global = lss_wrapper.bb_global

        self.texture_slot = None
        self.texture_int = None

    def preprocess(self):
        self._create_textures()
        self._create_geometry()
        self._create_shaders()

    def _create_textures(self) -> None:
        """Create textures for data."""
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

        info(f"Data texture created for {self.name}.")

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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Texel indices
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def _create_shaders(self) -> None:
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
        self.uniform_locs["color_inv"] = glGetUniformLocation(self.shader, "color_inv")
        self.uniform_locs["clip_x"] = glGetUniformLocation(self.shader, "clip_x")
        self.uniform_locs["clip_y"] = glGetUniformLocation(self.shader, "clip_y")
        self.uniform_locs["clip_z"] = glGetUniformLocation(self.shader, "clip_z")
        self.uniform_locs["cmap_idx"] = glGetUniformLocation(self.shader, "cmap_idx")
        self.uniform_locs["data_idx"] = glGetUniformLocation(self.shader, "data_idx")
        self.uniform_locs["data_min"] = glGetUniformLocation(self.shader, "data_min")
        self.uniform_locs["data_max"] = glGetUniformLocation(self.shader, "data_max")
        self.uniform_locs["data_tex"] = glGetUniformLocation(self.shader, "data_tex")

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

    def update_color_data(self) -> None:
        if self.guip.update_data_tex:
            self._update_data_texture()
            self.guip.update_data_tex = False

    def update_color_caps(self) -> None:
        if self.guip.update_caps:
            self.guip.calc_data_min_max()
            self.guip.update_caps = False

    def render(self, interaction: Action, gguip: GuiParameters) -> None:
        """Render roads as lines in the road network."""

        self._bind_vao()
        self._bind_shader()
        self._bind_data_texture()

        # MVP Calculations
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.uniform_locs["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uniform_locs["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uniform_locs["project"], 1, GL_FALSE, proj)

        self._set_clipping_uniforms(gguip)

        glUniform1i(self.uniform_locs["color_by"], int(self.guip.color))
        glUniform1i(self.uniform_locs["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uniform_locs["cmap_idx"], self.guip.cmap_idx)
        glUniform1i(self.uniform_locs["data_idx"], self.guip.data_idx)
        glUniform1f(self.uniform_locs["data_min"], self.guip.data_min)
        glUniform1f(self.uniform_locs["data_max"], self.guip.data_max)
        glUniform1i(self.uniform_locs["data_tex"], self.texture_int)

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

    def _bind_data_texture(self):
        """Bind the data texture."""
        glActiveTexture(self.texture_slot)
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

    def _unbind_data_texture(self):
        """Unbind the currently bound data texture."""
        glActiveTexture(self.texture_slot)
        glBindTexture(GL_TEXTURE_2D, 0)

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
