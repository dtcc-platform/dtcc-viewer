import pyrr
import numpy as np
import math
from enum import IntEnum
from dtcc_model import Mesh, PointCloud
from pprint import pp
import triangle as tr
from dtcc_viewer.logging import info, warning
from dtcc_model import MultiSurface, Surface
from shapely.geometry import Point, LineString


class Submeshes:
    face_start_indices: np.ndarray
    face_end_indices: np.ndarray
    ids: np.ndarray
    selected: np.ndarray
    meta_data: dict
    ids_2_uuids: dict  # Mapping between id (int) and uuid (str)
    id_offset: int

    def __init__(self, meshes: list[Mesh], uuids: list[str]):
        self._process_data(meshes, uuids)
        self.id_offset = 0

    def _process_data(self, meshes: list[Mesh], uuids: list[str]):
        face_start_indices = []
        face_end_indices = []
        tot_f_count = 0
        counter = 0
        ids = []

        if len(meshes) != len(uuids):
            warning("Number of meshes and uuids do not match")
            return

        for mesh in meshes:
            # Store face indices for this submesh to be used for picking
            mesh_f_count = len(mesh.faces)
            face_start_indices.append(tot_f_count)
            face_end_indices.append(tot_f_count + mesh_f_count - 1)
            tot_f_count += mesh_f_count

            ids.append(counter)
            counter += 1

        self.ids_2_uuids = {key: value for key, value in zip(ids, uuids)}
        self.face_start_indices = np.array(face_start_indices)
        self.face_end_indices = np.array(face_end_indices)
        self.ids = np.array(ids)

    def offset_ids(self, id_offset):
        self.ids = self.ids + id_offset
        self.ids_2_uuids = {
            key + id_offset: value for key, value in self.ids_2_uuids.items()
        }

    def id_exists(self, id):
        return id in self.ids

    def add_meta_data(self, id, newdata_dict):
        self.meta_data[id] = newdata_dict

    def print(self):
        print("Submeshes data: ")
        print(self.face_start_indices)
        print(self.face_end_indices)
        print(self.ids)

    def set_id_offset(self, offset):
        self.id_offset = offset

    def toogle_selected(self, id):
        self.selected[id] = not self.selected[id]

    def get_face_ids(self, id, mesh: Mesh):
        len(mesh.faces)


class Submesh:
    # Defining the start and end of face list
    face_start: int
    face_end: int
    face_count: int
    id: int
    meta_data: dict

    def __init__(self, face_start, face_end, id):
        self.face_start = face_start
        self.face_end = face_end
        self.face_count = face_end - face_start + 1
        self.id = id
        self.meta_data = {}

    def add_meta_data(self, newkey, newdata):
        self.meta_data[newkey] = newdata


class Shading(IntEnum):
    wireframe = 0
    ambient = 1
    diffuse = 2
    wireshaded = 3
    shadows = 4
    picking = 5


class ColorSchema(IntEnum):
    initial = 0
    red = 1
    blue = 2
    green = 3


class MeshColor(IntEnum):
    color = 1
    white = 2


class ParticleColor(IntEnum):
    color = 1
    white = 2


class Results(IntEnum):
    InvalidInput = 0
    DuplicatedVertices = 1
    FailedNormal = 2
    FailedTriangulation = 3
    SingularMatrix = 4
    TriSuccess = 5
    Success = 6


class UniformLocation:
    move: int
    view: int
    proj: int
    color_by: int
    light_color: int  # Uniform location for light color for diffuse shadow rendering
    light_position: int  # Uniform location for light position for diffuse shadow rendering
    view_position: int  # Uniform location for view position for diffuse shadow rendering
    light_space_matrix: int  # Uniform location for light space matrix for diffuse shadow rendering

    def __init__():
        move = None
        view = None
        proj = None
        pass


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

    def __init__(self, vertices: np.ndarray):
        self.calc_bounds_flat(vertices)
        self.origin = np.array([0, 0, 0])
        self.calc_mid_point()
        self.calc_center_vec()

    def calc_bounds(self, vertices: np.ndarray):
        self.xmin = vertices[:, 0].min()
        self.xmax = vertices[:, 0].max()
        self.ymin = vertices[:, 1].min()
        self.ymax = vertices[:, 1].max()
        self.zmin = vertices[:, 2].min()
        self.zmax = vertices[:, 2].max()

        self.xdom = self.xmax - self.xmin
        self.ydom = self.ymax - self.ymin
        self.zdom = self.zmax - self.zmin

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

    def print(self):
        print("Bounds: ")
        print([self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax])
        print("Mid point: ")
        print(self.mid_pt)
        print("Center vector: ")
        print(self.center_vec)
        print("Domain: ")
        print([self.xdom, self.ydom, self.zdom])


def fit_colors_to_faces(faces: np.ndarray, n_vertices: int, colors: np.ndarray):
    n_colors = len(colors)
    n_faces = len(faces) / 3
    new_colors = []
    c1s, c2s, c3s = [], [], []

    if n_colors == n_vertices:
        # Faces is 1D array
        fv1 = faces[0::3]
        fv2 = faces[1::3]
        fv3 = faces[2::3]
        c1s = colors[fv1, :]
        c2s = colors[fv2, :]
        c3s = colors[fv3, :]

    elif n_colors == n_faces:
        f_indices = range(0, n_faces)
        c1s = colors[f_indices, :]
        c2s = colors[f_indices, :]
        c3s = colors[f_indices, :]

    new_colors = np.zeros(n_vertices * 3, dtype="float32")

    new_colors[0::9] = c1s[:, 0]
    new_colors[1::9] = c1s[:, 1]
    new_colors[2::9] = c1s[:, 2]
    new_colors[3::9] = c2s[:, 0]
    new_colors[4::9] = c2s[:, 1]
    new_colors[5::9] = c2s[:, 2]
    new_colors[6::9] = c3s[:, 0]
    new_colors[7::9] = c3s[:, 1]
    new_colors[8::9] = c3s[:, 2]

    return new_colors


def calc_recenter_vector(mesh: Mesh = None, pc: PointCloud = None):
    """
    Calculate a recentering vector based on mesh vertices and point cloud points.

    Parameters
    ----------
    mesh : Mesh, optional
        A Mesh object representing the mesh (default is None).
    pc : PointCloud, optional
        A PointCloud object representing the point cloud (default is None).

    Returns
    -------
    numpy.ndarray
        A numpy array representing the calculated recentering vector.
    """

    all_vertices = np.array([[0, 0, 0]])

    if mesh is not None:
        all_vertices = np.concatenate((all_vertices, mesh.vertices), axis=0)

    if pc is not None:
        all_vertices = np.concatenate((all_vertices, pc.points), axis=0)

    # Remove the [0,0,0] row that was added to enable concatenate.
    all_vertices = np.delete(all_vertices, obj=0, axis=0)

    bb = BoundingBox(all_vertices)

    return bb


def calc_colormap(n_data):
    a = np.arange(0, 106)

    n_colors = 4

    rest = n_data % n_colors

    a1 = a[0 : len(a) - rest]
    a2 = a[len(a) - rest : -1]

    # if n_data % 2 == 0:


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


def surface_2_mesh(vertices):
    vertices = remove_duplicate_vertices(vertices)

    # Capture simple cases
    if vertices.shape[0] < 3:
        warning("Surface has fewer then 3 vertices -> returning None")
        return None, Results.InvalidInput
    elif vertices.shape[0] == 3:
        mesh = Mesh(vertices=vertices, faces=np.array([[0, 1, 2]]))
        return mesh, Results.Success
    elif vertices.shape[0] == 4:
        mesh = Mesh(vertices=vertices, faces=np.array([[0, 1, 2], [0, 2, 3]]))
        return mesh, Results.Success

    centroid = np.mean(vertices, axis=0)
    surface_normal = get_normal_from_surface(vertices, centroid)

    if surface_normal is None:
        warning("Surface normal is None -> returning None")
        return None, Results.FailedNormal

    T = calc_translation_matrix(centroid)
    R = rodrigues_rotation_matrix(surface_normal, np.array([0, 0, 1]))

    # Calculate the transformation matrix
    M = R @ T

    det = np.linalg.det(M)
    singular = np.isclose(det, 0)

    if singular:
        warning("Singular matrix -> returning None")
        return None, Results.SingularMatrix

    M_inv = np.linalg.inv(M)

    # Add 1 to the end of each vertex
    vertices = np.hstack((vertices, np.ones((vertices.shape[0], 1))))

    # Transforming the vertices to the xy-plane
    for i in range(vertices.shape[0]):
        vertices[i, :] = M @ vertices[i, :]

    vertices[:, 2] = 0

    # Triangulate the vertices
    t = tr.triangulate({"vertices": vertices[:, :2]})  # , "a0.2")

    if "triangles" not in t:  # If the triangulation fails
        warning("Triangulation failed -> returning None")
        return None, Results.FailedTriangulation

    # Build mesh from untransformed vertices and faces
    tri_faces = np.array(t["triangles"])
    vertices = np.array(t["vertices"])

    # Add 0 and then 1 to the end of each vertex
    vertices = np.hstack((vertices, np.zeros((vertices.shape[0], 1))))
    vertices = np.hstack((vertices, np.ones((vertices.shape[0], 1))))

    # Transforming the vertices back to 3d position
    for i in range(vertices.shape[0]):
        vertices[i, :] = M_inv @ vertices[i, :]

    # Remove last column from vertices
    mesh = Mesh(vertices=vertices[:, :3], faces=tri_faces)

    return mesh, Results.TriSuccess


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


def create_linestring_circle(center, radius, num_segments):
    # Calculate the angle between each segment
    angle_step = 2 * math.pi / num_segments

    # Generate points around the circumference of the circle
    points = []
    for i in range(num_segments):
        x = center.x + radius * math.cos(i * angle_step)
        y = center.y + radius * math.sin(i * angle_step)
        z = center.z
        points.append(Point(x, y, z))

    points.append(points[0])
    # Create a LineString from the points
    circle_line = LineString(points)

    return circle_line


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
        side_surface = Surface(vertices=np.array(side_surface_vertices))
        side_surfaces.append(side_surface)

    # Create the MultiSurface representing the cylinder
    all_surfaces = [top_surface, bottom_surface] + side_surfaces
    multisurface = MultiSurface(surfaces=all_surfaces)

    return multisurface


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


shader_cmaps = {
    "rainbow": 0,
    "inferno": 1,
    "blackbody": 2,
    "turbo": 3,
    "viridis": 4,
}