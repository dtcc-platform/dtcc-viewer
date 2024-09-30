from dtcc_core.model import MultiLineString
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene


def view(multilinestring: MultiLineString):
    """View a MultiLineString in 3D with a GLFW window.

    This function is added to the MultiLineString class in dtcc_model.

    Parameters
    ----------
    multilinestring : MultiLineString
        MultiLineString to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_multilinestring("Multilinestring", multilinestring)
    window.render(scene)
