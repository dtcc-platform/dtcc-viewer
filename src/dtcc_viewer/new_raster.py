from dtcc_core.model import Raster
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(raster: Raster):
    """View a raster in 3D with a GLFW window.

    Parameters
    ----------
    raster : Raster
        Raster to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_raster("Raster", raster)
    window.render(scene)
