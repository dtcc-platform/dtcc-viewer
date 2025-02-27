import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString, Point, MultiLineString
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper, MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_lines import LinesWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_core.model import Grid, VolumeGrid
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
    lines_wrp: LinesWrapper

    def __init__(self, name: str, grid: Grid, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        vertices, indices = self._connect_grid_points(grid)
        data_dict = self._get_fields_data(grid)
        self.lines_wrp = LinesWrapper(name, vertices, indices, mts, data_dict)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.lines_wrp is not None:
            self.lines_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])
        if self.lines_wrp is not None:
            vertex_pos = self.lines_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _connect_grid_points(self, grid: Grid):
        """Connect the points in the grid with lines."""

        indices = []

        nx = grid.width + 1
        ny = grid.height + 1
        xmax = grid.bounds.xmax
        ymax = grid.bounds.ymax

        coords = grid.coordinates()
        n_coords = coords.shape[0]

        # Create indices for horizontal lines along x-axis
        idx_x1 = np.arange(n_coords)
        idx_x2 = idx_x1 + 1
        mask_x = np.logical_and(idx_x2 < n_coords, coords[idx_x1, 0] != xmax)

        # Create indices for horizontal lines along y-axis
        idx_y1 = np.arange(n_coords)
        idx_y2 = idx_y1 + nx
        mask_y = np.logical_and(idx_y2 < n_coords, coords[idx_y1, 1] != ymax)

        indices.extend(zip(idx_x1[mask_x], idx_x2[mask_x]))  # Lines along x-axis
        indices.extend(zip(idx_y1[mask_y], idx_y2[mask_y]))  # Lines along y-axis

        indices = np.array(indices, dtype="uint32")

        vertices = np.column_stack((coords, np.zeros(n_coords)))

        return vertices, indices

    def _get_fields_data(self, grid: Grid) -> dict:
        data_dict = {}
        for i, field in enumerate(grid.fields):
            if field.dim == 1:
                data_dict[field.name] = field.values
                info(f"Field {i} has been added to the data dictionary")
            elif field.dim != 1:
                warning("Viewer only supports scalar fields in current implementation")
                warning(f"Field '{field.name}' has dimension != 1. Skipping.")

        return data_dict


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
    lines_wrp: LinesWrapper

    def __init__(self, name: str, volume_grid: VolumeGrid, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        # mls = self._create_gridlines(volume_grid)
        vertices, indices = self._connect_grid_points(volume_grid)
        data_dict = self._get_fields_data(volume_grid)
        self.lines_wrp = LinesWrapper(name, vertices, indices, mts, data_dict)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.lines_wrp is not None:
            self.lines_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        if self.lines_wrp is not None:
            vertex_pos = self.lines_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _connect_grid_points(self, volume_grid: VolumeGrid):
        """Connect the points in the grid with lines."""

        indices = []
        coords = volume_grid.coordinates()

        nx = volume_grid.width + 1
        ny = volume_grid.height + 1
        nz = volume_grid.depth + 1

        xmax = volume_grid.bounds.xmax
        ymax = volume_grid.bounds.ymax
        zmax = volume_grid.bounds.zmax

        # Generate indices for horizontal lines along x-axis
        idx_x1 = np.arange(coords.shape[0])
        idx_x2 = idx_x1 + nz
        mask_x = np.logical_and(idx_x2 < coords.shape[0], coords[idx_x1, 0] != xmax)

        # Generate indices for horizontal lines along y-axis
        idx_y1 = np.arange(coords.shape[0])
        idx_y2 = idx_y1 + nx * nz
        mask_y = np.logical_and(idx_y2 < coords.shape[0], coords[idx_y1, 1] != ymax)

        # Generate indices for horizontal lines along z-axis
        idx_z1 = np.arange(coords.shape[0])
        idx_z2 = idx_z1 + 1
        mask_z = np.logical_and(idx_z2 < coords.shape[0], coords[idx_z1, 2] != zmax)

        indices.extend(zip(idx_x1[mask_x], idx_x2[mask_x]))  # Lines along x-axis
        indices.extend(zip(idx_y1[mask_y], idx_y2[mask_y]))  # Lines along y-axis
        indices.extend(zip(idx_z1[mask_z], idx_z2[mask_z]))  # Lines along z-axis

        indices = np.array(indices, dtype="uint32")
        return coords, indices

    def _get_fields_data(self, volume_grid: VolumeGrid) -> dict:
        data_dict = {}
        for i, field in enumerate(volume_grid.fields):
            if field.dim == 1:
                data_dict[field.name] = field.values
                info(f"Field called {field.name} has been added to the data dictionary")
            elif field.dim != 1:
                warning("Viewer only supports scalar fields in current implementation")
                warning(f"Field '{field.name}' has dimension != 1. Skipping.")
        return data_dict
