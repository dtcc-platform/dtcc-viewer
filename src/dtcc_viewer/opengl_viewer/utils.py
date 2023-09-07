import pyrr
import numpy as np
from enum import IntEnum
from dtcc_model import Mesh, PointCloud


class MeshShading(IntEnum):
    wireframe = 0
    shaded_ambient = 1
    shaded_diffuse = 2
    shaded_shadows = 3


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
        if np.shape(vertices)[1] == 3 or np.shape(vertices)[1] == 9:
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


def calc_blended_color(min, max, value):
    """
    Calculate a blended color based on input range and value.

    Parameters
    ----------
    min_value : float
        The minimum value of the range.
    max_value : float
        The maximum value of the range.
    value : float
        The input value.

    Returns
    -------
    list of float
        A list representing the RGB values of the calculated blended color.
    """
    diff = max - min
    if (diff) <= 0:
        print(
            "Error: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!"
        )
        return [1, 0, 1]  # Error, returning magenta

    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min or new_value >= new_max:
        # Returning red [1,0,0]
        return [1.0, 0.0, 0.0]
    else:
        if percentage >= 0.0 and percentage <= 10.0:
            # Red fading to Magenta [1,0,x], where x is increasing from 0 to 1
            frac = percentage / 10.0
            return [1.0, 0.0, (frac * 1.0)]

        elif percentage > 10.0 and percentage <= 30.0:
            # Magenta fading to blue [x,0,1], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 10.0) / 20.0
            return [(frac * 1.0), 0.0, 1.0]

        elif percentage > 30.0 and percentage <= 50.0:
            # Blue fading to cyan [0,1,x], where x is increasing from 0 to 1
            frac = abs(percentage - 30.0) / 20.0
            return [0.0, (frac * 1.0), 1.0]

        elif percentage > 50.0 and percentage <= 70.0:
            # Cyan fading to green [0,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 50.0) / 20.0
            return [0.0, 1.0, (frac * 1.0)]

        elif percentage > 70.0 and percentage <= 90.0:
            # Green fading to yellow [x,1,0], where x is increasing from 0 to 1
            frac = abs(percentage - 70.0) / 20.0
            return [(frac * 1.0), 1.0, 0.0]

        elif percentage > 90.0 and percentage <= 100.0:
            # Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 90.0) / 10.0
            return [1.0, (frac * 1.0), 0.0]

        elif percentage > 100.0:
            # Returning red if the value overshoots the limit.
            return [1.0, 0.0, 0.0]
