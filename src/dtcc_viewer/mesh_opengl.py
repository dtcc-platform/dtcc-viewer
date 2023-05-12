import glfw
import numpy as np
from dtcc_model import Mesh
from dtcc_viewer.opengl_viewer.window import Window


def view(mesh:Mesh):
    
    window = Window(1200, 800)
    origin = np.array([0.0, 0.0, 0.0])
    vertices = move_to_origin(origin, mesh.vertices)
    vertices = normalise_colors(vertices) 
    edge_indices = create_edge_vertices(mesh)
    face_indices = mesh.faces

    # Making sure the datatypes are aligned with opengl implementation
    vertices = np.array(vertices, dtype= "float32").flatten()
    face_indices = np.array(face_indices, dtype= "uint32").flatten()
    edge_indices = np.array(edge_indices, dtype= "uint32").flatten()

    window.render_mesh(vertices, face_indices, edge_indices)


def create_edge_vertices(mesh:Mesh):
    edge_indices = []
    for face in mesh.faces:
        edge_indices.append([face[0], face[1], face[2], face[0]])

    edge_indices = np.array(edge_indices, dtype='uint32')

    return edge_indices


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
    
    # x,y,z,r,g,b
    origin = np.array([origin[0], origin[1], origin[2], 0, 0, 0])
    move_vec = origin - np.array([x_avrg, y_avrg, z_avrg, 0, 0, 0])
    vertices += move_vec

    return vertices


def normalise_colors(vertices:np.ndarray):

    vertices[:,3] /= 255
    vertices[:,4] /= 255
    vertices[:,5] /= 255
    
    return vertices