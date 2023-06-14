
from pprint import pp
from dtcc_viewer import * 
from dtcc_model import Mesh, PointCloud
from dtcc_viewer.colors import *
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


# ------------------------------- Mesh Conversion functions ----------------------------------#

def generate_mesh_colors(mesh:Mesh, data:np.ndarray = None):

    n_vertex_colors = len(mesh.vertex_colors)
    n_face_colors = len(mesh.face_colors)    
    n_vertices = len(mesh.vertices)
    n_faces = len(mesh.faces)
    n_data = 0

    if data is not None:
        n_data = len(data)

    # If no vertex of face colors are appended to the mesh and no data is provided
    # the mesh is colored by vertex height.
    color_by = ColorBy.vertex_height
    default_data = mesh.vertices[:,2]
    colors = calc_colors_rainbow(default_data)

    if(data is None):
        if n_vertex_colors == n_vertices:
            color_by = ColorBy.vertex_colors
            colors = normalise_colors(mesh.vertex_colors)
        elif n_face_colors == n_faces:
            color_by = ColorBy.face_colors
            colors = normalise_colors(mesh.face_colors)       
    else: 
        if n_data == n_vertices:                #Generate colors base on provided vertex data
            color_by = ColorBy.vertex_data
            colors = calc_colors_rainbow(data)
        elif n_data == n_faces:                 #Generate colors base on provided face data
            color_by = ColorBy.face_data        
            colors = calc_colors_rainbow(data) 

    return color_by, np.array(colors) 

def normalise_colors(colors:np.ndarray):
    #If the max color value is larger then 1 it is assumed that the color range is 0-255
    max = np.max(colors)
    if(max > 1.0):
        colors /= 255.0
    return colors

def restructure_mesh(mesh:Mesh, color_by:ColorBy, colors:np.ndarray):
    
    # Vertex format that suits the opengl data structure:
    # x, y, z, r, g, b, nx, ny ,nz

    new_faces = []
    new_vertices = []
    new_edges = []
    v_index = 0
    white = [0.9, 0.9, 0.9]
    c1 = white
    c2 = white
    c3 = white

    for face_index, face in enumerate(mesh.faces):
        
        v1 = mesh.vertices[face[0], :]
        v2 = mesh.vertices[face[1], :]
        v3 = mesh.vertices[face[2], :]

        if color_by == ColorBy.vertex_colors or color_by == ColorBy.vertex_data or color_by == ColorBy.vertex_height:
            c1 = colors[face[0], 0:3]
            c2 = colors[face[1], 0:3]
            c3 = colors[face[2], 0:3]
        elif color_by == ColorBy.face_colors or color_by == ColorBy.face_data:    
            c1 = colors[face_index, 0:3]
            c2 = colors[face_index, 0:3]
            c3 = colors[face_index, 0:3]
   
        v1 = np.concatenate((v1, c1), axis=0)
        v2 = np.concatenate((v2, c2), axis=0)
        v3 = np.concatenate((v3, c3), axis=0)

        f_normal = np.cross(v2[0:3]-v1[0:3], v3[0:3]-v1[0:3])
        f_normal = f_normal / np.linalg.norm(f_normal)

        v1 = np.concatenate((v1, f_normal), axis=0)
        v2 = np.concatenate((v2, f_normal), axis=0)
        v3 = np.concatenate((v3, f_normal), axis=0)

        new_vertices.append(v1)
        new_vertices.append(v2)
        new_vertices.append(v3)

        new_faces.append([v_index, v_index+1, v_index+2])
        new_edges.append([v_index, v_index+1])
        new_edges.append([v_index+1, v_index+2])
        new_edges.append([v_index+2, v_index])
        
        v_index += 3

    return np.array(new_vertices), np.array(new_faces), np.array(new_edges)

def move_mesh_to_origin(vertices:np.ndarray, pc_avrg_pt:np.ndarray = None):
    # x, y, z, r, g, b, nx, ny ,nz    
    origin = np.array([0.0, 0.0, 0.0])
    origin_extended = np.array([origin[0], origin[1], origin[2], 0, 0, 0, 0, 0, 0])
    move_vec = 0
    mesh_avrg_pt = None

    if (pc_avrg_pt is None):
        x_avrg = (vertices[:, 0].min() + vertices[:, 0].max())/2.0
        y_avrg = (vertices[:, 1].min() + vertices[:, 1].max())/2.0
        z_avrg = (vertices[:, 2].min() + vertices[:, 2].max())/2.0
        mesh_avrg_pt = np.array([x_avrg, y_avrg, z_avrg])
        mesh_avrg_pt_extended = np.concatenate((mesh_avrg_pt,[0, 0, 0, 0, 0, 0]), axis=0) 
        move_vec = origin_extended - mesh_avrg_pt_extended
    else:
        pc_avrg_pt_extended = np.concatenate((pc_avrg_pt,[0, 0, 0, 0, 0, 0]), axis=0)
        move_vec = origin_extended - pc_avrg_pt_extended
        
    vertices += move_vec    

    return vertices, mesh_avrg_pt

def flatten_mesh(vertices:np.ndarray, face_indices:np.ndarray, edge_indices:np.ndarray):
    # Making sure the datatypes are aligned with opengl implementation
    vertices = np.array(vertices, dtype= "float32").flatten()
    edge_indices = np.array(edge_indices, dtype= "uint32").flatten()
    face_indices = np.array(face_indices, dtype= "uint32").flatten()

    return vertices, face_indices, edge_indices

# -------------------------------- Mesh Conversion Ended -------------------------------------#

# ------------------------- PointCloude Conversion functions ---------------------------------#

def generate_pc_colors(pc:PointCloud, pc_data:np.ndarray = None):
    colors = []
    if(pc_data is not None):
        if len(pc.points) == len(pc_data):   
            colors = calc_colors_rainbow(pc_data)
        else:
            z = pc.points[:,2]
            colors = calc_colors_rainbow(z)    
    else:
        z = pc.points[:,2]                  # Color by height if no data is provided
        colors = calc_colors_rainbow(z)         

    colors = np.array(colors)
    colors = colors[:,0:3]
    return colors

def restructure_pc(pc:PointCloud, pc_colors:np.ndarray):
    # Add color to the points
    #points_with_color = []
    #for point_index, point in enumerate(pc.points):
    #    new_point = np.concatenate((point, pc_colors[point_index, 0:3]), axis=0)
    #    points_with_color.append(new_point)
    #points_with_color = np.array(points_with_color)
    #return points_with_color
    points = pc.points
    return points, pc_colors

def move_pc_to_origin(points: np.ndarray, pc:PointCloud, mesh_avrg_pt:np.ndarray = None):
    origin = np.array([0.0 ,0.0 ,0.0])
    pc_avrg_pt = None
    if mesh_avrg_pt is None:
        pc.calculate_bounds()
        bounds = pc.bounds.tuple
        x_avrg = (bounds[0] + bounds[2])/2.0
        y_avrg = (bounds[1] + bounds[3])/2.0
        z_avrg = 0
        pc_avrg_pt = np.array([x_avrg, y_avrg, z_avrg])                
        move_vec = origin - pc_avrg_pt
    else:
        move_vec = origin - mesh_avrg_pt

    #Move the mesh to the centre of the model
    points += move_vec

    return points, pc_avrg_pt

def flatten_pc(points:np.ndarray, colors:np.ndarray):
    points = np.array(points, dtype='float32').flatten()
    colors = np.array(colors, dtype='float32').flatten()
    return points, colors

# --------------------------- PointCloude Conversion Ended ---------------------------------#



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