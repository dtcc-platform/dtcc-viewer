import numpy as np
from dtcc_model import Mesh, City
from dtcc_model import PointCloud
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(
    city: City,
    shading: Shading = Shading.wireshaded,
):
    """View a mesh in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    city : City
        City to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_city("City", city)
    window.render(scene)