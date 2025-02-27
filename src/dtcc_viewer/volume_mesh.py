from dtcc_core.model import VolumeMesh
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(volume_mesh: VolumeMesh):
    """View a mesh in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    city : City
        City to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_volume_mesh("VolumeMesh", volume_mesh)
    window.render(scene)
