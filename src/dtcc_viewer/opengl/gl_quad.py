import math
import numpy as np
import pyrr
from pprint import pp
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.parameters import GuiParametersGlobal

from dtcc_viewer.shaders.shaders_base_quad import (
    vertex_shader_base_quad,
    fragment_shader_base_quad,
)


class GlQuad:
    """OpenGL quad for debugging purposes. Not used yet."""

    size: float
    vertices: np.ndarray
    indices: np.ndarray
    shader: int
    uni_locs: dict

    VAO: int  # OpenGL Vertex attribut object for debug quad
    VBO: int  # OpenGL Vertex buffer object for debug quad
    EBO: int  # OpenGL Element buffer object for debug quad

    def __init__(self, size):

        self.size = size
        self.uni_locs = {}
        self.vertices = self._get_vertices(size, 0.0)
        self.indices = self._get_indices()

        self._create_debug_quad()
        self._create_shader()

    def _create_debug_quad(self) -> None:

        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.indices = np.array(self.indices, dtype=np.uint32)

        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        size = len(self.vertices) * 4  # Size in bytes
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.indices) * 4  # Size in bytes
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.indices, GL_STATIC_DRAW)

        # Position (x, y, z)
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        # Texture coordinates (x, y)
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))

    def _create_shader(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader = compileProgram(
            compileShader(vertex_shader_base_quad, GL_VERTEX_SHADER),
            compileShader(fragment_shader_base_quad, GL_FRAGMENT_SHADER),
        )

        self.uni_locs["model"] = glGetUniformLocation(self.shader, "model")
        self.uni_locs["view"] = glGetUniformLocation(self.shader, "view")
        self.uni_locs["project"] = glGetUniformLocation(self.shader, "project")

    def _get_vertices(self, size, z) -> None:
        tex_min = 0
        tex_max = 1

        quad_vertices = [
            -size / 2.0,
            -size / 2.0,
            z,
            tex_min,
            tex_min,
            size / 2.0,
            -size / 2.0,
            z,
            tex_max,
            tex_min,
            -size / 2.0,
            size / 2.0,
            z,
            tex_min,
            tex_max,
            size / 2.0,
            -size / 2.0,
            z,
            tex_max,
            tex_min,
            -size / 2.0,
            size / 2.0,
            z,
            tex_min,
            tex_max,
            size / 2.0,
            size / 2.0,
            z,
            tex_max,
            tex_max,
        ]
        return quad_vertices

    def _get_indices(self) -> None:

        quad_indices = [
            0,
            1,
            2,
            3,
            4,
            5,
        ]
        return quad_indices

    def render(self, action: Action, gguip: GuiParametersGlobal) -> None:

        move = action.camera.get_move_matrix()
        proj = action.camera.get_projection_matrix(gguip)
        view = action.camera.get_view_matrix(gguip)

        glUseProgram(self.shader)

        glUniformMatrix4fv(self.uni_locs["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uni_locs["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uni_locs["project"], 1, GL_FALSE, proj)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
