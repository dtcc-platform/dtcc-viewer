from dtcc_core.model import DeSO
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.window import Window


def view(deso: DeSO):
    """View DeSO statistical areas in 3D with a GLFW window."""

    window = Window(1200, 800)
    scene = Scene()
    scene.add_deso("DeSO", deso)
    window.render(scene)
