import numpy as np
from dtcc_core.model import Mesh
from dtcc_core.model import Bounds, Raster
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox, Shading, RasterType
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.logging import info, warning
from pprint import PrettyPrinter


class RasterWrapper(Wrapper):
    """Support class for rendering rasters."""

    name: str
    vertices: np.ndarray
    indices: np.ndarray
    type: RasterType
    bb_local: BoundingBox
    bb_global: BoundingBox = None

    def __init__(self, name: str, raster: Raster, vertices: np.ndarray = None) -> None:
        """Initialize the RasterWrapper object."""
        self.name = name
        self.dict_data = {}

        self._find_raster_type(raster)
        self._extract_raster_data(raster)
        self._create_raster_mesh(raster, vertices)

    def _find_raster_type(self, raster: Raster):

        if raster.channels == 1:
            self.type = RasterType.Data
            info("1 channel data raster")
        elif raster.channels == 3:
            self.type = RasterType.RGB
            info("3 channel color raster")
        elif raster.channels == 4:
            self.type = RasterType.RGBA
            info("4 channel color raster")

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())
        self._reformat_mesh()

    def _extract_raster_data(self, raster: Raster):

        if self.type == RasterType.Data:
            self.data = np.array(raster.data, dtype="float32")
        elif self.type == RasterType.RGB:
            self.data = np.array(raster.data, dtype="uint8")
        elif self.type == RasterType.RGBA:
            self.data = np.array(raster.data, dtype="uint8")

    def _create_raster_mesh(self, raster: Raster, vertices: np.ndarray = None):
        # Creating a single quad for mapping of a raster texture

        if vertices is not None:
            self.vertices = vertices
        else:
            xdom = raster.shape[0] * abs(raster.cell_size[0])
            ydom = raster.shape[1] * abs(raster.cell_size[1])
            z = 0.0
            tex_min = 0.0
            tex_max = 1.0
            self.vertices = [
                -xdom / 2.0,
                -ydom / 2.0,
                z,
                tex_min,
                tex_min,
                xdom / 2.0,
                -ydom / 2.0,
                z,
                tex_max,
                tex_min,
                -xdom / 2.0,
                ydom / 2.0,
                z,
                tex_min,
                tex_max,
                xdom / 2.0,
                -ydom / 2.0,
                z,
                tex_max,
                tex_min,
                -xdom / 2.0,
                ydom / 2.0,
                z,
                tex_min,
                tex_max,
                xdom / 2.0,
                ydom / 2.0,
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

    def _move_to_origin(self, bb: BoundingBox):
        # [x, y, z, tx, ty]
        v_count = len(self.vertices) // 5
        recenter_vec = np.concatenate((bb.center_vec, [0, 0]), axis=0)
        recenter_vec = np.tile(recenter_vec, v_count)
        self.vertices += recenter_vec

    def _move_to_zero_z(self, bb: BoundingBox):
        self.vertices[2::5] -= bb.zmin

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


class MultiRasterWrapper:
    """Support class for rendering extra large rasters.

    For large rasters the MultiRasterWrapper is used to split the raster in sub-rasters
    to ensure that the raster textures can fit the GPU memory texture slot capacity.

    The maximum texture size is typically 16384x16384 pixels, but a lower limit is used
    to ensure compatability with older hardware.
    """

    name: str
    type: RasterType
    sub_count: int
    raster_wrappers: list[RasterWrapper]

    def __init__(self, name: str, raster: Raster, max_size: int) -> None:
        """Initialize the MultiRasterWrapper object."""
        self.name = name
        self.type = self._find_raster_type(raster)
        (sub_data, sub_verts) = self._split_raster(raster, max_size)
        self.raster_wrappers = self._create_raster_wrappers(raster, sub_data, sub_verts)

        info(f"Multi raster wrapper created with {self.sub_count} sub-rasters")

    def _find_raster_type(self, raster: Raster):
        if raster.channels == 1:
            info("1 channel data raster")
            return RasterType.Data
        elif raster.channels == 3:
            info("3 channel color raster")
            return RasterType.RGB
        elif raster.channels == 4:
            info("4 channel color raster")
            return RasterType.RGBA

    def _split_raster(self, raster: Raster, size: int):
        """Split a raster into sub-rasters if it is bigger then size."""
        sub_data = []
        sub_vertices = []
        dim = raster.data.shape
        rows = dim[0]
        cols = dim[1]
        for i in range(0, rows, size):
            for j in range(0, cols, size):
                sub_d = self._get_sub_data(raster, i, j, size)
                sub_bb = self._get_sub_bb(raster, i, j, sub_d.shape[0], sub_d.shape[1])
                sub_vs = self._get_quad_vertices(sub_bb)
                sub_data.append(sub_d)
                sub_vertices.append(sub_vs)

        self.sub_count = len(sub_data)
        return sub_data, sub_vertices

    def _get_sub_data(self, raster: Raster, i: int, j: int, size: int):
        """Get sub-raster data from a raster."""
        if self.type == RasterType.Data:
            sub_raster = raster.data[i : i + size, j : j + size]
            sub_raster = np.array(sub_raster, dtype="float32")
        elif self.type == RasterType.RGB or self.type == RasterType.RGBA:
            sub_raster = raster.data[i : i + size, j : j + size, :]
            sub_raster = np.array(sub_raster, dtype="uint8")
        return sub_raster

    def _get_sub_bb(self, raster: Raster, row_1, col_1, size_row, size_col):
        """Get the bounding box of a sub-raster."""
        x_start = row_1 * abs(raster.cell_size[0])
        y_start = col_1 * abs(raster.cell_size[1])
        x_end = x_start + size_row * abs(raster.cell_size[0])
        y_end = y_start + size_col * abs(raster.cell_size[1])

        return BoundingBox(np.array([x_start, y_start, 0, x_end, y_end, 0]))

    def preprocess_drawing(self, bb_global: BoundingBox):
        for raster_wrapper in self.raster_wrappers:
            raster_wrapper.preprocess_drawing(bb_global)

    def _create_raster_vertices(self, bbs: list[BoundingBox]):
        # Creating a single quad for mapping of a raster texture
        sub_vertices = []
        for i, bb in enumerate(bbs):
            vertices = self._get_quad_vertices(bb)
            sub_vertices.append(vertices)

        return sub_vertices

    def _get_quad_indices(self, i):

        indices = np.array([0, 1, 2, 3, 4, 5]) + i * 6

        return indices

    def _get_quad_vertices(self, bb: BoundingBox):
        z = 0.0

        v_count = 6
        texture_coords = np.array([0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1], dtype="float32")
        texture_coords = np.flip(texture_coords)
        texture_coord_mask = np.array([0, 0, 0, 1, 1], dtype=bool)
        texture_coord_mask = np.tile(texture_coord_mask, v_count)

        vertices = [
            -0.5,
            -0.5,
            z,
            0.0,
            0.0,
            0.5,
            -0.5,
            z,
            1.0,
            0.0,
            -0.5,
            0.5,
            z,
            0.0,
            1.0,
            0.5,
            -0.5,
            z,
            1.0,
            0.0,
            -0.5,
            0.5,
            z,
            0.0,
            1.0,
            0.5,
            0.5,
            z,
            1.0,
            1.0,
        ]

        vertices = np.array(vertices, dtype="float32")

        vertices[texture_coord_mask] = texture_coords

        # Scale to match the bounding box size
        vertices[0::5] *= bb.xdom
        vertices[1::5] *= bb.ydom

        # Move vertices to the center of the bounding box
        vertices[0::5] += bb.center_vec[0]
        vertices[1::5] += bb.center_vec[1]

        return vertices

    def get_vertex_positions(self):
        """Get the vertex positions of the mesh."""
        all_vertices = np.array([])
        for rw in self.raster_wrappers:
            vertex_pos = rw.get_vertex_positions()
            all_vertices = np.concatenate((all_vertices, vertex_pos), axis=0)

        return all_vertices

    def _create_raster_wrappers(
        self, raster: Raster, sub_data: list[np.ndarray], sub_vertices: list[np.ndarray]
    ):
        raster_wrappers = []
        for i in range(self.sub_count):
            raster_name = f"{self.name}_{i}"
            vertices = sub_vertices[i]
            new_raster = Raster(data=sub_data[i], crs=raster.crs, georef=raster.georef)
            raster_w = RasterWrapper(raster_name, new_raster, vertices)
            raster_wrappers.append(raster_w)

        return raster_wrappers
