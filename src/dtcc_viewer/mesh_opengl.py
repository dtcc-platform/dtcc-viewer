import glfw
import numpy as np
from dtcc_model import Mesh
from dtcc_model import PointCloud, Bounds
from dtcc_viewer.utils import ColorBy
from dtcc_viewer.colors import calc_colors_rainbow
from dtcc_viewer.opengl_viewer.window import Window
from pprint import pp

def view(mesh:Mesh, mesh_data:np.ndarray = None, pointcloud:PointCloud = None):
    
    origin = np.array([0.0, 0.0, 0.0])

    window = Window(1200, 800)

    # color vertices based on the data provided or stored in the mesh object.
    [color_by, colors] = generate_mesh_colors(mesh, mesh_data)

    # restructuring the mesh so that each face has its unique vertices with unique normals
    [vertices, face_indices, edge_indices] = restructure_mesh(mesh, color_by, colors)

    # move mesh and pointcloude to origin
    [vertices, points] = move_to_origin(origin, vertices, pointcloud)

    # flatten data
    [vertices, edge_indices, face_indices, points] = flatten(vertices, edge_indices, face_indices, points)    
    
    if(points is None):
        window.render_mesh(vertices, face_indices, edge_indices)
    else:
        window.render_particles_and_mesh(points, vertices, face_indices, edge_indices)    

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
    #If the average color value is larger then 1 it is assumed that the color range is 0-255
    averag = np.average(colors)
    if(averag > 1.0):
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

    for face_counter, face in enumerate(mesh.faces):
        
        v1 = mesh.vertices[face[0], :]
        v2 = mesh.vertices[face[1], :]
        v3 = mesh.vertices[face[2], :]

        if color_by == ColorBy.vertex_colors or color_by == ColorBy.vertex_data or color_by == ColorBy.vertex_height:
            c1 = colors[face[0], 0:3]
            c2 = colors[face[1], 0:3]
            c3 = colors[face[2], 0:3]
        elif color_by == ColorBy.face_colors or color_by == ColorBy.face_data:    
            c1 = colors[face_counter, 0:3]
            c2 = colors[face_counter, 0:3]
            c3 = colors[face_counter, 0:3]
   
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

def move_to_origin(origin:np.ndarray, vertices:np.ndarray, pc:PointCloud = None):

    xmin = vertices[:, 0].min()
    xmax = vertices[:, 0].max()
    ymin = vertices[:, 1].min()
    ymax = vertices[:, 1].max()
    zmin = vertices[:, 2].min()
    zmax = vertices[:, 2].max()

    x_avrg = (xmin + xmax)/2.0
    y_avrg = (ymin + ymax)/2.0
    z_avrg = (zmin + zmax)/2.0

    print('Size of bounding box')
    print('xmin: ' + str(xmin) + ', xmax: ' + str(xmax))
    print('ymin: ' + str(ymin) + ', ymax: ' + str(ymax))
    
    # x, y, z, r, g, b, nx, ny ,nz
    origin_extended = np.array([origin[0], origin[1], origin[2], 0, 0, 0, 0, 0, 0])
    move_vec = origin_extended - np.array([x_avrg, y_avrg, z_avrg, 0, 0, 0, 0, 0, 0])
    vertices += move_vec

    # Move the pc with the same vector.
    points = None
    if(pc):
        move_vec = origin - np.array([x_avrg, y_avrg, z_avrg])
        points = pc.points
        points += move_vec

    return vertices, points

def flatten(vertices:np.ndarray, edge_indices:np.ndarray, face_indices:np.ndarray, points:np.ndarray = None):

    # Making sure the datatypes are aligned with opengl implementation
    vertices = np.array(vertices, dtype= "float32").flatten()
    edge_indices = np.array(edge_indices, dtype= "uint32").flatten()
    face_indices = np.array(face_indices, dtype= "uint32").flatten()
    
    if points is not None:
        points = np.array(points, dtype='float32').flatten()

    return vertices, edge_indices, face_indices, points
