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
    """A class for rendering a grid and coordinate axes for the OpenGL scene.

    This class handles the setup and rendering of a grid and coordinate axes in an
    OpenGL scene. It provides methods to create the grid geometry, compile shaders, and
    render the grid with adjustable size and spacing.

    Attributes
    ----------
    bb_global : BoundingBox
        The global bounding box of the scene.
    ulocs_grid : dict
        Uniform locations for the shader program.
    shader_grid : int
        Shader program.
    VAO_grid : int
        Vertex array object.
    VBO_grid : int
        Vertex buffer object.
    EBO_grid : int
        Element buffer object.
    nx : int
        Number of grid lines in the x direction.
    ny : int
        Number of grid lines in the y direction.
    grid_coords : np.ndarray
        Coordinates for the grid lines.
    grid_indices : np.ndarray
        Indices for the grid lines.
    size : np.ndarray
        Grid sizes for the grid lines.
    grid_spaces : np.ndarray
        Grid spacings for the grid lines.
    """

    bb_global: BoundingBox
    ulocs_grid: dict  # Uniform locations for the shader program
    shader_grid: int  # Shader program

    VAO_grid: int  # Vertex array object
    VBO_grid: int  # Vertex buffer object
    EBO_grid: int  # Element buffer object

    nx: int  # Number of grid lines
    ny: int  # Number of grid lines

    grid_coords: np.ndarray  # Coordinates for the grid lines
    grid_indices: np.ndarray  # Indices for the grid lines

    size: np.ndarray  # Grid sizes for the grid lines
    grid_spaces: np.ndarray  # Grid spacings for the grid lines

    def __init__(self, bb_global: BoundingBox):

        self.bb_global = bb_global
        self.ulocs_grid = {}
        self.grid_spaces = np.array(
            [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
        )

        self.size = 2.0 * np.max([bb_global.xdom, bb_global.ydom])

        info(f"Grid size: {self.size}")
        grid_size = (self.size, self.size)
        grid_spacing = (1, 1)
        self._create_grid(grid_size, grid_spacing, bb_global.zmin)
        self._create_vao()
        self._create_shader()

    def _update_size(self, action: Action) -> None:

        if action.gguip.grid_adapt:
            dtt = action.camera.distance_to_target
            dtt_min = 10
            dtt_max = 100000
            normalized_dtt = (dtt - dtt_min) / (dtt_max - dtt_min)

            spc_min = np.min(self.grid_spaces)
            spc_max = np.max(self.grid_spaces)
            spc = spc_min + normalized_dtt * (spc_max - spc_min)
            spc = self.find_nearest(self.grid_spaces, spc)

            action.gguip.grid_sf = spc

    def _create_grid(self, size: tuple, spacing: tuple, zpos: float) -> None:
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

        zcoord = zpos * np.ones((n_gridlines_x * 2 + n_gridlines_y * 2))
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

    def _create_vao(self) -> None:
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

    def _create_shader(self) -> None:
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
        self.ulocs_grid["clip_xy"] = glGetUniformLocation(self.shader_grid, "clip_xy")

        self.ulocs_grid["fog_start"] = glGetUniformLocation(
            self.shader_grid, "fog_start"
        )
        self.ulocs_grid["fog_end"] = glGetUniformLocation(self.shader_grid, "fog_end")
        self.ulocs_grid["fog_color"] = glGetUniformLocation(
            self.shader_grid, "fog_color"
        )

        glUniform1f(self.ulocs_grid["fog_start"], self.size * 0.4)
        glUniform1f(self.ulocs_grid["fog_end"], self.size * 0.8)

    def render(self, action: Action) -> None:
        if action.gguip.show_grid:
            self._update_size(action)
            self._render_grid(action)

    def _render_grid(self, action: Action) -> None:

        glBindVertexArray(self.VAO_grid)
        glUseProgram(self.shader_grid)

        # MVP Calculations
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.ulocs_grid["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.ulocs_grid["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ulocs_grid["project"], 1, GL_FALSE, proj)

        bc = action.gguip.color
        c = self.adjust_color_brightness(bc, 0.25)
        glUniform3f(self.ulocs_grid["color"], c[0], c[1], c[2])
        glUniform1f(self.ulocs_grid["scale"], action.gguip.grid_sf)
        glUniform1f(self.ulocs_grid["clip_xy"], self.size)
        glUniform3f(self.ulocs_grid["fog_color"], bc[0], bc[1], bc[2])

        glDrawElements(GL_LINES, len(self.grid_indices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glUseProgram(0)

    def adjust_color_brightness(self, color, factor):
        new_color = [min(max(component + factor, 0), 1) for component in color]
        return new_color

    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]
