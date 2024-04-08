import math
import glfw
import numpy as np
import pyrr
from pprint import pp
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.parameters import GuiParametersGlobal
from dtcc_viewer.opengl.utils import BoundingBox

from dtcc_viewer.shaders.shaders_grid import (
    vertex_shader_grid,
    fragment_shader_grid,
    vertex_shader_axes,
    fragment_shader_axes,
)


class GlGrid:
    """A class for rendering a grid and coordinate axes for the OpenGL scene."""

    bb_local: BoundingBox
    bb_global: BoundingBox
    ulocs_grid: dict  # Uniform locations for the shader program
    ulocs_axes: dict  # Uniform locations for the shader program
    shader_grid: int  # Shader program
    shader_axes: int  # Shader program

    VAO_grid: int  # Vertex array object
    VBO_grid: int  # Vertex buffer object
    EBO_grid: int  # Element buffer object

    VAO_axes: int  # Vertex array object
    VBO_axes: int  # Vertex buffer object
    EBO_axes: int  # Element buffer object

    nx: int  # Number of grid lines
    ny: int  # Number of grid lines

    grid_coords: np.ndarray  # Coordinates for the grid lines
    grid_indices: np.ndarray  # Indices for the grid lines

    grid_sizes: np.ndarray  # Grid sizes for the grid lines
    grid_spaces: np.ndarray  # Grid spacings for the grid lines

    def __init__(self, bb_global: BoundingBox):

        self.bb_global = bb_global
        self.bb_local = bb_global

        self.ulocs_grid = {}
        self.ulocs_axes = {}

        self.grid_spaces = np.array([0.25, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500])

        size = np.min([bb_global.xdom, bb_global.ydom])

        grid_size = (size, size)
        axes_size = size * 2
        grid_spacing = (1, 1)
        self._create_grid(grid_size, grid_spacing)
        self._create_axes(axes_size)
        self._create_vao_grid()
        self._create_vao_axes()
        self._create_shader_grid()
        self._create_shader_axes()

    def _update_grid_size(self, action: Action, gguip: GuiParametersGlobal) -> None:

        dtt = action.camera.distance_to_target
        # dtt2 = dtt * dtt
        dtt_min = 10
        dtt_max = 10000
        normalized_dtt = (dtt - dtt_min) / (dtt_max - dtt_min)

        spc_min = np.min(self.grid_spaces)
        spc_max = np.max(self.grid_spaces)
        spc = spc_min + normalized_dtt * (spc_max - spc_min)
        spc = self.find_nearest(self.grid_spaces, spc)

        gguip.grid_sf = spc

    def _create_grid(self, size: tuple, spacing: tuple) -> None:
        """Create a grid for rendering."""

        # Update size to be a multiple of the spacing
        xsize = np.ceil(size[0] / spacing[0]) * spacing[0]
        ysize = np.ceil(size[1] / spacing[1]) * spacing[1]

        n_gridlines_x = int(xsize / spacing[0]) + 1
        n_gridlines_y = int(ysize / spacing[1]) + 1

        # Generate coordinates grid line vertices for the 4 sides of the grid.
        xcoord = np.zeros((n_gridlines_x * 2 + n_gridlines_y * 2))
        x1 = np.arange(-xsize / 2.0, (xsize / 2.0) + spacing[0], spacing[0])
        x2 = x1
        x3 = np.repeat(-xsize / 2.0, n_gridlines_y)
        x4 = np.repeat(xsize / 2.0, n_gridlines_y)

        xcoord[0:n_gridlines_x] = x1
        xcoord[n_gridlines_x : n_gridlines_x * 2] = x2
        xcoord[n_gridlines_x * 2 : n_gridlines_x * 2 + n_gridlines_y] = x3
        xcoord[n_gridlines_x * 2 + n_gridlines_y :] = x4

        ycoord = np.zeros((n_gridlines_x * 2 + n_gridlines_y * 2))
        y1 = np.repeat(-ysize / 2.0, n_gridlines_x)
        y2 = np.repeat(ysize / 2.0, n_gridlines_x)
        y3 = np.arange(-ysize / 2.0, (ysize / 2.0) + spacing[1], spacing[1])
        y4 = y3

        ycoord[0:n_gridlines_x] = y1
        ycoord[n_gridlines_x : n_gridlines_x * 2] = y2
        ycoord[n_gridlines_x * 2 : n_gridlines_x * 2 + n_gridlines_y] = y3
        ycoord[n_gridlines_x * 2 + n_gridlines_y :] = y4

        zcoord = np.zeros((n_gridlines_x * 2 + n_gridlines_y * 2))
        coord = np.zeros((len(xcoord) * 3))
        coord[0::3] = xcoord
        coord[1::3] = ycoord
        coord[2::3] = zcoord

        self.grid_coords = np.array(coord, dtype="float32")

        # Generate indices for the grid lines
        indices = np.arange(0, len(xcoord), 1)
        indices1 = indices[0:n_gridlines_x]
        indices2 = indices[n_gridlines_x : n_gridlines_x * 2]
        indices3 = indices[n_gridlines_x * 2 : n_gridlines_x * 2 + n_gridlines_y]
        indices4 = indices[n_gridlines_x * 2 + n_gridlines_y :]

        self.grid_indices = np.zeros(((n_gridlines_x + n_gridlines_y), 2))
        self.grid_indices[0:n_gridlines_x, 0] = indices1
        self.grid_indices[0:n_gridlines_x, 1] = indices2
        self.grid_indices[n_gridlines_x : n_gridlines_x + n_gridlines_y, 0] = indices3
        self.grid_indices[n_gridlines_x : n_gridlines_x + n_gridlines_y, 1] = indices4

        self.grid_indices = np.array(self.grid_indices, dtype="uint32").flatten()

    def _create_axes(self, size: float) -> None:

        r = [1.0, 0, 0]
        g = [0, 1.0, 0]
        b = [0, 0, 1.0]

        vertices = np.zeros((6, 6))
        vertices[1, 0:3] = [size, 0, 0]
        vertices[3, 0:3] = [0, size, 0]
        vertices[5, 0:3] = [0, 0, size]

        vertices[0, 3:6] = r
        vertices[1, 3:6] = r
        vertices[2, 3:6] = g
        vertices[3, 3:6] = g
        vertices[4, 3:6] = b
        vertices[5, 3:6] = b

        self.axes_vertices = np.array(vertices, dtype="float32").flatten()
        self.axes_indices = np.array([0, 1, 2, 3, 4, 5], dtype="uint32")

    def _create_vao_grid(self) -> None:
        """Set up vertex and element buffers for line rendering."""

        self.VAO_grid = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_grid)

        # Vertex buffer
        size = len(self.grid_coords) * 4
        self.VBO_grid = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_grid)
        glBufferData(GL_ARRAY_BUFFER, size, self.grid_coords, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.grid_indices) * 4
        self.EBO_grid = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_grid)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.grid_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

        glBindVertexArray(0)

    def _create_vao_axes(self) -> None:
        """Set up vertex and element buffers for line rendering."""

        self.VAO_axes = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_axes)

        # Vertex buffer
        size = len(self.axes_vertices) * 4
        self.VBO_axes = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_axes)
        glBufferData(GL_ARRAY_BUFFER, size, self.axes_vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.axes_indices) * 4
        self.EBO_axes = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_axes)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.axes_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Colors
        glEnableVertexAttribArray(1)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def _create_shader_grid(self) -> None:
        """Create and compile the shader program."""

        glBindVertexArray(self.VAO_grid)
        self.shader_grid = compileProgram(
            compileShader(vertex_shader_grid, GL_VERTEX_SHADER),
            compileShader(fragment_shader_grid, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader_grid)

        self.ulocs_grid["model"] = glGetUniformLocation(self.shader_grid, "model")
        self.ulocs_grid["view"] = glGetUniformLocation(self.shader_grid, "view")
        self.ulocs_grid["project"] = glGetUniformLocation(self.shader_grid, "project")
        self.ulocs_grid["scale"] = glGetUniformLocation(self.shader_grid, "scale")
        self.ulocs_grid["color"] = glGetUniformLocation(self.shader_grid, "color")

    def _create_shader_axes(self) -> None:
        """Create and compile the shader program."""

        glBindVertexArray(self.VAO_axes)
        self.shader_axes = compileProgram(
            compileShader(vertex_shader_axes, GL_VERTEX_SHADER),
            compileShader(fragment_shader_axes, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader_axes)

        self.ulocs_axes["model"] = glGetUniformLocation(self.shader_axes, "model")
        self.ulocs_axes["view"] = glGetUniformLocation(self.shader_axes, "view")
        self.ulocs_axes["project"] = glGetUniformLocation(self.shader_axes, "project")

    def render(self, action: Action, gguip: GuiParametersGlobal) -> None:
        if gguip.show_grid:
            self._update_grid_size(action, gguip)
            self._render_grid(action, gguip)
        if gguip.show_axes:
            self._render_axes(action, gguip)

    def _render_grid(self, action: Action, gguip: GuiParametersGlobal) -> None:

        glBindVertexArray(self.VAO_grid)
        glUseProgram(self.shader_grid)

        # MVP Calculations
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(gguip)
        proj = action.camera.get_projection_matrix(gguip)
        glUniformMatrix4fv(self.ulocs_grid["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.ulocs_grid["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ulocs_grid["project"], 1, GL_FALSE, proj)

        c = self.adjust_color_brightness(gguip.color, 0.25)
        glUniform3f(self.ulocs_grid["color"], c[0], c[1], c[2])
        glUniform1f(self.ulocs_grid["scale"], gguip.grid_sf)

        glDrawElements(GL_LINES, len(self.grid_indices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glUseProgram(0)

    def _render_axes(self, action: Action, gguip: GuiParametersGlobal) -> None:

        glBindVertexArray(self.VAO_axes)
        glUseProgram(self.shader_axes)

        # MVP Calculations
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(gguip)
        proj = action.camera.get_projection_matrix(gguip)
        glUniformMatrix4fv(self.ulocs_axes["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.ulocs_axes["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ulocs_axes["project"], 1, GL_FALSE, proj)

        glDrawElements(GL_LINES, len(self.axes_indices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glUseProgram(0)

    def adjust_color_brightness(self, color, factor):
        new_color = [min(max(component + factor, 0), 1) for component in color]
        return new_color

    def _set_clipping_uniforms(self, gguip: GuiParametersGlobal):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        glUniform1f(self.ulocs_grid["clip_x"], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.ulocs_grid["clip_y"], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.ulocs_grid["clip_z"], (zdom * gguip.clip_dist[2]))

    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]
