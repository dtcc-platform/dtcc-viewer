import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString, MultiLineString
from dtcc_viewer.opengl.wrp_data import MLSDataWrapper
from typing import Any


class MultiLineStringsWrapper:
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
    name : str
        Name of the line strings collection.
    bb_local : BoundingBox
        Local bounding box for the line strings.
    bb_global : BoundingBox
        Global bounding box for the entire scene.
    """

    dict_data: dict
    vertices: np.ndarray  # [n_vertices x 3] = [v1,v2,v3,v4,.. n_vertices]
    indices: np.ndarray  # [n_roads x 2] = [[v3, v2,], [v5, v2]...]
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self, name: str, mls: MultiLineString, mts: int, data: Any = None
    ) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        self.mts = mts

        v_count = self._get_vertex_count(mls)
        self.data_wrapper = MLSDataWrapper(mls, v_count, self.mts)
        self._restructure_multilinestring(mls)
        self._append_data(data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mls_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())
        self._reformat()

    def get_vertex_positions(self):
        """Get the vertex positions"""
        vertex_mask = np.array([1, 1, 1, 0, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 6
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _move_mls_to_origin(self, bb: BoundingBox = None):
        if bb is not None:
            v_count = len(self.vertices) // 6
            recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0]), axis=0)
            recenter_vec_tiled = np.tile(recenter_vec, v_count)
            self.vertices += recenter_vec_tiled

    def _get_segment_count(self, mls: MultiLineString):
        total_count = 0
        for line_string in mls.geoms:
            total_count += len(line_string.coords) - 1
        return total_count

    def _get_vertex_count(self, mls: MultiLineString):
        total_count = 0
        for line_string in mls.geoms:
            total_count += len(line_string.coords)
        return total_count

    def _restructure_multilinestring(self, mls: MultiLineString):
        l_count_tot = self._get_segment_count(mls)
        v_count_tot = self._get_vertex_count(mls)
        indices = np.zeros([l_count_tot, 2], dtype=int)

        # vertices = [x, y, z, tx, ty, id, x, y, z ...]
        vertices = np.zeros([v_count_tot, 6])

        idx1 = 0
        idx2 = 0
        for ls in mls.geoms:
            l_count = len(ls.coords[:]) - 1  # Line segegment count
            v_count = len(ls.coords[:])  # Vertex count
            indices1 = np.arange(idx1, idx1 + l_count, dtype=int)
            indices2 = np.arange(idx1 + 1, idx1 + l_count + 1, dtype=int)
            indices[idx2 : (idx2 + l_count), 0] = indices1
            indices[idx2 : (idx2 + l_count), 1] = indices2
            vertices[idx1 : (idx1 + v_count), 0:3] = np.array(list(ls.coords))
            idx1 += len(ls.coords[:])
            idx2 += l_count

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

    def _reformat(self):
        """Flatten the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl implementation
        self.vertices = np.array(self.vertices, dtype="float32")
        self.indices = np.array(self.indices, dtype="uint32")