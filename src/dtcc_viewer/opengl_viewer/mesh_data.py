import numpy as np
from dtcc_model import Mesh
from dtcc_viewer.utils import *

class MeshData:

    color_by: int
    mesh_colors: np.ndarray     
    vertices: np.ndarray
    face_indices: np.ndarray
    edge_indices: np.ndarray
    name: str
    
    def __init__(self, name:str, mesh:Mesh, mesh_data:np.ndarray = None, recenter_vec:np.ndarray = None,  pc_avrg_pt:np.ndarray = None,  multi_avrg_pt:np.ndarray = None) -> None:
        [self.color_by, self.mesh_colors] = generate_mesh_colors(mesh, mesh_data)
        [self.vertices, self.face_indices, self.edge_indices] = restructure_mesh(mesh, self.color_by, self.mesh_colors)
        self.vertices = move_mesh_to_origin_multi(self.vertices,  recenter_vec)
        [self.vertices, self.edge_indices, self.face_indices] = flatten_mesh(self.vertices, self.edge_indices, self.face_indices)
    

