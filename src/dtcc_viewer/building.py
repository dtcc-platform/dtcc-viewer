from dtcc_model import Building
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(building: Building):
    """View a mesh in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    city : City
        City to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_building("Building", building)
    window.render(scene)