from dtcc_core.model import RoadNetwork
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene


def view(roadnetwork: RoadNetwork):
    """View a roadnetwork in 3D with a GLFW window.

    This function is added to the Roadnetwork class in dtcc_model.

    Parameters
    ----------
    roadnetwork : Roadnetwork
        Roadnetwork to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_roadnetwork("Roadnetwork", roadnetwork)
    window.render(scene)
