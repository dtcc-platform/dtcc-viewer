# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
from pprint import pp
from dtcc_viewer import * 
from dtcc_viewer.colors import color_maps
from dtcc_viewer.mesh_pyglet import Viewer
from typing import List, Iterable
from dtcc_viewer import utils
import dtcc_viewer.mesh_pyglet as mesh_pyglet

from dtcc_io import pointcloud as pc

from dtcc_viewer import pointcloud_opengl

import trimesh
import numpy as np


class ViewerExamples():

    file_name:str   
    city_mesh:trimesh

    def __init__(self):
        self.file_name = '../../../data/models/CitySurfaceL.stl'
        self.city_mesh = trimesh.load_mesh(self.file_name)

    def example_simplest(self):        
        viewer = Viewer()
        mesh_pyglet.view(viewer, self.city_mesh)
        viewer.show()

    def example_simple(self):
        n_faces = len(self.city_mesh.faces)
        values = np.arange(n_faces) / n_faces 

        viewer = Viewer()
        mesh_pyglet.view(viewer, self.city_mesh, values, "rainbow")
        viewer.show()
        
    def example_color_by_height(self):
        
        face_mid_pts = utils.calc_face_mid_points(self.city_mesh)
        [meshes, values] = utils.split_mesh_in_quadrants(self.city_mesh, face_mid_pts)

        viewer = Viewer()
        mesh_pyglet.view(viewer, meshes[0], values[0], "rainbow")
        mesh_pyglet.view(viewer, meshes[1], values[1], "warm")
        mesh_pyglet.view(viewer, meshes[2], values[2], "mono")
        mesh_pyglet.view(viewer, meshes[3], values[3], "cold")
        viewer.show()

        assert True  

    def example_color_by_distance_to_centre(self):
        
        face_mid_pts = utils.calc_face_mid_points(self.city_mesh)
        [meshes, values] = utils.split_mesh_in_quadrants(self.city_mesh, face_mid_pts)

        all_dist = []
        for m in meshes:
            mesh_face_mid_pts = utils.calc_face_mid_points(m)
            distance_to_centre = utils.calc_distance_to_centre(mesh_face_mid_pts)
            all_dist.append(distance_to_centre)
        
        viewer = Viewer()
        mesh_pyglet.view(viewer, meshes[0], all_dist[0], "rainbow", min_val= 0, max_val= 100)
        mesh_pyglet.view(viewer, meshes[1], all_dist[1], "rainbow", min_val= 0, max_val= 200)
        mesh_pyglet.view(viewer, meshes[2], all_dist[2], "rainbow", min_val= 0, max_val= 300)
        mesh_pyglet.view(viewer, meshes[3], all_dist[3], "rainbow", min_val= 0, max_val= 400)
        viewer.show()



if __name__ == '__main__':

    os.system('clear')
    print("-------- View test started from main function -------")

    test = ViewerExamples()
    #test.example_simplest()
    #test.example_simple()
    #test.example_color_by_height()
    test.example_color_by_distance_to_centre()

    