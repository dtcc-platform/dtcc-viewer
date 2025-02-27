import numpy as np
from dtcc_core.model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.data_wrapper import MeshDataWrapper, PointsDataWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.logging import info, warning
from typing import Any


class PointCloudWrapper(Wrapper):
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
        self.points = np.array(pc.points, dtype="float64").flatten()
        fields = self._get_fields_data(pc)
        self._append_data(pc, fields, data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_pc_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.points)
        self._reformat_pc()

    def get_vertex_positions(self):
        return self.points

    def _get_fields_data(self, pc: PointCloud):
        """Extract data fields from the point cloud object."""
        fields = pc.fields
        data = {}
        for field in fields:
            if field.dim == 1:
                data[field.name] = field.values
            elif field.dim != 1:
                warning("Viewer only supports scalar field in current implementation")
                warning(f"Field '{field.name}' has dimension != 1. Skipping.")
        return data

    def _append_data(self, pc: PointCloud, fields: dict, data: Any = None):
        """Generate colors for the point cloud based on the provided data."""

        self.data_wrapper = PointsDataWrapper(len(pc.points), self.mts)
        results = []

        if fields is not None:
            for key, value in fields.items():
                success = self.data_wrapper.add_data(key, value)
                results.append(success)

        if data is not None:
            if type(data) == dict:
                for key, value in data.items():
                    success = self.data_wrapper.add_data(key, value)
                    results.append(success)
            elif type(data) == np.ndarray:
                success = self.data_wrapper.add_data("Data", data)
                results.append(success)

        if not np.any(results):
            self.data_wrapper.add_data("Vertex Z", self.points[2::3])
            self.data_wrapper.add_data("Vertex X", self.points[0::3])
            self.data_wrapper.add_data("Vertex Y", self.points[1::3])

    def _move_pc_to_origin(self, bb: BoundingBox = None):
        """Move the point cloud data to the origin using multiple recenter vectors."""
        move_vec = np.tile(bb.center_vec, self.n_points)
        if bb is not None:
            self.points += move_vec

    def _move_pc_to_zero_z(self, bb: BoundingBox):
        self.points[2::3] -= bb.zmin

    def _reformat_pc(self):
        """Flatten the point cloud data arrays for further processing."""
        self.points = np.array(self.points, dtype="float32")
