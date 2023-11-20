import pyrr
import numpy as np
from enum import IntEnum
from dtcc_model import Mesh, PointCloud
from pprint import pp


class MeshShading(IntEnum):
    wireframe = 0
    ambient = 1
    diffuse = 2
    wireshaded = 3
    shadows = 4


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
        if np.shape(vertices)[1] > 2:
            self.calc_bounds(vertices)
        elif len(np.shape(vertices)) == 1:
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
