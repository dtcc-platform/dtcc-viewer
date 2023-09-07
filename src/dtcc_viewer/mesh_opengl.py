import numpy as np
from dtcc_model import Mesh
from dtcc_model import PointCloud
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.scene import Scene


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
    scene = Scene()

    if pc is None:
        mesh = MeshData("Mesh", mesh, mesh_data)
        scene.add_mesh(mesh)
        window.render(scene)
    else:
        mesh = MeshData("Mesh", mesh, mesh_data)
        pc = PointCloudData("Point cloud", pc, pc_data)
        scene.add_mesh(mesh)
        scene.add_pointcloud(pc)
        window.render(scene)
