import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from string import Template
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.interaction import Action
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.shaders.shaders_raster import (
    vertex_shader_raster,
    fragment_shader_raster,
    fragment_shader_checker,
    fragment_shader_color_checker,
)

from dtcc_viewer.opengl.parameters import GuiParametersTexQuad, GuiParameters
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_roadnetwork import RoadNetworkWrapper
from dtcc_viewer.opengl.wrp_raster import RasterWrapper
from dtcc_viewer.shaders.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)


class GlRaster:
    """A class for rendering road networks using OpenGL.

    This class handles the rendering of road networks using OpenGL.
    It provides methods to set up the rendering environment, bind shaders,
    and perform the necessary transformations for visualization.
    """

    vertices: np.ndarray  # All vertices in the road network
    indices: np.ndarray  #  Quad indices
    guip: GuiParametersTexQuad  # GUI parameters for the texture quad
    name: str  # Name of the line string

    n_vertices: int  # Number of vertices
    n_lines: int  # Number of lines

    bb_local: BoundingBox
    bb_global: BoundingBox

    uniform_locs: dict  # Uniform locations for the shader program
    shader: int  # Shader program

    VAO: int  # Vertex array object
    VBO: int  # Vertex buffer object
    EBO: int  # Element buffer object

    def __init__(self, raster_w: RasterWrapper):
        """Initialize the RoadNetworkGL object and set up rendering."""

        self.vertices = raster_w.vertices
        self.indices = raster_w.indices

        self.data = raster_w.data
        self.data_texture = None
        self.data_min = np.min(self.data)
        self.data_max = np.max(self.data)

        self.shader: int
        self.uniform_locs = {}

        self.guip = GuiParametersTexQuad(raster_w.name)
        self.bb_local = raster_w.bb_local
        self.bb_global = raster_w.bb_global

        self._get_max_texture_size()

        self._create_triangels()
        self._create_texture_2()
        self._create_shader()

    def _create_triangels(self) -> None:
        """Set up vertex and element buffers for mesh rendering."""
        # ----------------- TRIANGLES for shaded display ------------------#

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        size = len(self.vertices) * 4  # Size in bytes
        self.VBO_debug = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_debug)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.indices) * 4  # Size in bytes
        self.EBO_debug = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_debug)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.indices, GL_STATIC_DRAW)

        # Position (x, y, z)
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        # Texture coordinates (x, y)
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))

    def _get_max_texture_size(self):
        max_texture_size = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
        info(f"Max texture size: {max_texture_size} x {max_texture_size}")
        return max_texture_size

    def _create_texture_2(self):

        # Assuming your data is stored in a 2D array named data, with width and height dimensions
        width = self.data.shape[1]
        height = self.data.shape[0]

        # Generate texture ID
        self.data_texture = glGenTextures(1)

        # Bind the texture
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

        # Set texture parameters (e.g., wrapping and filtering modes)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        # Specify the texture image data
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RED, width, height, 0, GL_RED, GL_FLOAT, self.data
        )

        # Unbind the texture
        glBindTexture(GL_TEXTURE_2D, 0)

    def _create_shader(self) -> None:
        """Create and compile the shader program."""

        glBindVertexArray(self.VAO)

        vertex_shader = vertex_shader_raster
        # fragment_shader = fragment_shader_raster
        # fragment_shader = fragment_shader_checker
        fragment_shader = fragment_shader_color_checker

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

        self.uniform_locs["data_tex"] = glGetUniformLocation(
            self.shader, "data_texture"
        )

        # Set data based uniforms that won't change
        glUniform1i(self.uniform_locs["data_tex"], 0)  # Set the texture unit to 0
        glUniform1f(self.uniform_locs["data_min"], self.data_min)
        glUniform1f(self.uniform_locs["data_max"], self.data_max)

    def update_color_caps(self):
        if self.guip.update_caps:
            self.guip.calc_data_min_max()
            self.guip.update_caps = False

    def render(self, interaction: Action, gguip: GuiParameters) -> None:
        """Render roads as lines in the road network."""
        # self._render_pass_1(interaction, gguip)
        glUseProgram(self.shader)

        # Bind the texture
        glActiveTexture(GL_TEXTURE0)  # Activate texture unit 0
        glBindTexture(GL_TEXTURE_2D, self.data_texture)
        glUniform1i(self.uniform_locs["data_tex"], 0)  # Set the texture unit to 0

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

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        glUseProgram(0)

    def _set_clipping_uniforms(self, gguip: GuiParameters):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        glUniform1f(self.uniform_locs["clip_x"], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.uniform_locs["clip_y"], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.uniform_locs["clip_z"], (zdom * gguip.clip_dist[2]))
