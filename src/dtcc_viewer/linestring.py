from dtcc_core.model import LineString
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene


def view(linestring: LineString):
    """View a LineString in 3D with a GLFW window.

    This function is added to the LineString class in dtcc_model.

    Parameters
    ----------
    linestring : LineString
        LineString to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_linestring("Linestring", linestring)
    window.render(scene)
