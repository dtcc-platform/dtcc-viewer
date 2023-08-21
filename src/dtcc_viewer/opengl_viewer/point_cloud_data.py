import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *


class PointCloudData:
    points: np.ndarray  # [n_points x 3]
    colors: np.ndarray  # [n_points x 3]
    pc_avrg_pt: np.ndarray  # [1 x 3]
    name: str

    def __init__(
        self, name: str, pc: PointCloud, pc_data: np.ndarray, recenter_vec: np.ndarray
    ) -> None:
        self.name = name
        self.colors = self.generate_pc_colors(pc, pc_data)  # TODO: Move functions here
        [self.points, self.colors] = self.restructure_pc(pc, self.colors)
        self.points = self.move_pc_to_origin_multi(self.points, recenter_vec)
        [self.points, self.colors] = self.flatten_pc(self.points, self.colors)

    def generate_pc_colors(self, pc: PointCloud, pc_data: np.ndarray = None):
        colors = []
        if pc_data is not None:
            if len(pc.points) == len(pc_data):
                colors = calc_colors_rainbow(pc_data)
            else:
                print("WARNING: Provided color data does not match the particle count!")
                print("Default colors are used instead -> i.e. coloring per z-value")
                z = pc.points[:, 2]
                colors = calc_colors_rainbow(z)
        else:
            print("No data provided for point cloud -> colors are set based on z-value")
            z = pc.points[:, 2]  # Color by height if no data is provided
            colors = calc_colors_rainbow(z)

        colors = np.array(colors)
        colors = colors[:, 0:3]
        return colors

    def restructure_pc(self, pc: PointCloud, pc_colors: np.ndarray):
        # Add color to the points
        # points_with_color = []
        # for point_index, point in enumerate(pc.points):
        #    new_point = np.concatenate((point, pc_colors[point_index, 0:3]), axis=0)
        #    points_with_color.append(new_point)
        # points_with_color = np.array(points_with_color)
        # return points_with_color
        points = pc.points
        return points, pc_colors

    def move_pc_to_origin(
        self, points: np.ndarray, pc: PointCloud, mesh_avrg_pt: np.ndarray = None
    ):
        origin = np.array([0.0, 0.0, 0.0])
        pc_avrg_pt = None
        if mesh_avrg_pt is None:
            pc.calculate_bounds()
            bounds = pc.bounds.tuple
            x_avrg = (bounds[0] + bounds[2]) / 2.0
            y_avrg = (bounds[1] + bounds[3]) / 2.0
            z_avrg = 0
            pc_avrg_pt = np.array([x_avrg, y_avrg, z_avrg])
            move_vec = origin - pc_avrg_pt
        else:
            move_vec = origin - mesh_avrg_pt

        # Move the mesh to the centre of the model
        points += move_vec

        return points, pc_avrg_pt

    def move_pc_to_origin_multi(
        self, points: np.ndarray, recenter_vec: np.ndarray = None
    ):
        if recenter_vec is not None:
            points += recenter_vec

        return points

    def flatten_pc(self, points: np.ndarray, colors: np.ndarray):
        points = np.array(points, dtype="float32").flatten()
        colors = np.array(colors, dtype="float32").flatten()
        return points, colors
