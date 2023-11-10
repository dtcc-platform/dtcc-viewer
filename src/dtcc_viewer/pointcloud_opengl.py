import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper
from dtcc_viewer.opengl_viewer.pointcloud_wrapper import PointCloudWrapper
from dtcc_viewer.opengl_viewer.scene import Scene


def view(
    pc: PointCloud,
    size: float = 0.2,
    data: np.ndarray = None,
    colors: np.ndarray = None,
    mesh: Mesh = None,
    mesh_data: np.ndarray = None,
    mesh_colors: np.ndarray = None,
    mesh_shading: MeshShading = MeshShading.wireshaded,
):
    """
    View a point cloud in 3D with a GLFW window.

    This function is added to the PointCloud class in dtcc_model.

    Parameters
    ----------
    pc : PointCloud
        Point cloud to be viewed (self).
    data : np.ndarray
        Data for coloring of point cloud. Data should match point count.
    colors : np.ndarray
        Points colors [[r,g,b],[r,g,b]..]. Colors should number of points in pc.
    size : float
        Particle size in meters. Default value = 0.2 m
    mesh : Mesh
        Mesh to be viewed togheter with the point cloud.
    mesh_data : np.ndarray
        Data for coloring of mesh. Data should match vertex or face count.
    mesh_colors : np.ndarray
        Mesh colors [[r,g,b],[r,g,b]..]. Colors should match vertex or face count.
    """

    window = Window(1200, 800)
    scene = Scene()

    if mesh is None:
        scene.add_pointcloud("Point cloud", pc, size, data, colors)
        window.render(scene)
    else:
        scene.add_pointcloud("Point cloud", pc, size, data, colors)
        scene.add_mesh("Mesh", mesh, mesh_data, mesh_colors, mesh_shading)
        window.render(scene)
