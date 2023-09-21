import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox


class PointCloudData:
    """Point cloud attributes and data structured for the purpous of rendering.

    This class is used to store point cloud data along with color information
    for visualization purposes. The class also provides methods to restructure
    the data to a format that fits the OpenGL functions.

    Attributes
    ----------
    points : np.ndarray
        Array of point coordinates in the format [n_points x 3].
    colors : np.ndarray
        Array of colors associated with each point in the format [n_points x 3].
    pc_avrg_pt : np.ndarray
        Average point of the point cloud for recentering in the format [1 x 3].
    name : str
        Name of the point cloud data.
    """

    points: np.ndarray  # [n_points x 3]
    colors: np.ndarray  # [n_points x 3]
    pc_avrg_pt: np.ndarray  # [1 x 3]
    pc_size: float
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self,
        name: str,
        pc: PointCloud,
        data: np.ndarray = None,
        colors: np.ndarray = None,
    ) -> None:
        """Initialize a PointCloudData object.

        Parameters
        ----------
        name : str
            Name of the point cloud data.
        pc : PointCloud
            The PointCloud object from which to generate data.
        data : np.ndarray
            Additional data for color calculation.
        recenter_vec : np.ndarray
            Recentering vector for point cloud data.

        Returns
        -------
        None
        """

        self.name = name
        self.pc_size = 0.2
        self.colors = self._generate_pc_colors(pc, pc_data=data, pc_colors=colors)
        self.points = pc.points

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self.points = self._move_pc_to_origin_multi(self.points, self.bb_global)
        self.bb_local = BoundingBox(self.points)
        [self.points, self.colors] = self._flatten_pc(self.points, self.colors)

    def _generate_pc_colors(
        self,
        pc: PointCloud,
        pc_data: np.ndarray = None,
        pc_colors: np.ndarray = None,
    ) -> np.ndarray:
        """Generate colors for the point cloud based on the provided data.

        Parameters
        ----------
        pc : PointCloud
            The PointCloud object to generate colors for.
        pc_data : np.ndarray, optional
            Additional data for color calculation (default is None).

        Returns
        -------
        np.ndarray
            Array of colors for the point cloud.
        """
        colors = []
        n_points = len(pc.points)

        if pc_colors is not None:
            n_pc_colors = len(pc_colors)
            if n_pc_colors == n_points:
                colors = np.array(pc_colors)
                return colors
            else:
                print(
                    "WARNING: Point cloud colors provided does not match point count!"
                )

        if pc_data is not None:
            if len(pc.points) == len(pc_data):
                colors = calc_colors_rainbow(pc_data)
            else:
                print("WARNING: Provided color data does not match the particle count!")
                print("Default colors are used instead -> i.e. coloring per z-value")
                z = pc.points[:, 2]
                colors = calc_colors_rainbow(z)
        else:
            print("No data provided for point cloud -> colors are set based on z-value")
            z = pc.points[:, 2]  # Color by height if no data is provided
            colors = calc_colors_rainbow(z)

        colors = np.array(colors)
        colors = colors[:, 0:3]
        return colors

    def _move_pc_to_origin_multi(self, points: np.ndarray, bb: BoundingBox = None):
        """Move the point cloud data to the origin using multiple recenter vectors.

        Parameters
        ----------
        points : np.ndarray
            Array of point cloud data.
        recenter_vec : np.ndarray, optional
            Recenter vector for each point (default is None).

        Returns
        -------
        np.ndarray
            Moved point cloud data.
        """
        if bb is not None:
            points += bb.center_vec

        return points

    def _flatten_pc(self, points: np.ndarray, colors: np.ndarray):
        """Flatten the point cloud data arrays for further processing.

        Parameters
        ----------
        points : np.ndarray
            Array of point cloud data.
        colors : np.ndarray
            Array of point cloud colors.

        Returns
        -------
        np.ndarray
            Flattened point cloud data array.
        np.ndarray
            Flattened point cloud colors array.
        """
        points = np.array(points, dtype="float32").flatten()
        colors = np.array(colors, dtype="float32").flatten()
        return points, colors
