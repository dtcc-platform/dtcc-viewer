from dtcc_model import PointCloud
import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from pprint import pp
from enum import Enum
import math
#from obj_loader import ObjLoader, import_point_cloud_from_txt
from opengl_viewer.camera import Camera

def view(pointcloud:PointCloud):
    pass