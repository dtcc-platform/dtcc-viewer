import numpy as np
from dtcc_model import Mesh, RoadNetwork
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.scene import Scene
from dtcc_viewer.opengl_viewer.roadnetwork_data import RoadNetworkData


def view(
    roadnetwork: RoadNetwork,
    data: np.ndarray = None,
    colors: np.ndarray = None,
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

    scene.add_roadnetwork("Road network", roadnetwork, data, colors)
    window.render(scene)
