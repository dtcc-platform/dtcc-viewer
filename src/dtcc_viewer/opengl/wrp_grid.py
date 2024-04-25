import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString, Point, MultiLineString
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper, MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_model import Grid, VolumeGrid
from typing import Any


class GridWrapper(Wrapper):
    """Wrapper for rendering a volume grid with lines.

    Attributes
    ----------
    name : str
        Name of the line strings collection.
    lss_wrp : LineStringsWrapper
        LineStringWrapper for line strings.
    """

    name: str
    mls_wrp: MultiLineStringWrapper

    def __init__(self, name: str, grid: Grid, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        mls = self._create_grid_lines(grid)
        self.mls_wrp = MultiLineStringWrapper(name, mls, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mls_wrp is not None:
            self.mls_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])
        if self.mls_wrp is not None:
            vertex_pos = self.mls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _create_grid_lines(self, grid: Grid):
        """Draw the grid lines between the grid points."""
        coords_2d = grid.coordinates()
        coords_3d = np.hstack((coords_2d, np.zeros((coords_2d.shape[0], 1))))
        num_rows, num_cols = grid.height + 1, grid.width + 1
        count = num_rows * num_cols

        side_1 = coords_3d[0:num_cols, :]
        side_2 = coords_3d[count - (num_cols) : count, :]

        side_3 = coords_3d[0 : num_cols * num_rows : num_cols, :]
        side_4 = coords_3d[num_cols - 1 : count : num_cols, :]

        line_start = np.vstack((side_1, side_3))
        line_end = np.vstack((side_2, side_4))

        lines = zip(line_start, line_end)
        lss = [LineString(line) for line in lines]
        mls = MultiLineString(lss)
        return mls


class VolumeGridWrapper(Wrapper):
    """Wrapper for rendering a volume grid with lines.

    Attributes
    ----------
    name : str
        Name of the line strings collection.
    lss_wrp : LineStringsWrapper
        LineStringWrapper for line strings.
    """

    name: str
    mls_wrp: MultiLineStringWrapper

    def __init__(self, name: str, volume_grid: VolumeGrid, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        mls = self._create_grid_lines(volume_grid)
        self.mls_wrp = MultiLineStringWrapper(name, mls, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mls_wrp is not None:
            self.mls_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        if self.mls_wrp is not None:
            vertex_pos = self.mls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _create_grid_lines(self, grid: VolumeGrid):
        """Draw the grid lines between the grid points."""
        coords = grid.coordinates()

        nx = grid.width + 1
        ny = grid.height + 1
        nz = grid.depth + 1
        n_xz = nx * nz
        count = nx * ny * nz

        mask1 = np.zeros(n_xz, dtype=bool)
        mask1[0:nz] = True
        mask1 = np.tile(mask1, ny)

        mask2 = np.zeros(n_xz, dtype=bool)
        mask2[n_xz - nz : n_xz] = True
        mask2 = np.tile(mask2, ny)

        side_yz_1 = coords[mask1, :]
        side_yz_2 = coords[mask2, :]
        side_xz_1 = coords[0:n_xz:, :]
        side_xz_2 = coords[count - n_xz : count, :]
        side_xy_1 = coords[0 : count - (nz - 1) : nz, :]
        side_xy_2 = coords[nz - 1 : count : nz, :]

        line_start = np.vstack((side_yz_1, side_xz_1, side_xy_1))
        line_end = np.vstack((side_yz_2, side_xz_2, side_xy_2))

        lines = zip(line_start, line_end)
        lss = [LineString(line) for line in lines]
        mls = MultiLineString(lss)

        return mls
