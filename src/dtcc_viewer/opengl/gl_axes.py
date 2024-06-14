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


class GlAxes:
    """A class for rendering coordinate axes for the OpenGL scene.

    This class handles the setup and rendering of coordinate axes in an OpenGL scene.
    It provides methods to create the axis geometry, compile shaders, and render.

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

    size: np.ndarray  # Grid sizes for the grid lines

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

        x_axis = create_cylinder_mesh(Point(0, 0, 0), Direction.x, r, h, n)
        x_cone = create_cone_mesh(Point(h, 0, 0), Direction.x, r * 2.5, r * 5, n)
        x = concatenate_meshes([x_axis, x_cone])
        x_color = np.array([1.0, 0.0, 0.0])
        x_color = np.tile(x_color, (len(x.vertices), 1))
        x_color = np.reshape(x_color, (-1, 3))

        y_axis = create_cylinder_mesh(Point(0, 0, 0), Direction.y, r, h, n)
        y_cone = create_cone_mesh(Point(0, h, 0), Direction.y, r * 2.5, r * 5, n)
        y = concatenate_meshes([y_axis, y_cone])
        y_color = np.array([0.0, 1.0, 0.0])
        y_color = np.tile(y_color, (len(y.vertices), 1))
        y_color = np.reshape(y_color, (-1, 3))

        z_axis = create_cylinder_mesh(Point(0, 0, 0), Direction.z, r, h, n)
        z_cone = create_cone_mesh(Point(0, 0, h), Direction.z, r * 2.5, r * 5, n)
        z = concatenate_meshes([z_axis, z_cone])
        z_color = np.array([0.0, 0.0, 1.0])
        z_color = np.tile(z_color, (len(z.vertices), 1))
        z_color = np.reshape(z_color, (-1, 3))

        origo = create_sphere_mesh(Point(0, 0, 0), r * 2.5, n, n)
        o_color = np.array([0.0, 0.0, 0.0])
        o_color = np.tile(o_color, (len(origo.vertices), 1))
        o_color = np.reshape(o_color, (-1, 3))

        all_meshes = [x, y, z, origo]

        n1 = len(x.vertices)
        n2 = len(x.vertices) + len(y.vertices)
        n3 = len(x.vertices) + len(y.vertices) + len(z.vertices)
        n4 = len(x.vertices) + len(y.vertices) + len(z.vertices) + len(origo.vertices)

        mesh = concatenate_meshes(all_meshes)

        # vertices = [x, y, z, r, g, b, x, y, z...]
        vertices = np.zeros((n4, 6))
        vertices[:, 0:3] = mesh.vertices
        vertices[0:n1, 3:6] = x_color
        vertices[n1:n2, 3:6] = y_color
        vertices[n2:n3, 3:6] = z_color
        vertices[n3:n4, 3:6] = o_color

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
        """Update axes scale based on zoom level."""
        action.gguip.axes_sf = 0.05 * action.camera.distance_to_target

    def render(self, action: Action) -> None:
        """Render the axes if the corresponding GUI parameter is set."""
        if action.gguip.show_axes:
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
        glUniform1f(self.ulocs["scale"], action.gguip.axes_sf)

        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glUseProgram(0)
