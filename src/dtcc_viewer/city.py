from dtcc_core.model import City
from dtcc_viewer.opengl.utils import Shading
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.logging import debug
from typing import Any

from time import time
import sys


def view(city: City):
    """View a mesh in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    city : City
        City to be viewed (self).
    """
    start_time = time()
    window = Window(1200, 800)
    scene = Scene()
    scene.add_city("City", city)
    debug(f"Adding city took {time() - start_time} seconds")
    window.render(scene)
