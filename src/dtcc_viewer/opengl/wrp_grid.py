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
        mls = self._create_gridlines(grid)
        mls, indices = self._connect_grid_points_2(grid)
        data_dict = self._get_fields_data(grid, indices)
        self.mls_wrp = MultiLineStringWrapper(name, mls, mts, data_dict)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mls_wrp is not None:
            self.mls_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])
        if self.mls_wrp is not None:
            vertex_pos = self.mls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _create_gridlines(self, grid: Grid) -> MultiLineString:
        """Create gridlines for a Grid object using LineStrings."""

        lss = []

        # Horizontal lines
        for i in range(grid.height + 1):
            x_vals = np.linspace(grid.bounds.xmin, grid.bounds.xmax, grid.width + 1)
            y_vals = np.repeat(
                np.linspace(grid.bounds.ymin, grid.bounds.ymax, grid.height + 1)[i],
                grid.width + 1,
            )
            points = [(x, y, 0) for x, y in zip(x_vals, y_vals)]
            lss.append(LineString(points))

        # Vertical lines
        for i in range(grid.width + 1):
            x_vals = np.repeat(
                np.linspace(grid.bounds.xmin, grid.bounds.xmax, grid.width + 1)[i],
                grid.height + 1,
            )
            y_vals = np.linspace(grid.bounds.ymin, grid.bounds.ymax, grid.height + 1)
            points = [(x, y, 0) for x, y in zip(x_vals, y_vals)]
            lss.append(LineString(points))

        mls = MultiLineString(lss)

        return mls

    def _connect_grid_points(self, grid: Grid):
        """Connect the points in the grid with lines."""
        lss = []
        indices = []

        nx = grid.width + 1
        ny = grid.height + 1

        xmax = grid.bounds.xmax
        ymax = grid.bounds.ymax

        coords = grid.coordinates()
        n_coords = coords.shape[0]

        # Horizontal lines (along x-axis)
        for i in range(n_coords):
            index1 = i
            index2 = i + 1
            x_coord = coords[index1, 0]
            if index2 < n_coords and x_coord != xmax:
                pt1 = [coords[index1, 0], coords[index1, 1], 0.0]
                pt2 = [coords[index2, 0], coords[index2, 1], 0.0]
                points = [pt1, pt2]
                indices.append([index1, index2])
                lss.append(LineString(points))

        # Horizontal lines (along y-axis)
        for i in range(n_coords):
            index1 = i
            index2 = i + nx
            y_coord = coords[index1, 1]
            if index2 < n_coords and y_coord != ymax:
                pt1 = [coords[index1, 0], coords[index1, 1], 0.0]
                pt2 = [coords[index2, 0], coords[index2, 1], 0.0]
                points = [pt1, pt2]
                indices.append([index1, index2])
                lss.append(LineString(points))

        indices = np.array(indices, dtype="uint32").flatten()
        mls = MultiLineString(lss)

        return mls, indices

    def _connect_grid_points_2(self, grid: Grid):
        """Connect the points in the grid with lines."""
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
        idx_x1 = idx_x1[mask_x]
        idx_x2 = idx_x2[mask_x]

        # Create indices for horizontal lines along y-axis
        idx_y1 = np.arange(n_coords)
        idx_y2 = idx_y1 + nx
        mask_y = np.logical_and(idx_y2 < n_coords, coords[idx_y1, 1] != ymax)
        idx_y1 = idx_y1[mask_y]
        idx_y2 = idx_y2[mask_y]

        # Create LineStrings for horizontal lines along x-axis
        points_x1 = np.column_stack(
            (coords[idx_x1, 0], coords[idx_x1, 1], np.zeros_like(idx_x1))
        )
        points_x2 = np.column_stack(
            (coords[idx_x2, 0], coords[idx_x2, 1], np.zeros_like(idx_x2))
        )
        lss_x = [LineString([pt1, pt2]) for pt1, pt2 in zip(points_x1, points_x2)]

        # Create LineStrings for horizontal lines along y-axis
        points_y1 = np.column_stack(
            (coords[idx_y1, 0], coords[idx_y1, 1], np.zeros_like(idx_y1))
        )
        points_y2 = np.column_stack(
            (coords[idx_y2, 0], coords[idx_y2, 1], np.zeros_like(idx_y2))
        )
        lss_y = [LineString([pt1, pt2]) for pt1, pt2 in zip(points_y1, points_y2)]

        # Combine LineStrings
        lss = lss_x + lss_y
        indices = np.column_stack((idx_x1, idx_x2, idx_y1, idx_y2)).flatten()

        mls = MultiLineString(lss)
        return mls, indices

    def _get_fields_data(self, grid: Grid, indices: np.ndarray) -> dict:

        data_dict = {}
        for i, field in enumerate(grid.fields):

            if max(indices) >= len(field.values):
                warning(f"Field {i} has less values than the grid")
                continue
            else:
                data_dict[f"field {i}"] = field.values[indices]
                info(f"Field {i} has been added to the data dictionary")

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
    mls_wrp: MultiLineStringWrapper

    def __init__(self, name: str, volume_grid: VolumeGrid, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name
        # mls = self._create_gridlines(volume_grid)
        mls, indices = self._connect_grid_points_2(volume_grid)
        data_dict = self._get_fields_data(volume_grid, indices)
        self.mls_wrp = MultiLineStringWrapper(name, mls, mts, data_dict)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mls_wrp is not None:
            self.mls_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        if self.mls_wrp is not None:
            vertex_pos = self.mls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _create_gridlines(self, grid: VolumeGrid) -> MultiLineString:
        """Create gridlines for a 3D VolumeGrid object using LineStrings."""
        lss = []
        # Horizontal lines (along y-z plane)
        for i in range(grid.height + 1):
            for j in range(grid.depth + 1):
                x_vals = np.linspace(grid.bounds.xmin, grid.bounds.xmax, grid.width + 1)
                y_val = grid.bounds.ymin + i * grid.ystep
                z_val = grid.bounds.zmin + j * grid.zstep
                points = [(x, y_val, z_val) for x in x_vals]
                lss.append(LineString(points))

        # Vertical lines (along x-z plane)
        for i in range(grid.width + 1):
            for j in range(grid.depth + 1):
                x_val = grid.bounds.xmin + i * grid.xstep
                y_vals = np.linspace(
                    grid.bounds.ymin, grid.bounds.ymax, grid.height + 1
                )
                z_val = grid.bounds.zmin + j * grid.zstep
                points = [(x_val, y, z_val) for y in y_vals]
                lss.append(LineString(points))

        # Depth lines (along x-y plane)
        for i in range(grid.width + 1):
            for j in range(grid.height + 1):
                x_val = grid.bounds.xmin + i * grid.xstep
                y_val = grid.bounds.ymin + j * grid.ystep
                z_vals = np.linspace(grid.bounds.zmin, grid.bounds.zmax, grid.depth + 1)
                points = [(x_val, y_val, z) for z in z_vals]
                lss.append(LineString(points))

        mls = MultiLineString(lss)

        return mls

    def _connect_grid_points(self, volume_grid: VolumeGrid):
        """Connect the points in the grid with lines."""
        lss = []
        indices = []

        nx = volume_grid.width + 1
        nz = volume_grid.depth + 1

        xmax = volume_grid.bounds.xmax
        ymax = volume_grid.bounds.ymax
        zmax = volume_grid.bounds.zmax

        coords = volume_grid.coordinates()
        n_coords = coords.shape[0]

        # Horizontal lines (along x axis)
        for i in range(n_coords):
            index1 = i
            index2 = i + nz
            x_coord = coords[index1, 0]
            if index2 < n_coords and x_coord != xmax:
                points = [coords[index1], coords[index2]]
                indices.append([index1, index2])
                lss.append(LineString(points))

        # Horizontal lines (along x axis)
        for i in range(n_coords):
            index1 = i
            index2 = i + nx * nz
            y_coord = coords[index1, 1]
            if index2 < n_coords and y_coord != ymax:
                points = [coords[index1], coords[index2]]
                indices.append([index1, index2])
                lss.append(LineString(points))

        # Horizontal lines (along x axis)
        for i in range(n_coords):
            index1 = i
            index2 = i + 1
            z_coord = coords[index1, 2]
            if index2 < n_coords and z_coord != zmax:
                points = [coords[index1], coords[index2]]
                indices.append([index1, index2])
                lss.append(LineString(points))

        mls = MultiLineString(lss)
        indices = np.array(indices, dtype="uint32").flatten()
        return mls, indices

    def _connect_grid_points_2(self, volume_grid: VolumeGrid):
        """Connect the points in the grid with lines."""
        lss = []
        indices = []

        coords = volume_grid.coordinates()

        nx = volume_grid.width + 1
        ny = volume_grid.height + 1
        nz = volume_grid.depth + 1

        # Generate indices for horizontal lines along x-axis
        idx_x1 = np.arange(coords.shape[0])
        idx_x2 = idx_x1 + nz
        mask_x = np.logical_and(
            idx_x2 < coords.shape[0], coords[idx_x1, 0] != volume_grid.bounds.xmax
        )

        # Generate indices for horizontal lines along y-axis
        idx_y1 = np.arange(coords.shape[0])
        idx_y2 = idx_y1 + nx * nz
        mask_y = np.logical_and(
            idx_y2 < coords.shape[0], coords[idx_y1, 1] != volume_grid.bounds.ymax
        )

        # Generate indices for horizontal lines along z-axis
        idx_z1 = np.arange(coords.shape[0])
        idx_z2 = idx_z1 + 1
        mask_z = np.logical_and(
            idx_z2 < coords.shape[0], coords[idx_z1, 2] != volume_grid.bounds.zmax
        )

        # Create LineStrings for horizontal lines along x-axis
        points_x = np.column_stack((coords[idx_x1[mask_x]], coords[idx_x2[mask_x]]))

        lss.extend(LineString([points[0:3], points[3:6]]) for points in points_x)
        indices.extend(zip(idx_x1[mask_x], idx_x2[mask_x]))

        # Create LineStrings for horizontal lines along y-axis
        points_y = np.column_stack((coords[idx_y1[mask_y]], coords[idx_y2[mask_y]]))
        lss.extend(LineString([points[0:3], points[3:6]]) for points in points_y)
        indices.extend(zip(idx_y1[mask_y], idx_y2[mask_y]))

        # Create LineStrings for horizontal lines along z-axis
        points_z = np.column_stack((coords[idx_z1[mask_z]], coords[idx_z2[mask_z]]))
        lss.extend(LineString([points[0:3], points[3:6]]) for points in points_z)
        indices.extend(zip(idx_z1[mask_z], idx_z2[mask_z]))

        mls = MultiLineString(lss)
        indices = np.array(indices, dtype="uint32").flatten()
        return mls, indices

    def _get_fields_data(self, volume_grid: VolumeGrid, indices: np.ndarray) -> dict:

        data_dict = {}
        for i, field in enumerate(volume_grid.fields):
            if max(indices) >= len(field.values):
                warning(f"Field {i} has less values than the grid")
                continue
            else:
                data_dict[f"field {i}"] = field.values[indices]
                info(f"Field {i} has been added to the data dictionary")

        return data_dict
