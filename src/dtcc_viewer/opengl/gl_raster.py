import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from string import Template
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.gl_object import GlObject

from dtcc_viewer.shaders.shaders_raster import (
    vertex_shader_raster,
    fragment_shader_raster_data,
    fragment_shader_raster_rgb,
    fragment_shader_raster_rgba,
)

from dtcc_viewer.opengl.parameters import GuiParametersRaster, GuiParametersGlobal
from dtcc_viewer.opengl.utils import BoundingBox, RasterType
from dtcc_viewer.opengl.wrp_raster import RasterWrapper
from dtcc_viewer.shaders.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)


class GlRaster(GlObject):
    """A class for rendering rasters using OpenGL.

    Three types of rasters can be handled: data, RGB, and RGBA. The data raster
    stores data and displays it using a color map. The RGB(A) raster displays RGB(A)
    data using the specified channels.

    TODO: Split the data, RGB, and RGBA rasters into separate classes with a common
    base class.


    Attributes
    ----------
    vertices : np.ndarray
        Vertices for the quad on which to draw the raster texture.
    indices : np.ndarray
        Indices for the quad.
    guip : GuiParametersRaster
        GUI parameters for the texture quad.
    name : str
        Name of the raster.
    n_vertices : int
        Number of vertices.
    n_lines : int
        Number of lines.
    bb_local : BoundingBox
        Local bounding box.
    bb_global : BoundingBox
        Global bounding box.
    type : RasterType
        Type of raster.
    data_texture : int
        Texture for the data.
    rgb_texture : int
        Texture for the color.
    uniform_locs : dict
        Uniform locations for the shader program.
    shader : int
        Shader program.
    VAO : int
        Vertex array object.
    VBO : int
        Vertex buffer object.
    EBO : int
        Element buffer object.
    """

    vertices: np.ndarray
    indices: np.ndarray
    guip: GuiParametersRaster
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox
    type: RasterType
    data_texture: int
    rgb_texture: int
    uniform_locs: dict
    shader: int
    VAO: int
    VBO: int
    EBO: int

    def __init__(self, raster_w: RasterWrapper):
        """Initialize the GlRaster object and set up rendering."""
        self.vertices = raster_w.vertices
        self.indices = raster_w.indices
        self.type = raster_w.type
        self.data = raster_w.data
        self.data_min = np.min(self.data)
        self.data_max = np.max(self.data)
        self.data_texture = None
        self.rgb_texture = None
        self.rgba_texture = None
        self.aspect_ratio = 1.0
        self.shader = 0
        self.uniform_locs = {}
        self.guip = GuiParametersRaster(raster_w.name, self.type)
        self.bb_local = raster_w.bb_local
        self.bb_global = raster_w.bb_global

        self._get_max_texture_size()
        self._get_max_texture_slots()

    def preprocess(self):
        """Preprocess method to create textures, geometry, and shaders."""
        self._create_textures()
        self._create_geometry()
        self._create_shaders()

    def _create_geometry(self) -> None:
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
        """Get max texture size for raster textures."""
        max_texture_size = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
        info(f"Max texture size: {max_texture_size} x {max_texture_size}")

    def _get_max_texture_slots(self):
        """Get max texture slots for raster textures."""
        n_slots = glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)
        n_slots_2 = glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)
        info(f"Max texture slots: {n_slots}")
        info(f"Max texture slots: {n_slots_2}")

    def _create_textures(self) -> None:
        """Create textures for the raster."""
        if self.type == RasterType.Data:
            self._create_data_texture()
        elif self.type == RasterType.RGB:
            self._create_rgb_texture()
        elif self.type == RasterType.RGBA:
            self._create_rgba_texture()

        info(f"Raster texture size: {self.width} x {self.height}")
        info(f"Data shape: {self.data.shape}")

    def _create_data_texture(self):
        """Create texture for data storage."""
        # Assuming data is stored in a 2D array, with width and height dimensions
        self.width = self.data.shape[0]
        self.height = self.data.shape[1]
        self.aspect_ratio = self.width / self.height

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
            GL_TEXTURE_2D,
            0,
            GL_RED,
            self.width,
            self.height,
            0,
            GL_RED,
            GL_FLOAT,
            self.data,
        )

        # Unbind the texture
        glBindTexture(GL_TEXTURE_2D, 0)

    def _create_rgb_texture(self):
        """Create texture for RGB data storage."""
        # Assuming your data is stored in a 2D array named data, with width and height dimensions
        self.width = self.data.shape[0]
        self.height = self.data.shape[1]
        self.aspect_ratio = self.width / self.height

        # Generate texture ID
        self.rgb_texture = glGenTextures(1)

        # Bind the texture
        glBindTexture(GL_TEXTURE_2D, self.rgb_texture)

        # Set texture parameters (e.g., wrapping and filtering modes)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        # Specify the texture image data
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            self.data,
        )

        # Unbind the texture
        glBindTexture(GL_TEXTURE_2D, 0)

    def _create_rgba_texture(self):
        """Create texture for RGBA data storage."""
        # Assuming your data is stored in a 2D array named data, with width and height dimensions
        self.width = self.data.shape[0]
        self.height = self.data.shape[1]
        self.aspect_ratio = self.width / self.height

        # Generate texture ID
        self.rgba_texture = glGenTextures(1)

        # Bind the texture
        glBindTexture(GL_TEXTURE_2D, self.rgba_texture)

        # Set texture parameters (e.g., wrapping and filtering modes)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        # Specify the texture image data
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            self.data,
        )

        # Unbind the texture
        glBindTexture(GL_TEXTURE_2D, 0)

    def _create_shaders(self) -> None:
        """Create and compile the shader program."""

        if self.type == RasterType.Data:
            self._create_data_shader()
        elif self.type == RasterType.RGB:
            self._create_rgb_shader()
        elif self.type == RasterType.RGBA:
            self._create_rgba_shader()

    def _create_data_shader(self) -> None:

        glBindVertexArray(self.VAO)

        vertex_shader = vertex_shader_raster
        fragment_shader = fragment_shader_raster_data

        fragment_shader = Template(fragment_shader).substitute(
            color_map_0=color_map_rainbow,
            color_map_1=color_map_inferno,
            color_map_2=color_map_black_body,
            color_map_3=color_map_turbo,
            color_map_4=color_map_viridis,
        )

        self._create_shader_common(vertex_shader, fragment_shader)

        self.uniform_locs["color_by"] = glGetUniformLocation(self.shader, "color_by")
        self.uniform_locs["cmap_idx"] = glGetUniformLocation(self.shader, "cmap_idx")
        self.uniform_locs["data_idx"] = glGetUniformLocation(self.shader, "data_idx")
        self.uniform_locs["data_min"] = glGetUniformLocation(self.shader, "data_min")
        self.uniform_locs["data_max"] = glGetUniformLocation(self.shader, "data_max")

        # Set data based uniforms that won't change
        glUniform1f(self.uniform_locs["data_min"], self.data_min)
        glUniform1f(self.uniform_locs["data_max"], self.data_max)

    def _create_rgb_shader(self) -> None:
        glBindVertexArray(self.VAO)
        vertex_shader = vertex_shader_raster
        fragment_shader = fragment_shader_raster_rgb
        self._create_shader_common(vertex_shader, fragment_shader)

    def _create_rgba_shader(self) -> None:
        glBindVertexArray(self.VAO)
        vertex_shader = vertex_shader_raster
        fragment_shader = fragment_shader_raster_rgba
        self._create_shader_common(vertex_shader, fragment_shader)

    def _create_shader_common(self, vertex_shader, fragment_shader) -> None:
        # Shader function calls common for all shaders
        self.shader = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER),
            compileShader(fragment_shader, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader)

        self.uniform_locs["model"] = glGetUniformLocation(self.shader, "model")
        self.uniform_locs["view"] = glGetUniformLocation(self.shader, "view")
        self.uniform_locs["project"] = glGetUniformLocation(self.shader, "project")
        self.uniform_locs["clip_x"] = glGetUniformLocation(self.shader, "clip_x")
        self.uniform_locs["clip_y"] = glGetUniformLocation(self.shader, "clip_y")
        self.uniform_locs["clip_z"] = glGetUniformLocation(self.shader, "clip_z")
        self.uniform_locs["color_inv"] = glGetUniformLocation(self.shader, "color_inv")
        self.uniform_locs["r_channel"] = glGetUniformLocation(self.shader, "r_channel")
        self.uniform_locs["g_channel"] = glGetUniformLocation(self.shader, "g_channel")
        self.uniform_locs["b_channel"] = glGetUniformLocation(self.shader, "b_channel")
        self.uniform_locs["asp_rat"] = glGetUniformLocation(self.shader, "asp_rat")
        self.uniform_locs["data_tex"] = glGetUniformLocation(
            self.shader, "data_texture"
        )

        glUniform1i(self.uniform_locs["data_tex"], 0)  # Set the texture unit to 0
        glUniform1f(self.uniform_locs["asp_rat"], self.aspect_ratio)

    def update_data_caps(self):
        """Update data min and max values."""
        if self.guip.update_caps:
            self.guip.calc_data_min_max()
            self.guip.update_caps = False

    def render(self, action: Action) -> None:
        """Render raster."""
        if self.type == RasterType.Data:
            self._render_data(action)
        elif self.type == RasterType.RGB:
            self._render_rgb(action)
        elif self.type == RasterType.RGBA:
            self._render_rgba(action)

    def _render_data(self, action: Action) -> None:
        """Render the data raster."""
        glUseProgram(self.shader)

        # Bind the texture
        glActiveTexture(GL_TEXTURE0)  # Activate texture unit 0
        glBindTexture(GL_TEXTURE_2D, self.data_texture)
        glUniform1i(self.uniform_locs["data_tex"], 0)  # Set the texture unit to 0

        self._render_common(action)

        glUniform1i(self.uniform_locs["color_by"], int(self.guip.color))
        glUniform1i(self.uniform_locs["cmap_idx"], self.guip.cmap_idx)

        self._draw_call()

    def _render_rgb(self, action: Action) -> None:
        """Render the RGB raster."""
        glUseProgram(self.shader)

        # Bind the texture
        glActiveTexture(GL_TEXTURE0)  # Activate texture unit 0
        glBindTexture(GL_TEXTURE_2D, self.rgb_texture)
        glUniform1i(self.uniform_locs["data_tex"], 0)  # Set the texture unit to 0
        glUniform1i(self.uniform_locs["r_channel"], self.guip.channels[0])
        glUniform1i(self.uniform_locs["g_channel"], self.guip.channels[1])
        glUniform1i(self.uniform_locs["b_channel"], self.guip.channels[2])

        self._render_common(action)
        self._draw_call()

    def _render_rgba(self, action: Action) -> None:
        """Render the RGBA raster."""
        glUseProgram(self.shader)

        glActiveTexture(GL_TEXTURE0)  # Activate texture unit 0
        glBindTexture(GL_TEXTURE_2D, self.rgba_texture)
        glUniform1i(self.uniform_locs["data_tex"], 0)  # Set the texture unit to 0
        glUniform1i(self.uniform_locs["r_channel"], self.guip.channels[0])
        glUniform1i(self.uniform_locs["g_channel"], self.guip.channels[1])
        glUniform1i(self.uniform_locs["b_channel"], self.guip.channels[2])

        self._render_common(action)
        self._draw_call()

    def _render_common(self, action: Action):
        """Common rendering code for all raster types."""
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.uniform_locs["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uniform_locs["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uniform_locs["project"], 1, GL_FALSE, proj)
        glUniform1i(self.uniform_locs["color_inv"], int(self.guip.invert_cmap))
        self._set_clipping_uniforms(action.gguip)
        pass

    def _draw_call(self):
        """Draw call for the raster."""
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)

    def _set_clipping_uniforms(self, gguip: GuiParametersGlobal):
        """Set clipping uniforms for the shader program."""
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        glUniform1f(self.uniform_locs["clip_x"], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.uniform_locs["clip_y"], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.uniform_locs["clip_z"], (zdom * gguip.clip_dist[2]))
