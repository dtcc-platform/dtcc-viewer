import numpy as np

# from dtcc_model import Mesh, RoadNetwork
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.wrp_roadnetwork import RoadNetworkWrapper
from typing import Any


def view(
    roadnetwork: Any,
    data: np.ndarray = None,
):
    """View a roadnetwork in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    roadnetwork : RoadNetwork
        Road network to be viewed (self).
    data : np.ndarray
        Data for coloring of road network. Data should match vertex count.
    colors : np.ndarray
        Mesh colors [[r,g,b],[r,g,b]..]. Colors should match vertex or face count.
    """

    window = Window(1200, 800)
    scene = Scene()

    scene.add_roadnetwork("Road network", roadnetwork, data)
    window.render(scene)
