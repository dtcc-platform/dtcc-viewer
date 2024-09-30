import numpy as np
from dtcc_core.model import PointCloud
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene


def view(pc: PointCloud, size: float = 0.2, data: np.ndarray = None):
    """
    View a point cloud in 3D with a GLFW window.

    This function is added to the PointCloud class in dtcc_model.

    Parameters
    ----------
    pc : PointCloud
        Point cloud to be viewed (self).
    data : np.ndarray
        Data for coloring of point cloud. Data should match point count.
    size : float
        Particle size in meters. Default value = 0.2 m.
    """

    window = Window(1200, 800)
    scene = Scene()
    scene.add_pointcloud("Point cloud", pc, size, data)
    window.render(scene)
