import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from typing import Any
from dtcc_viewer.colors import color_maps


class PointCloudWrapper:
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
    dict_colors: dict
    pc_avrg_pt: np.ndarray  # [1 x 3]
    size: float
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self,
        name: str,
        pc: PointCloud,
        size: float = 0.2,
        data: Any = None,
    ) -> None:
        """Initialize a PointCloudData object.

        Parameters
        ----------
        name : str
            Name of the point cloud data.
        pc : PointCloud
            The PointCloud object from which to generate data.
        size : float, optional
            Particle size in meters (default is 0.2 m).
        data : np.ndarray, optional
            Additional data for color calculation (default is None).
        colors : np.ndarray, optional
            Colors for each point in the pointcloud (default is None).

        Returns
        -------
        None
        """

        self.name = name
        self.size = size
        self.dict_data = {}
        self.n_points = len(pc.points)
        self.points = np.array(pc.points, dtype="float32").flatten()
        self._reformat_data_dict(data=data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_pc_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.points)
        self._reformat_pc()

    def _reformat_data_dict(self, data: np.ndarray = None):
        """Generate colors for the point cloud based on the provided data."""

        # Coloring by dictionary
        if isinstance(data, dict):
            if self._generate_dict_data(data, self.n_points):
                return True
            else:
                warning("Data dict for pc colors does not match point count!")

        # Coloring by array data
        elif data is not None:
            if self.n_points == len(data):
                self.dict_data["Data"] = data
                return True
            else:
                warning("Provided color data does not match the particle count!")

        info("No data provided for point cloud -> coloring per z-value")
        z = self.points[2::3]  # Color by height if no data is provided
        self.dict_data["Default data"] = z

        return True

    def _generate_dict_data(self, data_dict: dict, n_points: int):
        """Check the data dict to math point count."""
        keys = data_dict.keys()

        for key in keys:
            row_data = data_dict[key]
            if len(row_data) == n_points:
                self.dict_data[key] = row_data
            else:
                warning(f"Dict data in for key {key} doesn't match point count:")

        return True

    def _move_pc_to_origin_multi(self, bb: BoundingBox = None):
        """Move the point cloud data to the origin using multiple recenter vectors."""
        move_vec = np.tile(bb.center_vec, self.n_points)
        if bb is not None:
            self.points += move_vec

    def _reformat_pc(self):
        """Flatten the point cloud data arrays for further processing."""
        self.points = np.array(self.points, dtype="float32")
