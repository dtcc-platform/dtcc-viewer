import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString
from dtcc_viewer.opengl.wrp_data import LSDataWrapper
from typing import Any


class BoundsWrapper:
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

    vertices: np.ndarray  # [n_vertices x 3] = [v1,v2,v3,v4,.. n_vertices]
    indices: np.ndarray  # [n_roads x 2] = [[v3, v2,], [v5, v2]...]
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self,
        name: str,
        bounds: Bounds,
    ) -> None:
        """Initialize a line string wrapper object."""
        self.dict_data = {}
        self.name = name

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_lss_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())
        self._reformat()

    def _move_lss_to_origin(self, bb: BoundingBox = None):
        if bb is not None:
            v_count = len(self.vertices) // 6
            recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0]), axis=0)
            recenter_vec_tiled = np.tile(recenter_vec, v_count)
            self.vertices += recenter_vec_tiled

    def _move_lss_to_zero_z(self, bb: BoundingBox):
        self.vertices[2::6] -= bb.zmin

    def _restructure_linestring(self, bounds: Bounds):
        """Restructure the line string data for OpenGL compatibility."""
        self.vertices = np.array(bounds.bounds, dtype="float32")
        self.indices = np.array([0, 1, 1, 3, 3, 2, 2, 0], dtype="uint32")

    def get_vertex_positions(self):
        """Get the vertex positions"""
        vertex_mask = np.array([1, 1, 1, 0, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 6
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _reformat(self):
        """Flatten the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl implementation
        self.vertices = np.array(self.vertices, dtype="float32")
        self.indices = np.array(self.indices, dtype="uint32")
