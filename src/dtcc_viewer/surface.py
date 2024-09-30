from dtcc_core.model import Surface
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene


def view(surface: Surface):
    """View a surface in 3D with a GLFW window.

    This function is added to the Surface class in dtcc_model.

    Parameters
    ----------
    surface : Surface
        Surface to be viewed (self).
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_surface("Surface", surface)
    window.render(scene)
