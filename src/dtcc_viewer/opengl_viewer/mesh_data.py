import numpy as np
from dtcc_model import Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *

class MeshData:

    color_by: int
    mesh_colors: np.ndarray     
    vertices: np.ndarray
    face_indices: np.ndarray
    edge_indices: np.ndarray
    name: str
    
    def __init__(self, name:str, mesh:Mesh, mesh_data:np.ndarray = None, recenter_vec:np.ndarray = None) -> None:
        self.name = name
        [self.color_by, self.mesh_colors] = self.generate_mesh_colors(mesh, mesh_data)
        [self.vertices, self.face_indices, self.edge_indices] = self.restructure_mesh(mesh, self.color_by, self.mesh_colors)
        self.vertices = self.move_mesh_to_origin_multi(self.vertices,  recenter_vec)
        [self.vertices, self.edge_indices, self.face_indices] = self.flatten_mesh(self.vertices, self.edge_indices, self.face_indices)
    
    def generate_mesh_colors(self, mesh:Mesh, data:np.ndarray = None):

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
                colors = self.normalise_colors(mesh.vertex_colors)
            elif n_face_colors == n_faces:
                color_by = ColorBy.face_colors
                colors = self.normalise_colors(mesh.face_colors)           
            else:
                print("WARNING: Provided color data for mesh does not match vertex of face count!")
                print("Default colors are used instead -> i.e. coloring per vertex z-value")
        else: 
            if n_data == n_vertices:                #Generate colors base on provided vertex data
                color_by = ColorBy.vertex_data
                colors = calc_colors_rainbow(data)
            elif n_data == n_faces:                 #Generate colors base on provided face data
                color_by = ColorBy.face_data        
                colors = calc_colors_rainbow(data)
            else:
                print("WARNING: Provided color data for mesh does not match vertex of face count!")
                print("Default colors are used instead -> i.e. coloring per vertex z-value")
                    
        return color_by, np.array(colors) 

    def normalise_colors(self, colors:np.ndarray):
        #If the max color value is larger then 1 it is assumed that the color range is 0-255
        max = np.max(colors)
        if(max > 1.0):
            colors /= 255.0
        return colors

    def restructure_mesh(self, mesh:Mesh, color_by:ColorBy, colors:np.ndarray):       
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

    def move_mesh_to_origin(self, vertices:np.ndarray, pc_avrg_pt:np.ndarray = None, multi_recenter_vec:np.ndarray = None):
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

    def move_mesh_to_origin_multi(self, vertices:np.ndarray, recenter_vec:np.ndarray = None):
        # x, y, z, r, g, b, nx, ny ,nz
        if recenter_vec is not None:    
            recenter_vec = np.concatenate((recenter_vec,[0, 0, 0, 0, 0, 0]), axis=0)
            vertices += recenter_vec    
        
        return vertices

    def flatten_mesh(self, vertices:np.ndarray, face_indices:np.ndarray, edge_indices:np.ndarray):
        # Making sure the datatypes are aligned with opengl implementation
        vertices = np.array(vertices, dtype= "float32").flatten()
        edge_indices = np.array(edge_indices, dtype= "uint32").flatten()
        face_indices = np.array(face_indices, dtype= "uint32").flatten()

        return vertices, face_indices, edge_indices