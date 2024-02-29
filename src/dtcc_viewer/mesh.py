import numpy as np
from dtcc_model import Mesh
from dtcc_model import PointCloud
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(
    mesh: Mesh,
    data: Any = None,
    shading: Shading = Shading.wireshaded,
    pc: PointCloud = None,
    pc_data: np.ndarray = None,
    pc_size: float = 0.2,
):
    """View a mesh in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    mesh : Mesh
        Mesh to be viewed (self).
    data : np.ndarray
        Data for coloring of mesh. Data should match vertex or face count.
    colors : np.ndarray
        Mesh colors [[r,g,b],[r,g,b]..]. Colors should match vertex or face count.
    pc : PointCloud
        Point cloud to be viewed togheter with the mesh.
    pc_data: np.ndarray
        Data for coloring of point cloud.
    pc_colors : np.ndarray
        Points colors [[r,g,b],[r,g,b]..]. Colors should number of points in pc.

    """

    window = Window(1200, 800)
    scene = Scene()

    if pc is None:
        scene.add_mesh("Mesh", mesh, data, shading)
        window.render(scene)
    else:
        scene.add_mesh("Mesh", mesh, data, shading)
        scene.add_pointcloud("Point cloud", pc, pc_size, pc_data)
        window.render(scene)
