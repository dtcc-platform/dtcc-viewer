import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString
from dtcc_viewer.opengl.wrp_data import LSDataWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from typing import Any


class LineStringWrapper(Wrapper):
    """Wrapper for rendering a list of LineString.

    This class is used to store a list of LineStrings and associated data for
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

    data_wrapper: LSDataWrapper
    vertices: np.ndarray  # [n_vertices x 3] = [v1,v2,v3,v4,.. n_vertices]
    indices: np.ndarray  # [n_roads x 2] = [[v3, v2,], [v5, v2]...]
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(self, name: str, ls: LineString, mts: int, data: Any = None) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        self.mts = mts

        v_count = len(ls.coords)
        self.data_wrapper = LSDataWrapper(ls, v_count, self.mts)
        self._restructure_linestring(ls)
        self._append_data(data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_lss_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())

    def get_vertex_positions(self):
        """Get the vertex positions"""
        vertex_mask = np.array([1, 1, 1, 0, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 6
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _move_lss_to_origin(self, bb: BoundingBox = None):
        if bb is not None:
            v_count = len(self.vertices) // 6
            recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0]), axis=0)
            recenter_vec_tiled = np.tile(recenter_vec, v_count)
            self.vertices += recenter_vec_tiled

    def _move_lss_to_zero_z(self, bb: BoundingBox):
        self.vertices[2::6] -= bb.zmin

    def _get_vertices(self, lss: list[LineString]):
        return np.array([coord for ls in lss for coord in ls.coords]).flatten()

    def _restructure_linestring(self, line_string: LineString):
        v_count = len(line_string.coords)  # Number of vertices
        l_count = len(line_string.coords) - 1  # Number of line segments

        # vertices = [x, y, z, tx, ty, id, x, y, z ...]
        vertices = np.zeros([v_count, 6])
        indices = np.zeros([l_count, 2], dtype=int)

        indices1 = np.arange(0, l_count, dtype=int)
        indices2 = np.arange(1, l_count + 1, dtype=int)
        indices[0:l_count, 0] = indices1
        indices[0:l_count, 1] = indices2
        vertices[0 : 0 + v_count, 0:3] = np.array(list(line_string.coords))

        indices = indices.flatten()
        vertices = vertices.flatten()
        vertices[3::6] = self.data_wrapper.texel_x
        vertices[4::6] = self.data_wrapper.texel_y

        # Format and flatten the vertices and indices
        self.vertices = np.array(vertices, dtype="float32")
        self.indices = np.array(indices, dtype="uint32")

    def _append_data(self, data: Any = None):
        """Generate colors for the point cloud based on the provided data."""

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
            self.data_wrapper.add_data("Vertex X", self.vertices[0::6])
            self.data_wrapper.add_data("Vertex Y", self.vertices[1::6])
            self.data_wrapper.add_data("Vertex Z", self.vertices[2::6])
