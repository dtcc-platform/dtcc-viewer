import numpy as np
from dtcc_model import Mesh
from dtcc_model import PointCloud
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData


def view(
    mesh: Mesh,
    mesh_data: np.ndarray = None,
    pc: PointCloud = None,
    pc_data: np.ndarray = None,
):
    """View a mesh in 3D with a GLFW window. This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    mesh : Mesh
        Mesh to be viewed (self).
    mesh_data : np.ndarray
        Data for coloring of mesh. Data should match vertex or face count.
    pc : PointCloud
        Point cloud to be viewed togheter with the mesh.
    p_data: np.ndarray
        Data for coloring of point cloud.
    """

    window = Window(1200, 800)

    if pc is None:
        [recenter_vec, bb] = calc_recenter_vector(mesh=mesh)
        mesh_data_obj = MeshData("Mesh View", mesh, mesh_data, recenter_vec, bb)
        window.render(mesh_data_obj=mesh_data_obj)
    else:
        [recenter_vec, bb] = calc_recenter_vector(mesh, pc)
        mesh_data_obj = MeshData("Mesh View", mesh, mesh_data, recenter_vec, bb)
        pc_data_obj = PointCloudData("Point Cloud View", pc, pc_data, recenter_vec, bb)
        window.render(mesh_data_obj=mesh_data_obj, pc_data_obj=pc_data_obj)
