import numpy as np
import math
from enum import IntEnum
from dtcc_core.model import Mesh, PointCloud
from pprint import pp
from dtcc_viewer.logging import info, warning
from dtcc_core.model import MultiSurface, Surface, VolumeMesh, LineString, MultiLineString
from shapely.geometry import Point
from shapely.geometry import LineString as ShapelyLineString
from dtcc_viewer.utils import Direction


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


def create_arrow_mesh(cp: np.ndarray, dir: np.ndarray, r: float, h: float, n: int):
    b_vertices = []
    b_indices = []
    h_vertices = []
    h_indices = []
    angle_increment = 2 * math.pi / n
    h_body = 0.9 * h
    r_body = r
    r_head = 2 * r

    dir /= np.linalg.norm(dir)

    # Calculate perpendicular vectors using cross product
    z = np.array([0.0, 0.0, 1.0])
    if np.allclose(dir, z):
        u = np.array([1.0, 0.0, 0.0])
        v = np.array([0.0, 1.0, 0.0])
    else:
        u = np.linalg.norm(np.cross(dir, z))
        v = np.linalg.norm(np.cross(dir, u))

    # Generate vertices for the top and bottom circles for the cylinder body
    for hs in [0, h_body]:
        for i in range(n):
            ang = i * angle_increment
            p = cp + dir * hs + r_body * (u * math.cos(ang) + v * math.sin(ang))
            b_vertices.append(p)

    # Generate the mesh faces for cylinder body
    for i in range(n):
        b_indices.append([i, (i + 1) % n, i + n])
        b_indices.append([i + n, (i + 1) % n + n, (i + 1) % n])

    body_mesh = Mesh(vertices=np.array(b_vertices), faces=np.array(b_indices))

    # Generate vertices cone head
    for i in range(n):
        ang = i * angle_increment
        p = cp + dir * hs + r_head * (u * math.cos(ang) + v * math.sin(ang))
        h_vertices.append(p)

    h_vertices.append(cp + dir * h)
    h_vertices.append(cp + dir * h_body)

    # Generate the mesh faces for the cone head
    for i in range(n):
        h_indices.append([i, (i + 1) % n, n])
        h_indices.append([i, (i + 1) % n, n + 1])

    head_mesh = Mesh(vertices=np.array(h_vertices), faces=np.array(h_indices))

    mesh = concatenate_meshes([body_mesh, head_mesh])

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
