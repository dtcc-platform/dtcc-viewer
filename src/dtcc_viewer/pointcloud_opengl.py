import glfw
import numpy as np
from dtcc_model import PointCloud, Bounds, Mesh
from dtcc_viewer.opengl_viewer.window import Window


def view(pc:PointCloud, mesh:Mesh = None):
    
    window = Window(1200, 800)
    points = pre_process(pc)
    window.render_particles(points)

def pre_process(pc:PointCloud):

    pc.calculate_bounds()
    points = pc.points
    bounds = pc.bounds.tuple

    origin = np.array([0.0 ,0.0 ,0.0])
    points = move_to_origin(origin, points, bounds)
    points = np.array(points, dtype='float32').flatten()

    return points


def move_to_origin(origin:np.ndarray, points: np.ndarray, bounds:Bounds):

    x_avrg = (bounds[0] + bounds[2])/2.0
    y_avrg = (bounds[1] + bounds[3])/2.0
    
    origin = np.array([0.0, 0.0, 0.0])

    #Center mesh based on x and y coordinates only
    centerVec = origin - np.array([x_avrg, y_avrg, 0])

    #Move the mesh to the centre of the model
    points += centerVec

    return points

