import glfw
import numpy as np
from dtcc_model import Mesh
from dtcc_viewer.opengl_viewer.window import Window
from pprint import pp

def view(mesh:Mesh):
    
    window = Window(1200, 800)

    # Resturcturing the mesh so that each face has its unique vertices with unique normals
    [vertices, face_indices, edge_indices] = restructure_mesh(mesh)

    vertices = normalise_colors(vertices)

    print("Num vertices:" + str(len(vertices)))
    print("Num faces:" + str(len(face_indices)))
    print("Num edges:" + str(len(edge_indices)))

    origin = np.array([0.0, 0.0, 0.0])
    vertices = move_to_origin(origin, vertices)
    
    # Making sure the datatypes are aligned with opengl implementation
    vertices = np.array(vertices, dtype= "float32").flatten()
    face_indices = np.array(face_indices, dtype= "uint32").flatten()
    edge_indices = np.array(edge_indices, dtype= "uint32").flatten()

    window.render_fancy_mesh(vertices, face_indices, edge_indices)


def restructure_mesh(mesh:Mesh):
    
    new_faces = []
    new_vertices = []
    new_edges = []
    v_index = 0

    for face in mesh.faces:

        v1 = mesh.vertices[face[0],:]
        v2 = mesh.vertices[face[1],:]
        v3 = mesh.vertices[face[2],:]

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


def normalise_colors(vertices:np.ndarray):

    vertices[:,3] /= 255
    vertices[:,4] /= 255
    vertices[:,5] /= 255
    
    return vertices


def move_to_origin(origin:np.ndarray, vertices:np.ndarray):

    xmin = vertices[:, 0].min()
    xmax = vertices[:, 0].max()
    ymin = vertices[:, 1].min()
    ymax = vertices[:, 1].max()
    zmin = vertices[:, 2].min()
    zmax = vertices[:, 2].max()

    x_avrg = (xmin + xmax)/2.0
    y_avrg = (ymin + ymax)/2.0
    z_avrg = (zmin + zmax)/2.0
    
    # x, y, z, r, g, b, nx, ny ,nz
    origin = np.array([origin[0], origin[1], origin[2], 0, 0, 0, 0, 0, 0])
    move_vec = origin - np.array([x_avrg, y_avrg, z_avrg, 0, 0, 0, 0, 0, 0])
    vertices += move_vec

    return vertices
