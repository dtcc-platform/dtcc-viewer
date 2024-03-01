import numpy as np
from dtcc_model import Object
from dtcc_model import PointCloud
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.scene import Scene
from typing import Any


def view(obj: Object):
    """View a generic object in 3D with a GLFW window.

    This function is added to the Object class in dtcc_model.

    Parameters
    ----------
    obj : Object
        Object to be viewed (self).
    shading : MeshShading
        Shading option for mesh drawing style.
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_object("Object", obj)
    window.render(scene)
