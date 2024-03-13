import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from typing import Any


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
    data_dict: dict
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
        self.data_dict = {}
        self.n_points = len(pc.points)
        self.points = np.array(pc.points, dtype="float32").flatten()
        self._restructure_data(data=data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_pc_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.points)
        self._reformat_pc()

    def _restructure_data(self, data: Any = None):
        """Generate colors for the point cloud based on the provided data."""

        new_dict = {
            "slot0": np.zeros(self.n_points),
            "slot1": np.zeros(self.n_points),
            "slot2": np.zeros(self.n_points),
        }

        if isinstance(data, dict):
            info("Provided color data is dict.")
            self.data_dict = self._restructure_data_dict(data, self.n_points, new_dict)
        elif isinstance(data, np.ndarray):
            info("Provided color data is np.ndarray.")
            self.data_dict = self._restructure_data_array(data, self.n_points, new_dict)
        else:
            info("No data provided for point cloud -> coloring per z-value")
            z = self.points[2::3]  # Color by height if no data is provided
            new_dict["slot0"] = self.points[0::3]
            new_dict["slot1"] = self.points[1::3]
            new_dict["slot2"] = self.points[2::3]
            self.data_dict = new_dict

    def _restructure_data_array(self, data: np.ndarray, n_points: int, new_dict: dict):
        if self.n_points == len(data):
            new_dict["slot0"] = data
        else:
            warning("Provided data array does not match the particle count!")
        return new_dict

    def _restructure_data_dict(self, data_dict: dict, n_points: int, new_dict: dict):
        """Check the data dict to math point count."""
        keys = data_dict.keys()
        counter = 0
        slots = len(new_dict)
        for key in keys:
            data = data_dict[key]
            if len(data) == n_points:
                if counter < slots:
                    new_dict[f"slot{counter}"] = data
                else:
                    warning("Data in for key {key} doesn't fit available data slots.")
                counter += 1
            else:
                warning(f"Dict data in for key {key} doesn't match point count:")

        return new_dict

    def _move_pc_to_origin_multi(self, bb: BoundingBox = None):
        """Move the point cloud data to the origin using multiple recenter vectors."""
        move_vec = np.tile(bb.center_vec, self.n_points)
        if bb is not None:
            self.points += move_vec

    def _reformat_pc(self):
        """Flatten the point cloud data arrays for further processing."""
        self.points = np.array(self.points, dtype="float32")
