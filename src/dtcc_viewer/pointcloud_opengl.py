import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData


def view(
    pc: PointCloud,
    pc_data: np.ndarray = None,
    mesh: Mesh = None,
    mesh_data: np.ndarray = None,
):
    """
    View a point cloud in 3D with a GLFW window. This function is added to the PointCloud class in dtcc_model.

    Parameters
    ----------
    pc : PointCloud
        Point cloud to be viewed (self).
    pc_data : np.ndarray
        Data for coloring of point cloud. Data should match point count.
    mesh : Mesh
        Mesh to be viewed togheter with the point cloud.
    mesh_data : np.ndarray
        Data for coloring of mesh. Data should match vertex or face count.
    """

    window = Window(1200, 800)

    if mesh is None:
        recenter_vec = calc_recenter_vector(pc=pc)
        pc_data_obj = PointCloudData("Point Cloud View", pc, pc_data, recenter_vec, 0.2)
        window.render(pc_data_obj=pc_data_obj)
    else:
        recenter_vec = calc_recenter_vector(mesh, pc)
        mesh_data_obj = MeshData("Mesh View", mesh, mesh_data, recenter_vec)
        pc_data_obj = PointCloudData("Point Cloud View", pc, pc_data, recenter_vec, 0.2)
        window.render(pc_data_obj=pc_data_obj, mesh_data_obj=mesh_data_obj)
