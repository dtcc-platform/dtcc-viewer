# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import sys
import os
from pprint import pp
from dtcc_viewer import * 
from dtcc_viewer.colors import color_maps
from dtcc_viewer.mesh import Viewer
from typing import List, Iterable
from dtcc_viewer import utils
import dtcc_viewer.mesh as mesh

import trimesh
import numpy as np
import copy


class TestViewer():

    file_name:str   
    city_mesh:trimesh

    def __init__(self):
        self.file_name = '../../../data/models/CitySurfaceL.stl'
        self.city_mesh = trimesh.load_mesh(self.file_name)

    def test_simplest(self):        
        viewer = Viewer()
        mesh.view(viewer, self.city_mesh)
        viewer.show()

    def test_simple(self):
        n_faces = len(self.city_mesh.faces)
        values = np.arange(n_faces) / n_faces 

        viewer = Viewer()
        mesh.view(viewer, self.city_mesh, values, "mono")
        viewer.show()
        
    def test_color_by_height(self):
        
        face_mid_pts = utils.calc_face_mid_points(self.city_mesh)
        [meshes, values] = utils.split_mesh_in_quadrants(self.city_mesh, face_mid_pts)

        viewer = Viewer()
        mesh.view(viewer, meshes[0], values[0], "rainbow")
        mesh.view(viewer, meshes[1], values[1], "warm")
        mesh.view(viewer, meshes[2], values[2], "mono")
        mesh.view(viewer, meshes[3], values[3], "cold")
        viewer.show()

        assert True  

    def test_color_by_distance_to_centre(self):
        
        face_mid_pts = utils.calc_face_mid_points(self.city_mesh)
        [meshes, values] = utils.split_mesh_in_quadrants(self.city_mesh, face_mid_pts)

        all_dist = []
        for m in meshes:
            mesh_face_mid_pts = utils.calc_face_mid_points(m)
            distance_to_centre = utils.calc_distance_to_centre(mesh_face_mid_pts)
            all_dist.append(distance_to_centre)
        
        viewer = Viewer()
        mesh.view(viewer, meshes[0], all_dist[0], "rainbow", min_val= 0, max_val= 100)
        mesh.view(viewer, meshes[1], all_dist[1], "rainbow", min_val= 0, max_val= 200)
        mesh.view(viewer, meshes[2], all_dist[2], "rainbow", min_val= 0, max_val= 300)
        mesh.view(viewer, meshes[3], all_dist[3], "rainbow", min_val= 0, max_val= 400)
        viewer.show()



if __name__ == '__main__':

    os.system('clear')
    print("-------- View test started from main function -------")

    test = TestViewer()
    test.test_simplest()
    test.test_color_by_height()
    test.test_color_by_distance_to_centre()
    #test.test_viewer()

    pass