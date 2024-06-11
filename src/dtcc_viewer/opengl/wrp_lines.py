import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString, MultiLineString
from dtcc_viewer.opengl.data_wrapper import LinesDataWrapper
from dtcc_viewer.opengl.data_wrapper import PointsDataWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from typing import Any


class LinesWrapper(Wrapper):
    """Wrapper for rendering a lines represented as a list of vertices and indices.

    This class is used to store a list of lines and associated data for
    the purpous of visualization. The class provides methods to restructure
    the data to a format that fits the OpenGL functions.

    Attributes
    ----------
    vertices : np.ndarray
        Array of vertex coordinates in the format [n_points x 3].
    indices : np.ndarray
        Array of indices for the line strings in the format [n_lines x 2].
    data : np.ndarray or dict
        Data associated with each vertex.
    name : str
        Name of the line strings collection.
    bb_local : BoundingBox
        Local bounding box for the line strings.
    bb_global : BoundingBox
        Global bounding box for the entire scene.
    """

    vertices: np.ndarray  # [n_vertices x 3] = [v1,v2,v3,v4,.. n_vertices]
    indices: np.ndarray  # [n_roads x 2] = [[v3, v2,], [v5, v2]...]
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self,
        name: str,
        vertices: np.ndarray,
        indices: np.ndarray,
        mts: int,
        data: Any = None,
    ) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        self.mts = mts

        self._append_data(vertices, data)
        self._restructure(vertices, indices)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())

    def get_vertex_positions(self):
        """Get the vertex positions"""
        vertex_mask = np.array([1, 1, 1, 0, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 6
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _move_to_origin(self, bb: BoundingBox = None):
        if bb is not None:
            v_count = len(self.vertices) // 6
            recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0]), axis=0)
            recenter_vec_tiled = np.tile(recenter_vec, v_count)
            self.vertices += recenter_vec_tiled

    def _get_vertices(self, lss: list[LineString]):
        return np.array([coord for ls in lss for coord in ls.coords]).flatten()

    def _restructure(self, vertices: np.ndarray, indices: np.ndarray):

        # Vertex = [x1, y1, z1, texel_x, texel_y, x2, y2, z2, ...]
        new_vertices = np.zeros(len(vertices) * 6)
        new_vertices[0::6] = vertices[:, 0]
        new_vertices[1::6] = vertices[:, 1]
        new_vertices[2::6] = vertices[:, 2]
        new_vertices[3::6] = self.data_wrapper.texel_x
        new_vertices[4::6] = self.data_wrapper.texel_y
        new_vertices[5::6] = np.arange(len(vertices))

        # Indices = [[v1, v2], [v3, v4], ...] -> [v1, v2, v3, v4, ...]
        new_indices = indices.flatten()

        # Format and flatten the vertices and indices
        self.vertices = np.array(new_vertices, dtype="float32")
        self.indices = np.array(new_indices, dtype="uint32")

    def _append_data(self, vertices: np.ndarray, data: Any = None):
        """Generate colors for the point cloud based on the provided data."""

        self.data_wrapper = PointsDataWrapper(len(vertices), self.mts)
        results = []

        if data is not None:
            if type(data) == dict:
                for key, value in data.items():
                    success = self.data_wrapper.add_data(key, value)
                    results.append(success)
            elif type(data) == np.ndarray:
                success = self.data_wrapper.add_data("Data", data)
                results.append(success)

        if data is None or not np.any(results):
            self.data_wrapper.add_data("Vertex Z", vertices[:, 2])
            self.data_wrapper.add_data("Vertex X", vertices[:, 0])
            self.data_wrapper.add_data("Vertex Y", vertices[:, 1])
