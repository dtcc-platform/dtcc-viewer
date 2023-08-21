import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.shaders_point_cloud import (
    vertex_shader_pc,
    fragment_shader_pc,
)
from dtcc_viewer.opengl_viewer.gui import GuiParametersPC


class PointCloudGL:
    vertices: np.ndarray  # Vertices for one single instance of the particle mesh geometry
    face_indices: np.ndarray  # Face indices for one singel instance of particle mesh geometry
    guip: GuiParametersPC

    # Settings for calc of particle mesh resolution
    low_count = 1000000  # Upp to 1M particles -> highest resolution
    upper_count = 20000000  # More then 20M particles -> lowest resolution
    low_sides = 5  # Edge count for lowest resolution for discs
    upper_sides = 15  # Edge count for highest resolution for discs

    def __init__(
        self, name: str, disc_size: float, points: np.ndarray, colors: np.ndarray
    ):
        self.guip = GuiParametersPC(name)
        n_points = len(points) / 3
        self._create_single_instance(disc_size, n_points)
        self._create_multiple_instances(points, colors)
        self._create_shader()

    def render(self, interaction: Interaction):
        self._bind_vao()
        self._bind_shader()

        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.project_loc, 1, GL_FALSE, proj)

        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, view)

        tans = self._get_billborad_transform(
            interaction.camera.camera_pos, interaction.camera.camera_target
        )
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, tans)

        color_by = int(self.guip.color_pc)
        glUniform1i(self.color_by_loc, color_by)

        scale_factor = self.guip.pc_scale
        scale = pyrr.matrix44.create_from_scale(
            [scale_factor, scale_factor, scale_factor], dtype=np.float32
        )
        glUniformMatrix4fv(self.scale_loc, 1, GL_FALSE, scale)

        glDrawElementsInstanced(
            GL_TRIANGLES,
            len(self.face_indices),
            GL_UNSIGNED_INT,
            None,
            self.n_instances,
        )

        self._unbind_vao()
        self._unbind_shader()

    def _create_single_instance(self, disc_size: float, n_points: int):
        # Get vertices and face indices for one instance. The geometry resolution is related to number of particles.
        [self.vertices, self.face_indices] = self._get_instance_geometry(
            disc_size, n_points
        )

        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.face_indices = np.array(self.face_indices, dtype=np.uint32)

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(
            GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW
        )  # Second argument is nr of bytes

        # Element buffer
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            len(self.face_indices) * 4,
            self.face_indices,
            GL_STATIC_DRAW,
        )

        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def _create_multiple_instances(self, points: np.ndarray, colors: np.ndarray):
        self.n_instances = int(points.size / 3.0)
        self.instance_transforms = points

        print("Number of instances created: " + str(self.n_instances))

        self.transforms_VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.transforms_VBO)
        glBufferData(
            GL_ARRAY_BUFFER,
            self.instance_transforms.nbytes,
            self.instance_transforms,
            GL_STATIC_DRAW,
        )

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(
            2, 1
        )  # 2 is layout location, 1 means every instance will have it's own attribute (translation in this case).

        self.color_VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_VBO)
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)

        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(
            3, 1
        )  # 3 is layout location, 1 means every instance will have it's own attribute (color in this case).

    def _bind_vao(self):
        glBindVertexArray(self.VAO)

    def _unbind_vao(self):
        glBindVertexArray(0)

    def _create_shader(self):
        self.shader = compileProgram(
            compileShader(vertex_shader_pc, GL_VERTEX_SHADER),
            compileShader(fragment_shader_pc, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.shader)

        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.project_loc = glGetUniformLocation(self.shader, "project")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.color_by_loc = glGetUniformLocation(self.shader, "color_by")
        self.scale_loc = glGetUniformLocation(self.shader, "scale")

    def _bind_shader(self):
        glUseProgram(self.shader)

    def _unbind_shader(self):
        glUseProgram(0)

    def _get_billborad_transform(self, camera_position, camera_target):
        dir_from_camera = camera_target - camera_position
        angle1 = np.arctan2(-dir_from_camera[1], dir_from_camera[0])  # arctan(dy/dx)
        dist2d = math.sqrt(
            dir_from_camera[0] ** 2 + dir_from_camera[1] ** 2
        )  # sqrt(dx^2 + dy^2)
        angle2 = np.arctan2(dir_from_camera[2], dist2d)  # angle around vertical axis

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        model_transform = pyrr.matrix44.multiply(
            model_transform,
            pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32),
        )
        model_transform = pyrr.matrix44.multiply(
            model_transform,
            pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32),
        )

        return model_transform

    def _create_circular_disc(self, radius, n):
        center = [0.0, 0.0, 0.0]
        center_color = [1.0, 1.0, 1.0]  # White
        edge_color = [0.5, 0.5, 0.5]  # Magenta
        angle_between_points = 2 * math.pi / n
        vertices = []
        vertices.extend(center)
        vertices.extend(center_color)
        face_indices = []
        # Iterate over each angle and calculate the corresponding point on the circle
        for i in range(n):
            angle = i * angle_between_points
            x = center[0]
            y = center[1] + radius * math.cos(angle)
            z = center[2] + radius * math.sin(angle)
            vertices.extend([x, y, z])
            vertices.extend(edge_color)
            if i > 0 and i < n:
                face_indices.extend([0, i + 1, i])
            if i == n - 1:
                face_indices.extend([0, 1, i + 1])

        return vertices, face_indices

    def _create_quad(self, radius):
        color = [1.0, 1.0, 1.0]  # White
        dy = radius / 2.0
        dz = dy

        vertices = []
        vertices.extend([0, -dy, -dz])
        vertices.extend(color)
        vertices.extend([0, -dy, dz])
        vertices.extend(color)
        vertices.extend([0, dy, dz])
        vertices.extend(color)
        vertices.extend([0, dy, -dz])
        vertices.extend(color)

        face_indices = []
        face_indices.extend([0, 1, 2])
        face_indices.extend([2, 3, 0])

        return vertices, face_indices

    def _get_instance_geometry(self, disc_size: float, n_points: int):
        n_sides = self._calc_n_sides(n_points)

        if n_points > self.upper_count:
            [self.vertices, self.face_indices] = self._create_quad(
                disc_size
            )  # Lowest resolution, only 2 triangles
        else:
            n_sides = self._calc_n_sides(n_points)
            [self.vertices, self.face_indices] = self._create_circular_disc(
                disc_size, n_sides
            )  # Higher res discs

        return self.vertices, self.face_indices

    def _calc_n_sides(self, n_points: int):
        count_diff = self.upper_count - self.low_count
        sides_diff = self.upper_sides - self.low_sides

        if n_points < self.low_count:
            n_sides = self.upper_sides
        elif n_points > self.upper_count:
            n_sides = self.low_sides
        else:
            n_sides = self.low_sides + sides_diff * (
                1 - ((n_points - self.low_count) / count_diff)
            )
            n_sides = round(n_sides, 0)

        return int(n_sides)
