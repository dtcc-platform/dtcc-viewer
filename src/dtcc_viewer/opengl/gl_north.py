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
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.shaders.shaders_axes import vertex_shader_axes, fragment_shader_axes


class GlNorth:
    """A class for rendering north arrow for the OpenGL scene.

    This class handles the setup and rendering of a north arrow in an OpenGL scene.
    It provides methods to create the arrow geometry, compile shaders, and render.

    Attributes
    ----------
    bb_local : BoundingBox
        The local bounding box of the scene.
    bb_global : BoundingBox
        The global bounding box of the scene.
    ulocs_axes : dict
        Uniform locations for the shader program.
    shader_axes : int
        Shader program.
    VAO : int
        Vertex array object.
    VBO : int
        Vertex buffer object.
    EBO : int
        Element buffer object.
    vertices : np.ndarray
        All vertices in the mesh.
    indices : np.ndarray
        Mesh faces.
    size : np.ndarray
        Sizes for the grid lines.
    """

    bb_local: BoundingBox
    bb_global: BoundingBox
    ulocs_axes: dict  # Uniform locations for the shader program
    shader_axes: int  # Shader program

    VAO: int  # Vertex array object
    VBO: int  # Vertex buffer object
    EBO: int  # Element buffer object

    vertices = np.ndarray  # All vertices in mesh
    indices = np.ndarray  # Mesh faces

    size: np.ndarray  # Size

    def __init__(self, size: float, zpos: float):
        """Initialize the GlAxes object with size and z-position.

        Parameters
        ----------
        size : float
            The size of the axes.
        zpos : float
            The z-position of the axes.
        """
        self.ulocs = {}
        self.size = size

        h = 1.0 * size
        r = 0.02 * size
        n = 20

        model_vector = pyrr.Vector3([0.0, 0.0, zpos])
        self.model_matrix = pyrr.matrix44.create_from_translation(model_vector)

        self._create_mesh(h, r, n)
        self._create_vao()
        self._create_shader()

    def _create_mesh(self, h: float, r: float, n: int) -> None:
        """Create the mesh for the axes arrows. The x-arrow is red, y-arrow is green,
        and z-arrow is blue.

        Parameters
        ----------
        h : float
            The height of the axes.
        r : float
            The radius of the axes.
        n : int
            The number of segments for the cylinders and cones.
        """

        compass_size = 1.0

        compass_mesh = create_compass(compass_size)
        compass_color = np.array([0.8, 0.8, 0.8])
        compass_color = np.tile(compass_color, (len(compass_mesh.vertices), 1))

        # Color every second triangle darker
        color_dark = np.array([0.0, 0.0, 0.0])
        compass_color[0::6, :] = color_dark
        compass_color[1::6, :] = color_dark
        compass_color[2::6, :] = color_dark

        letters_mesh = create_compass_letters(size=0.2, distance=(compass_size * 1.3))
        letters_color = color_dark
        letters_color = np.tile(letters_color, (len(letters_mesh.vertices), 1))

        # Combine meshes
        mesh = concatenate_meshes([compass_mesh, letters_mesh])
        colors = np.vstack((compass_color, letters_color))

        # vertices = [x, y, z, r, g, b, x, y, z...]
        vertices = np.zeros((len(mesh.vertices), 6))
        vertices[:, 0:3] = mesh.vertices
        vertices[:, 3:6] = colors

        self.vertices = np.array(vertices, dtype="float32").flatten()
        self.indices = np.array(mesh.faces, dtype="uint32").flatten()

    def _create_vao(self) -> None:
        """Set up vertex and element buffers for line rendering."""

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        size = len(self.vertices) * 4
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.indices) * 4
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Colors
        glEnableVertexAttribArray(1)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)

    def _create_shader(self) -> None:
        """Create and compile the shader program."""

        glBindVertexArray(self.VAO)
        self.shader = compileProgram(
            compileShader(vertex_shader_axes, GL_VERTEX_SHADER),
            compileShader(fragment_shader_axes, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader)

        self.ulocs["model"] = glGetUniformLocation(self.shader, "model")
        self.ulocs["view"] = glGetUniformLocation(self.shader, "view")
        self.ulocs["project"] = glGetUniformLocation(self.shader, "project")
        self.ulocs["scale"] = glGetUniformLocation(self.shader, "scale")

    def _update_size(self, action: Action) -> None:
        """Update north arrow scale based on zoom level."""
        action.gguip.north_sf = 0.05 * action.camera.distance_to_target

    def render(self, action: Action) -> None:
        """Render the axes if the corresponding GUI parameter is set."""
        if action.gguip.show_north:
            self._update_size(action)
            self._render(action)

    def _render(self, action: Action) -> None:
        """Render the axes."""

        glBindVertexArray(self.VAO)
        glUseProgram(self.shader)

        # MVP Calculations
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.ulocs["model"], 1, GL_FALSE, self.model_matrix)
        glUniformMatrix4fv(self.ulocs["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.ulocs["project"], 1, GL_FALSE, proj)
        glUniform1f(self.ulocs["scale"], action.gguip.north_sf)

        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glUseProgram(0)
