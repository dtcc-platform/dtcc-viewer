from dtcc_core.model import RoadNetwork
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene


def view(roadnetwork: RoadNetwork, road_width: float = 6.0, z_offset: float = 0.05):
    """View a roadnetwork in 3D with a GLFW window.

    This function is added to the Roadnetwork class in dtcc_model.

    Parameters
    ----------
    roadnetwork : Roadnetwork
        Roadnetwork to be viewed (self).
    road_width : float, default 6.0
        Rendered road ribbon width in model units.
    z_offset : float, default 0.05
        Small vertical offset for road ribbons to avoid z-fighting.
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_roadnetwork(
        "Roadnetwork", roadnetwork, road_width=road_width, z_offset=z_offset
    )
    window.render(scene)
