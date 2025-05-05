import numpy as np
import math
from enum import IntEnum
from dtcc_core.model import Mesh, PointCloud
from pprint import pp
from dtcc_viewer.logging import info, warning
from dtcc_core.model import (
    MultiSurface,
    Surface,
    VolumeMesh,
    LineString,
    MultiLineString,
)
from shapely.geometry import Point
from shapely.geometry import LineString as ShapelyLineString
from dtcc_viewer.utils import Direction
from typing import Optional


class Shading(IntEnum):
    WIREFRAME = 0
    AMBIENT = 1
    DIFFUSE = 2
    WIRESHADED = 3
    SHADOWS_STATIC = 4
    SHADOWS_DYNAMIC = 5
    PICKING = 6


class ColorMaps(IntEnum):
    TURBO = 0
    INFERNO = 1
    BLACKBODY = 2
    RAINBOW = 3
    VIRIDIS = 4


class Results(IntEnum):
    InvalidInput = 0
    DuplicatedVertices = 1
    FailedNormal = 2
    FailedTriangulation = 3
    SingularMatrix = 4
    TriSuccess = 5
    Success = 6


class RasterType(IntEnum):
    Data = 0
    RGB = 1
    RGBA = 2


class CameraProjection(IntEnum):
    PERSPECTIVE = 0
    ORTHOGRAPHIC = 1


class CameraView(IntEnum):
    PERSPECTIVE = 0
    TOP = 1
    FRONT = 2
    BACK = 3
    LEFT = 4
    RIGHT = 5


class BoundingBox:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float

    xdom: float
    ydom: float
    zdom: float

    mid_pt: np.ndarray
    center_vec: np.ndarray
    origin: np.ndarray
    size: float

    def __init__(self, vertices: np.ndarray):
        self.calc_bounds_flat(vertices)
        self.origin = np.array([0, 0, 0])
        self.calc_mid_point()
        self.calc_center_vec()
        self.calc_size()

    def calc_bounds_flat(self, vertices: np.ndarray):
        self.xmin = vertices[0::3].min()
        self.xmax = vertices[0::3].max()
        self.ymin = vertices[1::3].min()
        self.ymax = vertices[1::3].max()
        self.zmin = vertices[2::3].min()
        self.zmax = vertices[2::3].max()

        self.xdom = self.xmax - self.xmin
        self.ydom = self.ymax - self.ymin
        self.zdom = self.zmax - self.zmin

    def calc_mid_point(self):
        x = (self.xmax + self.xmin) / 2.0
        y = (self.ymax + self.ymin) / 2.0
        z = (self.zmax + self.zmin) / 2.0
        self.mid_pt = np.array([x, y, z], dtype="float32")

    def calc_center_vec(self):
        self.center_vec = self.origin - self.mid_pt

    def move_to_zero_z(self):
        """Move the bounding box so everything is positive z."""
        self.zmax -= self.zmin
        self.zmin -= self.zmin
        self.mid_pt[2] -= self.zmin
        self.origin = np.array([0, 0, (self.zmax + self.zmin) / 2.0])
        self.calc_center_vec()

    def move_to_center(self):
        """Move the bounding box so everything is centered."""
        self.xmax -= self.mid_pt[0]
        self.xmin -= self.mid_pt[0]
        self.ymax -= self.mid_pt[1]
        self.ymin -= self.mid_pt[1]
        self.zmax -= self.mid_pt[2]
        self.zmin -= self.mid_pt[2]
        self.origin = self.mid_pt
        self.calc_center_vec()

    def calc_size(self):
        """Calculate the size of the bounding box as the length of the diagonal."""
        min_pt = np.array([self.xmin, self.ymin, self.zmin])
        max_pt = np.array([self.xmax, self.ymax, self.zmax])
        self.size = np.linalg.norm(max_pt - min_pt)

    def print(self):
        print("Bounds: ")
        print([self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax])
        print("Mid point: ")
        print(self.mid_pt)
        print("Center vector: ")
        print(self.center_vec)
        print("Domain: ")
        print([self.xdom, self.ydom, self.zdom])
        print("Size: ")
        print([self.xdom, self.ydom, self.zdom])


# ---------- load CityJSON helper functions --------#


def rodrigues_rotation_matrix(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)

    v = np.cross(a, b)
    # Catch situations where a and b are parallel
    if np.allclose(v, 0):
        return np.eye(4)

    s = np.linalg.norm(v)
    c = np.dot(a, b)

    vx = np.array(
        [
            [0, -v[2], v[1]],
            [v[2], 0, -v[0]],
            [-v[1], v[0], 0],
        ]
    )
    R = np.eye(4)
    R[:3, :3] = np.eye(3) + vx + vx @ vx * (1 / (1 + c))
    return R


def calc_translation_matrix(centroid):
    T = np.eye(4)
    T[:3, 3] = -centroid
    return T


def get_unique_vertex_pair(vertices):
    # Get the vertices from the surface
    vertex1 = vertices[0, :]

    for i in range(1, vertices.shape[0]):
        vertex2 = vertices[i, :]

        if vertex_vertex_distance(vertex1, vertex2) > 1e-5:
            break

    return vertex1, vertex2


def remove_duplicate_vertices(vertices):
    unique_vertices = []
    for i in range(vertices.shape[0]):
        new_vertex = vertices[i, :]
        if not vertex_in_list(new_vertex, unique_vertices):
            unique_vertices.append(new_vertex)

    return np.array(unique_vertices)


def vertex_in_list(vertex, vertex_list):
    for v in vertex_list:
        if vertex_vertex_distance(v, vertex) < 1e-8:
            return True

    return False


def vertex_vertex_distance(vertex1, vertex2):
    return np.linalg.norm(vertex1 - vertex2)


def get_normal_from_surface(vertices, centroid):
    vertex1, vertex2 = get_unique_vertex_pair(vertices)

    # Calculate the normal vector of the plane defined by the vertices
    vec1 = vertex1 - centroid
    vec2 = vertex2 - centroid  # Could there be duplicate vertices?

    normal_vector = np.cross(vec1, vec2)
    vec_length = np.linalg.norm(normal_vector)

    if vec_length != 0:
        normal_vector = normal_vector / vec_length
    else:
        return None

    return normal_vector


def concatenate_pcs(pcs: list[PointCloud]):
    v_count_tot = 0
    for pc in pcs:
        v_count_tot += len(pc.points)

    all_points = np.zeros((v_count_tot, 3), dtype=float)
    start_idx = 0
    for pc in pcs:
        v_count = len(pc.points)
        all_points[start_idx : start_idx + v_count, :] = pc.points
        start_idx += v_count

    pc = PointCloud(points=all_points)
    return pc


def concatenate_meshes(meshes: list[Mesh]):
    v_count_tot = 0
    f_count_tot = 0
    for mesh in meshes:
        v_count_tot += len(mesh.vertices)
        f_count_tot += len(mesh.faces)

    all_vertices = np.zeros((v_count_tot, 3), dtype=float)
    all_faces = np.zeros((f_count_tot, 3), dtype=int)

    # Accumulative face and vertex count
    acc_v_count = 0
    acc_f_count = 0

    for mesh in meshes:
        v_count = len(mesh.vertices)
        f_count = len(mesh.faces)
        vertex_offset = acc_v_count
        all_vertices[acc_v_count : acc_v_count + v_count, :] = mesh.vertices
        all_faces[acc_f_count : acc_f_count + f_count, :] = mesh.faces + vertex_offset
        acc_v_count += v_count
        acc_f_count += f_count

    mesh = Mesh(vertices=all_vertices, faces=all_faces)
    return mesh


def id_to_color(id):
    # Extracting color components
    r = (id & 0x000000FF) >> 0
    g = (id & 0x0000FF00) >> 8
    b = (id & 0x00FF0000) >> 16

    return np.array([r, g, b], dtype=np.float32)


def color_to_id(color):
    id = color[0] + color[1] * 256 + color[2] * 256 * 256
    return id


def invert_color(color):
    """Invert the color."""
    inv_color = [1 - color[0], 1 - color[1], 1 - color[2], 1]
    return inv_color


# ---------- Geometry primitives for testing --------#


def create_ls_circle(center, radius, num_segments):
    # Calculate the angle between each segment
    angle_step = 2 * math.pi / num_segments

    # Generate points around the circumference of the circle
    vertices = []
    for i in range(num_segments):
        x = center.x + radius * math.cos(i * angle_step)
        y = center.y + radius * math.sin(i * angle_step)
        z = center.z + math.sin(i * angle_step * 2) * 10.0
        vertices.append([x, y, z])

    vertices.append(vertices[0])
    vertices = np.array(vertices)
    circle_ls = LineString(vertices=vertices)
    return circle_ls


def create_cylinder(center, radius, height, num_segments):
    vertices = []

    # Calculate angle increment
    angle_increment = 2 * math.pi / num_segments

    # Generate vertices for the top circle
    for i in range(num_segments):
        x = center.x + radius * math.cos(i * angle_increment)
        y = center.y + radius * math.sin(i * angle_increment)
        z = center.z + height
        vertices.append([x, y, z])

    # Generate vertices for the bottom circle
    for i in range(num_segments):
        x = center.x + radius * math.cos(i * angle_increment)
        y = center.y + radius * math.sin(i * angle_increment)
        z = center.z
        vertices.append([x, y, z])

    # Generate the top and bottom surfaces
    top_surface = Surface(vertices=np.array(vertices[:num_segments]))
    bottom_surface = Surface(
        vertices=np.array(vertices[num_segments:][::-1])
    )  # Reverse the order for the bottom circle

    # Generate the side surfaces
    side_surfaces = []
    for i in range(num_segments):
        side_surface_vertices = [
            vertices[i],
            vertices[(i + 1) % num_segments],
            vertices[(i + 1) % num_segments + num_segments],
            vertices[i + num_segments],
        ]
        side_surface_vertices = np.flip(side_surface_vertices, axis=0)
        side_surface = Surface(vertices=np.array(side_surface_vertices))
        side_surfaces.append(side_surface)

    # Create the MultiSurface representing the cylinder
    all_surfaces = [top_surface, bottom_surface] + side_surfaces
    multisurface = MultiSurface(surfaces=all_surfaces)

    return multisurface


def create_surface_disc(center, radius, num_segments):
    vertices = []

    # Calculate angle increment
    angle_increment = 2 * math.pi / num_segments

    # Generate vertices for the top circle
    for i in range(num_segments):
        x = center.x + radius * math.cos(i * angle_increment)
        y = center.y + radius * math.sin(i * angle_increment)
        z = center.z
        vertices.append([x, y, z])

    srf = Surface(vertices=np.array(vertices))

    return srf


def create_cylinder_mesh(center, direction, radius, height, n):
    vertices = []
    indices = []
    # Calculate angle increment
    angle_increment = 2 * math.pi / n
    heights = [0, height]

    # Generate vertices for the top circle
    for h in heights:
        for i in range(n):
            if direction == Direction.x:
                x = center.x + h
                y = center.y + radius * math.cos(i * angle_increment)
                z = center.z + radius * math.sin(i * angle_increment)
            elif direction == Direction.y:
                x = center.x + radius * math.cos(i * angle_increment)
                y = center.y + h
                z = center.z + radius * math.sin(i * angle_increment)
            elif direction == Direction.z:
                x = center.x + radius * math.cos(i * angle_increment)
                y = center.y + radius * math.sin(i * angle_increment)
                z = center.z + h

            vertices.append([x, y, z])

    # Generate the top and bottom mesh faces

    for i in range(n):
        indices.append([i, (i + 1) % n, i + n])
        indices.append([i + n, (i + 1) % n + n, (i + 1) % n])

    return Mesh(vertices=np.array(vertices), faces=np.array(indices))


def create_cone_mesh(center, direction, radius, height, n):
    vertices = []
    indices = []
    # Calculate angle increment
    angle_increment = 2 * math.pi / n

    # Generate vertices for the top circle
    for i in range(n):
        if direction == Direction.x:
            x = center.x
            y = center.y + radius * math.cos(i * angle_increment)
            z = center.z + radius * math.sin(i * angle_increment)
        elif direction == Direction.y:
            x = center.x + radius * math.cos(i * angle_increment)
            y = center.y
            z = center.z + radius * math.sin(i * angle_increment)
        elif direction == Direction.z:
            x = center.x + radius * math.cos(i * angle_increment)
            y = center.y + radius * math.sin(i * angle_increment)
            z = center.z

        vertices.append([x, y, z])

    if direction == Direction.x:
        top_vertex = [center.x + height, center.y, center.z]
    elif direction == Direction.y:
        top_vertex = [center.x, center.y + height, center.z]
    elif direction == Direction.z:
        top_vertex = [center.x, center.y, center.z + height]

    vertices.append(top_vertex)
    # Generate the top and bottom mesh faces

    for i in range(n):
        indices.append([i, (i + 1) % n, n])

    return Mesh(vertices=np.array(vertices), faces=np.array(indices))


def create_sphere_mesh(center, radius, latitude_segments=20, longitude_segments=20):
    vertices = []
    faces = []

    # Generate vertices
    for lat in range(latitude_segments + 1):
        theta = lat * np.pi / latitude_segments
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)

        for lon in range(longitude_segments + 1):
            phi = lon * 2 * np.pi / longitude_segments
            sin_phi = np.sin(phi)
            cos_phi = np.cos(phi)

            x = center.x + radius * sin_theta * cos_phi
            y = center.y + radius * sin_theta * sin_phi
            z = center.z + radius * cos_theta

            vertices.append([x, y, z])

    # Generate faces
    for lat in range(latitude_segments):
        for lon in range(longitude_segments):
            first = lat * (longitude_segments + 1) + lon
            second = first + longitude_segments + 1
            faces.append([first, second, first + 1])
            faces.append([second, second + 1, first + 1])

    vertices = np.array(vertices)
    faces = np.array(faces)

    mesh = Mesh(vertices=vertices, faces=faces)

    return mesh


import numpy as np


def create_compass(size) -> Mesh:
    """
    Create a compass rose mesh with 4 arrows and 'N' letter.


    Returns
    -------
    Mesh
        A Mesh representing the compass rose.
    """

    vertices = []
    faces = []

    # --- Define points ---
    r_big = size
    r_small = 0.25 * size
    angles_big = np.deg2rad([90.0, 180.0, 270.0, 360])
    angles_small = np.deg2rad([45.0, 135.0, 225.0, 315.0])

    dir = [-1.0, 1.0]
    small_vs = []
    big_vs = []
    vertices = []
    faces = []

    idx = 0

    for j in range(2):

        origin = np.array([0, 0, dir[j] * size * 0.1])

        for i, angle in enumerate(angles_small):
            x_small = r_small * np.cos(angles_small[i])
            y_small = r_small * np.sin(angles_small[i])
            small_vs.append([x_small, y_small, 0.0])

            x_big = r_big * np.cos(angles_big[i])
            y_big = r_big * np.sin(angles_big[i])
            big_vs.append([x_big, y_big, 0.0])

        for i in range(4):
            vertices.append(origin)
            vertices.append(small_vs[i])
            vertices.append(big_vs[i])
            faces.append([idx, idx + 1, idx + 2])
            idx += 3

            vertices.append(origin)
            vertices.append(big_vs[i])
            vertices.append(small_vs[(i + 1) % 4])
            faces.append([idx, idx + 1, idx + 2])
            idx += 3

    mesh = Mesh(vertices=np.array(vertices), faces=np.array(faces))
    return mesh


def double_sine_wave_surface(x_range, y_range, n_x, n_y, freq_x, freq_y):
    x = np.linspace(x_range[0], x_range[1], n_x)
    y = np.linspace(y_range[0], y_range[1], n_y)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(freq_x * X) + np.sin(freq_y * Y)
    return X, Y, Z


def create_cylinder_2(p, w, radius, height, num_segments=20):

    w = w / np.linalg.norm(w)

    # (0, c, -b)
    u = np.array([0, w[2], -w[1]])
    u = u / np.linalg.norm(u)

    # (-c, 0, a)
    v = np.array([-w[2], 0, w[0]])
    v = v / np.linalg.norm(v)

    # (b, -a, 0)
    # v = np.array([-w[2], 0, w[0]])


def create_tetrahedral_cube_mesh(nx, ny, nz, length=1.0):
    # Calculate the step size
    dx = length / nx
    dy = length / ny
    dz = length / nz

    # Create an array to store the vertices
    vertices = []

    # Create vertices
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                x = i * dx
                y = j * dy
                z = k * dz
                vertices.append([x, y, z])

    vertices = np.array(vertices)

    # Create an array to store the cells (tetrahedra)
    cells = []

    # Create cells
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # Define the indices of the vertices for the current cell
                v0 = i + j * (nx + 1) + k * (nx + 1) * (ny + 1)
                v1 = v0 + 1
                v2 = v0 + (nx + 1)
                v3 = v0 + (nx + 1) + 1

                v4 = v0 + (nx + 1) * (ny + 1)
                v5 = v1 + (nx + 1) * (ny + 1)
                v6 = v2 + (nx + 1) * (ny + 1)
                v7 = v3 + (nx + 1) * (ny + 1)

                # Create the tetrahedra
                tetra1 = [v0, v3, v2, v6]
                tetra2 = [v0, v3, v6, v4]
                tetra3 = [v0, v1, v3, v4]
                tetra4 = [v3, v6, v4, v7]
                tetra5 = [v1, v3, v4, v7]
                tetra6 = [v1, v7, v4, v5]

                # Append the tetrahedra to the list of cells
                # cells.extend([tetra1, tetra2, tetra3, tetra4, tetra5, tetra6])
                cells.append(tetra1)
                cells.append(tetra2)
                cells.append(tetra3)
                cells.append(tetra4)
                cells.append(tetra5)
                cells.append(tetra6)

    cells = np.array(cells)
    vmesh = VolumeMesh(vertices=vertices, cells=cells)
    return vmesh


def mesh_to_pointcloud(
    mesh: Mesh, num_points: int, seed: Optional[int] = None
) -> PointCloud:
    """
    Sample uniformly over the surface of a mesh and generate a PointCloud.

    Parameters
    ----------
    mesh : Mesh
        The input triangular mesh.
    num_points : int
        Total number of points to sample.
    seed : int, optional
        Seed for reproducibility.

    Returns
    -------
    PointCloud
        A point cloud sampled over the surface of the mesh.
    """
    if seed is not None:
        np.random.seed(seed)

    # Get triangle vertices
    v0 = mesh.vertices[mesh.faces[:, 0]]
    v1 = mesh.vertices[mesh.faces[:, 1]]
    v2 = mesh.vertices[mesh.faces[:, 2]]

    # Calculate triangle areas using cross product
    tri_areas = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1)

    # Compute probability distribution over triangles
    tri_probs = tri_areas / tri_areas.sum()

    # Choose triangles based on surface area
    chosen_faces = np.random.choice(len(tri_probs), size=num_points, p=tri_probs)

    # Barycentric coordinates sampling
    r1 = np.random.rand(num_points)
    r2 = np.random.rand(num_points)
    sqrt_r1 = np.sqrt(r1)

    u = 1 - sqrt_r1
    v = r2 * sqrt_r1
    w = 1 - u - v

    # Get vertices of the chosen triangles
    tri_v0 = v0[chosen_faces]
    tri_v1 = v1[chosen_faces]
    tri_v2 = v2[chosen_faces]

    # Compute random points in triangles
    points = u[:, None] * tri_v0 + v[:, None] * tri_v1 + w[:, None] * tri_v2

    return PointCloud(points=points)


def create_compass_letters(size=0.5, distance=2.0):

    faces_E = np.array(
        [
            [0, 1, 2],
            [3, 2, 4],
            [3, 0, 2],
            [4, 5, 3],
            [3, 5, 6],
            [9, 7, 8],
            [10, 9, 8],
            [10, 2, 9],
            [2, 1, 9],
            [1, 12, 11],
            [1, 0, 12],
        ]
    )

    vertices_E = size * np.array(
        [
            [-0.4, -0.2, 0],
            [-0.4, 0.2, 0],
            [-0.8, 0, 0],
            [-0.4, -0.6, 0],
            [-0.8, -1, 0],
            [0.8, -1, 0],
            [0.8, -0.6, 0],
            [0.8, 0.6, 0],
            [0.8, 1, 0],
            [-0.4, 0.6, 0],
            [-0.8, 1, 0],
            [0.6, 0.2, 0],
            [0.6, -0.2, 0],
        ]
    )

    faces_S = np.array(
        [
            [26, 22, 25],
            [23, 24, 25],
            [25, 22, 23],
            [22, 26, 27],
            [29, 21, 28],
            [30, 20, 29],
            [20, 21, 29],
            [21, 22, 27],
            [39, 40, 15],
            [28, 21, 27],
            [11, 41, 10],
            [41, 11, 12],
            [9, 10, 42],
            [42, 8, 9],
            [13, 41, 12],
            [40, 41, 14],
            [13, 14, 41],
            [15, 40, 14],
            [7, 42, 43],
            [6, 7, 43],
            [8, 42, 7],
            [10, 41, 42],
            [19, 30, 31],
            [17, 38, 16],
            [32, 19, 31],
            [15, 16, 39],
            [33, 18, 32],
            [34, 18, 33],
            [17, 35, 36],
            [34, 35, 18],
            [18, 35, 17],
            [19, 32, 18],
            [36, 37, 17],
            [38, 39, 16],
            [5, 6, 44],
            [44, 6, 43],
            [45, 5, 44],
            [5, 45, 4],
            [2, 0, 1],
            [45, 3, 4],
            [3, 45, 2],
            [2, 45, 0],
            [38, 17, 37],
            [20, 30, 19],
        ]
    )

    vertices_S = size * np.array(
        [
            [0.370957, 0.299215, 0],
            [0.742432, 0.327176, 0],
            [0.716825, 0.548845, 0],
            [0.619097, 0.748731, 0],
            [0.452885, 0.896401, 0],
            [0.245687, 0.978833, 0],
            [0.024166, 1.007479, 0],
            [-0.198607, 0.991232, 0],
            [-0.410833, 0.922389, 0],
            [-0.587984, 0.788129, 0],
            [-0.695647, 0.593699, 0],
            [-0.715077, 0.372408, 0],
            [-0.638172, 0.164419, 0],
            [-0.477425, 0.011067, 0],
            [-0.273695, -0.079873, 0],
            [-0.057912, -0.138985, 0],
            [0.158914, -0.194315, 0],
            [0.361705, -0.284604, 0],
            [0.396577, -0.489756, 0],
            [0.220354, -0.616842, 0],
            [-0.001297, -0.638744, 0],
            [-0.217502, -0.586556, 0],
            [-0.376797, -0.436685, 0],
            [-0.423533, -0.218943, 0],
            [-0.789656, -0.250954, 0],
            [-0.767769, -0.47371, 0],
            [-0.679549, -0.678854, 0],
            [-0.527745, -0.842488, 0],
            [-0.329818, -0.946172, 0],
            [-0.110962, -0.993499, 0],
            [0.113066, -1.000544, 0],
            [0.333561, -0.962167, 0],
            [0.535612, -0.866527, 0],
            [0.693524, -0.709054, 0],
            [0.781724, -0.504252, 0],
            [0.783963, -0.281321, 0],
            [0.696056, -0.076894, 0],
            [0.530235, 0.072117, 0],
            [0.32523, 0.161676, 0],
            [0.108579, 0.219858, 0],
            [-0.109343, 0.27314, 0],
            [-0.311003, 0.365026, 0],
            [-0.29052, 0.568219, 0],
            [-0.084984, 0.645811, 0],
            [0.138356, 0.635988, 0],
            [0.319499, 0.515575, 0],
        ]
    )

    faces_N = np.array(
        [
            [5, 1, 0],
            [2, 5, 4],
            [3, 2, 4],
            [2, 1, 5],
            [6, 2, 7],
            [3, 7, 2],
            [5, 9, 8],
            [0, 9, 5],
        ]
    )

    vertices_N = size * np.array(
        [
            [-0.8, 1, 0],
            [-0.2, 1, 0],
            [0.4, -0.6, 0],
            [0.8, -1, 0],
            [0.2, -1, 0],
            [-0.4, 0.6, 0],
            [0.4, 1, 0],
            [0.8, 1, 0],
            [-0.4, -1, 0],
            [-0.8, -1, 0],
        ]
    )

    faces_W = np.array(
        [
            [11, 1, 2],
            [3, 10, 11],
            [0, 1, 11],
            [0, 11, 12],
            [3, 4, 8],
            [8, 4, 5],
            [6, 8, 5],
            [2, 3, 11],
            [10, 3, 9],
            [9, 3, 8],
            [8, 6, 7],
        ]
    )

    vertices_W = size * np.array(
        [
            [-0.8, 1, 0],
            [-0.5, -1, 0],
            [-0.2, -1, 0],
            [0, -0.4, 0],
            [0.2, -1, 0],
            [0.5, -1, 0],
            [0.8, 1, 0],
            [0.5, 1, 0],
            [0.3, -0.4, 0],
            [0.1, 0.2, 0],
            [-0.1, 0.2, 0],
            [-0.3, -0.4, 0],
            [-0.5, 1, 0],
        ]
    )

    mesh_E = Mesh(vertices=vertices_E, faces=faces_E)
    mesh_S = Mesh(vertices=vertices_S, faces=faces_S)
    mesh_N = Mesh(vertices=vertices_N, faces=faces_N)
    mesh_W = Mesh(vertices=vertices_W, faces=faces_W)

    # Move the letters to the correct position
    mesh_E.vertices[:, 0:3] += np.array([distance, 0.0, 0.0])
    mesh_S.vertices[:, 0:3] += np.array([0.0, -1.0 * distance, 0.0])
    mesh_N.vertices[:, 0:3] += np.array([0.0, distance, 0.0])
    mesh_W.vertices[:, 0:3] += np.array([-1.0 * distance, 0.0, 0.0])

    letters_mesh = concatenate_meshes([mesh_E, mesh_S, mesh_N, mesh_W])

    return letters_mesh
