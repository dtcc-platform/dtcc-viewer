
from pprint import pp
from dtcc_viewer import * 
from dtcc_model import Mesh
from typing import List, Iterable
import trimesh
import numpy as np
import copy
from enum import Enum

class ColorBy(Enum):
    vertex_colors = 2
    vertex_data = 1
    face_colors = 3
    face_data = 4
    vertex_height = 5

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


def calc_distance_to_centre(face_mid_pts:Iterable):
    n = len(face_mid_pts)
    average_x = np.sum(face_mid_pts[:,0]) / n
    average_y = np.sum(face_mid_pts[:,1]) / n
    average_z = np.sum(face_mid_pts[:,2]) / n
    mesh_mid_pt = np.array([average_x, average_y, average_z])
    dist = np.sqrt(np.sum((face_mid_pts-mesh_mid_pt)**2,axis=1))  
    return dist