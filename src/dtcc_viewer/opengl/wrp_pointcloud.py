import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_data import MeshDataWrapper, PCDataWrapper
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

    data_wrapper: MeshDataWrapper
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
        mts: int,
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
        self.mts = mts
        self.data_dict = {}
        self.n_points = len(pc.points)
        self.points = np.array(pc.points, dtype="float32").flatten()
        self._restructure_data(pc, data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_pc_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.points)
        self._reformat_pc()

    def _restructure_data(self, pc: PointCloud, data: Any = None):
        """Generate colors for the point cloud based on the provided data."""

        self.data_wrapper = PCDataWrapper(pc, self.mts)

        data_1 = self.points[0::3]
        data_2 = self.points[1::3]
        data_3 = self.points[2::3]

        data_1 = np.array(data_1, dtype="float32")
        data_2 = np.array(data_2, dtype="float32")
        data_3 = np.array(data_3, dtype="float32")

        self.data_wrapper.add_data("Vertex X", data_1)
        self.data_wrapper.add_data("Vertex Y", data_2)
        self.data_wrapper.add_data("Vertex Z", data_3)

    def _move_pc_to_origin_multi(self, bb: BoundingBox = None):
        """Move the point cloud data to the origin using multiple recenter vectors."""
        move_vec = np.tile(bb.center_vec, self.n_points)
        if bb is not None:
            self.points += move_vec

    def _reformat_pc(self):
        """Flatten the point cloud data arrays for further processing."""
        self.points = np.array(self.points, dtype="float32")
