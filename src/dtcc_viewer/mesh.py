import pyglet
import trimesh
import numpy as np
from typing import List, Any, Iterable
#import dtcc_model as model
from dtcc_viewer.colors import color_maps


class Viewer:

    def __init__(self):        
        self.scene = trimesh.Scene()
        self.scene.camera._fov = [35,35]     #Field of view [x, y]
        self.scene.camera.z_far = 10000      #Distance to the far clipping plane        

    def add_meshes(self, meshes):
        self.scene.add_geometry(meshes)       

    def show(self):
        self.scene.show()   

def view(viewer: Viewer, mesh: trimesh, values: Iterable[float], color_map_key: str, min_val = None, max_val = None):

    color_map_function = color_maps[color_map_key]        
    colors = color_map_function(values, min_val, max_val)

    if len(mesh.faces) == len(colors):
        mesh.visual.face_colors = colors
    elif len(mesh.vertices) == len(colors):
        mesh.visual.vertice_colors = colors

    viewer.add_meshes(mesh)    

