import sys
from pprint import pp
from dtcc_viewer import * 
from dtcc_viewer.colors import color_maps
from dtcc_viewer.mesh import Viewer
from typing import List, Iterable
import dtcc_viewer.mesh as mesh
import trimesh
import pytest
import numpy as np
import copy


class TestViewer():

    file_name:str   
    city_mesh:trimesh

    def setup_method(self):
        self.file_name = 'data/models/CitySurfaceL.stl'
        self.city_mesh = trimesh.load_mesh(self.file_name)
        
    def test_color_by_height(self):
        
        face_mid_pts = calc_face_mid_points(self.city_mesh)
        [meshes, values] = split_mesh_in_quadrants(self.city_mesh, face_mid_pts)

        viewer = Viewer()
        mesh.view(viewer, meshes[0], values[0], "rainbow")
        mesh.view(viewer, meshes[1], values[1], "fire")
        mesh.view(viewer, meshes[2], values[2], "mono")
        mesh.view(viewer, meshes[3], values[3], "cold")
        viewer.show()

        assert True  

    def test_viewer(self):

        n_faces = len(self.city_mesh.faces)
        values = np.arange(n_faces) / n_faces 

        viewer = Viewer()
        mesh.view(viewer, self.city_mesh, values, "mono")
        viewer.show()

        pass


def calc_face_mid_points(mesh:trimesh):
    faceVertexIndex1 = mesh.faces[:,0]
    faceVertexIndex2 = mesh.faces[:,1]
    faceVertexIndex3 = mesh.faces[:,2] 
    vertex1 = np.array(mesh.vertices[faceVertexIndex1])
    vertex2 = np.array(mesh.vertices[faceVertexIndex2])
    vertex3 = np.array(mesh.vertices[faceVertexIndex3])
    face_mid_points = (vertex1 + vertex2 + vertex3) / 3.0
    return face_mid_points

def split_mesh_in_quadrants(mesh:trimesh, face_mid_pts:Iterable):
    
    meshes = []
    masks = []
    values = []

    masks.append([pt[0] < 0 and pt[1] < 0 for pt in face_mid_pts])
    masks.append([pt[0] > 0 and pt[1] < 0 for pt in face_mid_pts])
    masks.append([pt[0] > 0 and pt[1] > 0 for pt in face_mid_pts])
    masks.append([pt[0] < 0 and pt[1] > 0 for pt in face_mid_pts])

    for i in np.arange(4):
        mesh_q = copy.deepcopy(mesh)
        mesh_q.update_faces(masks[i])
        mesh_q.remove_unreferenced_vertices()

        face_mid_pts = calc_face_mid_points(mesh_q)
        face_mid_pt_z = face_mid_pts[:,2]
        values.append(face_mid_pt_z)
        meshes.append(mesh_q)
    
    return meshes, values


if __name__ == '__main__':

    test = TestViewer()
    test.setup_method()
    test.test_color_by_height()
    #test.test_viewer()

    pass