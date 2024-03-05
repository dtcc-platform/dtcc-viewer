import numpy as np
from dtcc_model import Mesh
from dtcc_model import Bounds, Raster
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl.utils import BoundingBox, Shading, Submeshes
from dtcc_viewer.logging import info, warning
from pprint import PrettyPrinter


class RasterWrapper:
    """Support class for rendering rasters."""

    name: str
    vertices: np.ndarray
    indices: np.ndarray
    bb_local: BoundingBox
    bb_global: BoundingBox = None

    def __init__(self, name: str, raster: Raster) -> None:
        """Initialize the MeshData object."""
        self.name = name
        self.dict_data = {}

        self._extract_raster_data(raster)
        self._create_raster_mesh(raster)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mesh_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())
        self._reformat_mesh()

    def _extract_raster_data(self, raster: Raster):
        self.data = np.array(raster.data, dtype="float32")

    def _create_raster_mesh(self, raster: Raster):
        # Creating a single quad for mapping of a raster texture
        dx = raster.shape[0] * raster.cell_size[0]
        dy = raster.shape[1] * raster.cell_size[1]
        z = 0.0
        tex_min = 0.0
        tex_max = 1.0

        self.vertices = [
            -dx / 2.0,
            -dy / 2.0,
            z,
            tex_min,
            tex_min,
            dx / 2.0,
            -dy / 2.0,
            z,
            tex_max,
            tex_min,
            -dx / 2.0,
            dy / 2.0,
            z,
            tex_min,
            tex_max,
            dx / 2.0,
            -dy / 2.0,
            z,
            tex_max,
            tex_min,
            -dx / 2.0,
            dy / 2.0,
            z,
            tex_min,
            tex_max,
            dx / 2.0,
            dy / 2.0,
            z,
            tex_max,
            tex_max,
        ]
        self.indices = [
            0,
            1,
            2,
            3,
            4,
            5,
        ]

        self.vertices = np.array(self.vertices, dtype="float32")
        self.indices = np.array(self.indices, dtype="uint32")

    def _move_mesh_to_origin(self, bb: BoundingBox):
        # [x, y, z, r, g, b, nx, ny ,nz]
        v_count = len(self.vertices) // 5
        recenter_vec = np.concatenate((bb.center_vec, [0, 0]), axis=0)
        recenter_vec = np.tile(recenter_vec, v_count)
        self.vertices += recenter_vec

    def get_vertex_positions(self):
        """Get the vertex positions of the mesh."""
        vertex_mask = np.array([1, 1, 1, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 5
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _reformat_mesh(self):
        """Reformat the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl types
        self.vertices = np.array(self.vertices, dtype="float32")
        self.indices = np.array(self.indices, dtype="uint32")
