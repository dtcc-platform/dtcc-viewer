import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.scene import Scene


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
    scene = Scene()

    if mesh is None:
        pc = PointCloudData("Point cloud", pc, pc_data)
        scene.add_pointcloud(pc)
        window.render(scene)
    else:
        mesh = MeshData("Mesh", mesh, mesh_data)
        pc = PointCloudData("Point cloud", pc, pc_data)
        scene.add_mesh(mesh)
        scene.add_pointcloud(pc)
        window.render(scene)
