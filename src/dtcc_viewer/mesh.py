import numpy as np
from dtcc_core.model import Mesh
from dtcc_viewer.opengl.utils import Shading
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(mesh: Mesh, data: Any = None):
    """View a mesh in 3D with a GLFW window.

    This function is added to the Mesh class in dtcc_model.

    Parameters
    ----------
    mesh : Mesh
        Mesh to be viewed (self).
    data : np.ndarray
        Data for coloring of mesh. Data should match vertex or face count.
    shading : MeshShading
        Shading option for mesh drawing style.
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_mesh("Mesh", mesh, data)
    window.render(scene)
