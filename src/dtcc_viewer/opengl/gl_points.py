import math
import pyrr
import numpy as np
import time
from string import Template
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.data_wrapper import MeshDataWrapper, PointsDataWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.parameters import GuiParametersPC, GuiParametersGlobal
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.gl_object import GlObject

from dtcc_viewer.shaders.shaders_color_maps import (
    color_map_rainbow,
    color_map_inferno,
    color_map_black_body,
    color_map_turbo,
    color_map_viridis,
)

from dtcc_viewer.shaders.shaders_points import (
    vertex_shader_pc,
    fragment_shader_pc,
)


class GlPoints(GlObject):
    """A class for rendering point cloud data using OpenGL.

    This class handles the rendering of point cloud data using OpenGL.
    It provides methods to set up the rendering environment, bind shaders,
    and perform the necessary transformations for visualization.

    Each particle is represented by a circular mesh disc with a number of sides given
    by the particle count to ensure good performance and visual quality. The particles
    rendered using instanced rendering to improve performance. Each mesh disc is also
    transformed to face the camera using billboarding. The color of the mesh disc is
    brighter in the center and darker at the edge to give a 3D effect which makes the
    particles look like spheres but with much fewer triangles.

    Attributes
    ----------
    vertices : np.ndarray
        Vertices for one single instance of the particle mesh geometry.
    face_indices : np.ndarray
        Face indices for one single instance of the particle mesh geometry.
    guip : GuiParametersPC
        GuiParametersPC object for managing GUI parameters.
    name : str
        Name of the point cloud.
    low_count : int
        Upper limit for particle count to determine highest resolution.
    upper_count : int
        Lower limit for particle count to determine lowest resolution.
    low_sides : int
        Edge count for lowest resolution for discs.
    upper_sides : int
        Edge count for highest resolution for discs.
    bb_local : BoundingBox
        Local bounding box for the point cloud.
    bb_global : BoundingBox
        Global bounding box for the entire scene.
    uniform_locs : dict
        Uniform locations for the shader program.
    shader : int
        Shader program.
    p_size : float
        Particle size.
    n_points : int
        Number of particles in point cloud.
    n_sides : int
        Number of sides for the particle mesh instance geometry.
    """

    vertices: np.ndarray  # Vertices for single instance of the particle mesh geometry
    face_indices: np.ndarray  # Indices for singel instance of particle mesh geometry
    guip: GuiParametersPC  # GuiParametersPC object for managing GUI parameters
    name: str  # Name of the point cloud

    # Settings for calc of particle mesh resolution
    low_count = 1000000  # Upp to 1M particles -> highest resolution
    upper_count = 20000000  # More then 20M particles -> lowest resolution
    low_sides = 5  # Edge count for lowest resolution for discs
    upper_sides = 15  # Edge count for highest resolution for discs
    bb_local: BoundingBox
    bb_global: BoundingBox

    uniform_locs = {}  # Uniform locations for the shader program
    shader: int  # Shader program

    p_size: float  # Particle size
    n_points: int  # Number of particles in point cloud
    n_sides: int  # Number of sides for the particle mesh instance geometry

    def __init__(self, pc_wrapper: PointCloudWrapper):
        """Initialize the PointCloudGL object and set up rendering."""

        self.p_size = pc_wrapper.size
        self.n_points = len(pc_wrapper.points) // 3
        self.transforms = pc_wrapper.points
        self.name = pc_wrapper.name
        self.data_wrapper = pc_wrapper.data_wrapper

        self.texels = np.zeros((self.n_points, 2), dtype="float32")
        self.texels[:, 0] = self.data_wrapper.texel_x
        self.texels[:, 1] = self.data_wrapper.texel_y
        self.texels = np.array(self.texels, dtype="float32")

        self.uniform_locs = {}

        data_mat_dict = self.data_wrapper.data_mat_dict
        data_min_max = self.data_wrapper.data_min_max
        self.guip = GuiParametersPC(pc_wrapper.name, data_mat_dict, data_min_max)
        self.bb_local = pc_wrapper.bb_local
        self.bb_global = pc_wrapper.bb_global

    def render(self, action: Action) -> None:
        """Render the point cloud using provided interaction parameters."""

        self._bind_vao()
        self._bind_shader()
        self._bind_data_texture()

        proj = action.camera.get_projection_matrix(action.gguip)
        glUniformMatrix4fv(self.uniform_locs["project"], 1, GL_FALSE, proj)

        view = action.camera.get_view_matrix(action.gguip)
        glUniformMatrix4fv(self.uniform_locs["view"], 1, GL_FALSE, view)

        cam_position = action.camera.position
        cam_target = action.camera.target
        model = self._get_billboard_transform(cam_position, cam_target)
        glUniformMatrix4fv(self.uniform_locs["model"], 1, GL_FALSE, model)

        self._set_clipping_uniforms(action.gguip)

        glUniform1i(self.uniform_locs["color_by"], int(self.guip.color))
        glUniform1i(self.uniform_locs["color_inv"], int(self.guip.invert_cmap))
        glUniform1i(self.uniform_locs["cmap_idx"], self.guip.cmap_idx)
        glUniform1f(self.uniform_locs["data_min"], self.guip.data_min)
        glUniform1f(self.uniform_locs["data_max"], self.guip.data_max)
        glUniform1i(self.uniform_locs["data_tex"], self.texture_idx)

        sf = self.guip.point_scale
        scale = pyrr.matrix44.create_from_scale([sf, sf, sf], dtype=np.float32)
        glUniformMatrix4fv(self.uniform_locs["scale"], 1, GL_FALSE, scale)

        f_count = len(self.face_indices)
        p_count = self.n_points
        glDrawElementsInstanced(GL_TRIANGLES, f_count, GL_UNSIGNED_INT, None, p_count)

        self._unbind_vao()
        self._unbind_shader()
        self._unbind_data_texture()

    def _create_textures(self) -> None:
        """Create textures for data."""
        self._create_data_texture()

    def _create_geometry(self) -> None:
        """Create the geometry for the point cloud."""
        self._create_single_instance()
        self._create_multiple_instances()

    def _create_single_instance(self):
        """Create a single instance of particle mesh geometry."""

        # Get vertices and face indices for one instance. The geometry resolution is related to number of particles.
        self.n_sides = self._get_instance_geometry()

        # Vertex structure is [x, y, z, r, g, b...]
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.face_indices = np.array(self.face_indices, dtype=np.uint32)

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        self.VBO = glGenBuffers(1)
        size = len(self.vertices) * 4  # Size is nr of bytes
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, size, self.vertices, GL_STATIC_DRAW)

        # Element buffer
        self.EBO = glGenBuffers(1)
        size = len(self.face_indices) * 4
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.face_indices, GL_STATIC_DRAW)

        # Position for single instance around origin
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Color for single instance white in the center and greay at the edge
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def _create_multiple_instances(self):
        """Create multiple instances of a particle mesh geometry."""

        self.transforms_VBO = glGenBuffers(1)
        size = self.transforms.nbytes
        glBindBuffer(GL_ARRAY_BUFFER, self.transforms_VBO)
        glBufferData(GL_ARRAY_BUFFER, size, self.transforms, GL_STATIC_DRAW)

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        # 2 is layout location, 1 means every instance will have it's own attribute
        # a translation in this case.
        glVertexAttribDivisor(2, 1)

        self.texel_VBO = glGenBuffers(1)
        size = self.texels.nbytes
        glBindBuffer(GL_ARRAY_BUFFER, self.texel_VBO)
        glBufferData(GL_ARRAY_BUFFER, size, self.texels, GL_STATIC_DRAW)

        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

        # 3 is layout location, 1 means every instance will have it's own attribute
        # two texel incices in this case.
        glVertexAttribDivisor(3, 1)

    def _bind_vao(self) -> None:
        """Bind the Vertex Array Object (VAO)."""
        glBindVertexArray(self.VAO)

    def _unbind_vao(self) -> None:
        """Unbind the Vertex Array Object (VAO)."""
        glBindVertexArray(0)

    def _create_shaders(self) -> None:
        """Create and compile the shader program."""

        vertex_shader = vertex_shader_pc
        fragment_shader = fragment_shader_pc

        # Insert function for color map calculations
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
        self.uniform_locs["scale"] = glGetUniformLocation(self.shader, "scale")
        self.uniform_locs["clip_x"] = glGetUniformLocation(self.shader, "clip_x")
        self.uniform_locs["clip_y"] = glGetUniformLocation(self.shader, "clip_y")
        self.uniform_locs["clip_z"] = glGetUniformLocation(self.shader, "clip_z")
        self.uniform_locs["cmap_idx"] = glGetUniformLocation(self.shader, "cmap_idx")
        self.uniform_locs["data_min"] = glGetUniformLocation(self.shader, "data_min")
        self.uniform_locs["data_max"] = glGetUniformLocation(self.shader, "data_max")
        self.uniform_locs["color_inv"] = glGetUniformLocation(self.shader, "color_inv")
        self.uniform_locs["data_tex"] = glGetUniformLocation(self.shader, "data_tex")

    def _bind_shader(self) -> None:
        """Bind the shader program."""
        glUseProgram(self.shader)

    def _unbind_shader(self) -> None:
        """Unbind the shader program."""
        glUseProgram(0)

    def _get_billboard_transform(self, camera_position, camera_target):
        """Calculate the transformation matrix for billboarding.

        Parameters
        ----------
        camera_position : np.ndarray
            The position of the camera.
        camera_target : np.ndarray
            The target point that the camera is looking at.

        Returns
        -------
        np.ndarray
            The transformation matrix for billboarding.
        """
        dir_from_camera = camera_target - camera_position

        # Angle1: arctan(dy/dx)
        angle1 = np.arctan2(-dir_from_camera[1], dir_from_camera[0])

        # Dist 2d: sqrt(dx^2 + dy^2)
        dist2d = math.sqrt(dir_from_camera[0] ** 2 + dir_from_camera[1] ** 2)

        # Angle2: around vertical axis
        angle2 = np.arctan2(dir_from_camera[2], dist2d)

        # Create transformation matrices for each mode
        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        rotation_y = pyrr.matrix44.create_from_y_rotation(angle2, np.float32)
        rotation_z = pyrr.matrix44.create_from_z_rotation(angle1, np.float32)

        # Combine the the transformations
        model_transform = pyrr.matrix44.multiply(model_transform, rotation_y)
        model_transform = pyrr.matrix44.multiply(model_transform, rotation_z)

        return model_transform

    def _create_circular_disc(self, n_sides: int):
        """Create vertices and face indices for a circular disc.

        Parameters
        ----------
        radius : float
            The radius of the circular disc.
        n_sides : int
            The number of sides of the disc.

        Returns
        -------
        Tuple[List[float], List[int]]
            A tuple containing lists of vertices and face indices.
        """
        center = np.array([0.0, 0.0, 0.0], dtype=float)
        center_color = [1.0, 1.0, 1.0]  # White
        edge_color = [0.5, 0.5, 0.5]  # Grey
        angle_between_points = 2 * math.pi / n_sides
        vertices = []
        vertices.extend(center)
        vertices.extend(center_color)
        face_indices = []
        # Iterate over each angle and calculate the corresponding point on the circle
        for i in range(n_sides):
            angle = i * angle_between_points
            x = center[0]
            y = center[1] + self.p_size * math.cos(angle)
            z = center[2] + self.p_size * math.sin(angle)
            vertices.extend([x, y, z])
            vertices.extend(edge_color)
            if i > 0 and i < n_sides:
                face_indices.extend([0, i + 1, i])
            if i == n_sides - 1:
                face_indices.extend([0, 1, i + 1])

        return vertices, face_indices

    def _create_quad(self):
        """Create vertices and face indices for a quad.

        Parameters
        ----------
        radius : float
            The radius of the quad.

        Returns
        -------
        Tuple[List[float], List[int]]
            A tuple containing lists of vertices and face indices.
        """
        color = [1.0, 1.0, 1.0]  # White
        dy = self.p_size / 2.0
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

    def _get_instance_geometry(self):
        """Get vertices and face indices for a single instance of particle mesh geometry.

        Returns
        -------
        Tuple[List[float], List[int]]
            A tuple containing lists of vertices and face indices.
        """
        n_sides = self._calc_n_sides()

        if self.n_points > self.upper_count:
            # Lowest resolution, only 2 triangles
            [self.vertices, self.face_indices] = self._create_quad()
        else:
            # Higher res discs
            n_sides = self._calc_n_sides()
            [self.vertices, self.face_indices] = self._create_circular_disc(n_sides)

        return n_sides

    def _calc_n_sides(self):
        """Calculate the number of sides for particle mesh geometry.

        Returns
        -------
        int
            The calculated number of sides for particle mesh geometry.
        """
        count_diff = self.upper_count - self.low_count
        sides_diff = self.upper_sides - self.low_sides

        if self.n_points < self.low_count:
            n_sides = self.upper_sides
        elif self.n_points > self.upper_count:
            n_sides = self.low_sides
        else:
            n_sides = self.low_sides + sides_diff * (
                1 - ((self.n_points - self.low_count) / count_diff)
            )
            n_sides = round(n_sides, 0)

        return int(n_sides)

    def _set_clipping_uniforms(self, gguip: GuiParametersGlobal):
        xdom = 0.5 * np.max([self.bb_local.xdom, self.bb_global.xdom])
        ydom = 0.5 * np.max([self.bb_local.ydom, self.bb_global.ydom])
        zdom = 0.5 * np.max([self.bb_local.zdom, self.bb_global.zdom])

        glUniform1f(self.uniform_locs["clip_x"], (xdom * gguip.clip_dist[0]))
        glUniform1f(self.uniform_locs["clip_y"], (ydom * gguip.clip_dist[1]))
        glUniform1f(self.uniform_locs["clip_z"], (zdom * gguip.clip_dist[2]))
