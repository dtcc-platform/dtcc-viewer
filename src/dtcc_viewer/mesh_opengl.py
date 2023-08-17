import numpy as np
from dtcc_model import Mesh
from dtcc_model import PointCloud
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData

def view(mesh:Mesh, mesh_data:np.ndarray = None, pc:PointCloud = None, pc_data:np.ndarray = None):

    window = Window(1200, 800)
    
    if(pc is None):
        recenter_vec = calc_recenter_vector(mesh=mesh)
        mesh_data_obj = MeshData("Mesh View", mesh, mesh_data, recenter_vec)
        window.render_mesh(mesh_data_obj.vertices, mesh_data_obj.face_indices, mesh_data_obj.edge_indices)
    else:
        recenter_vec = calc_recenter_vector(mesh, pc)
        mesh_data_obj = MeshData("Mesh View", mesh, mesh_data, recenter_vec)
        pc_data_obj = PointCloudData("Point Cloud View", pc, pc_data, recenter_vec)    
        window.render_pc_and_mesh(pc_data_obj.points, pc_data_obj.colors, mesh_data_obj.vertices, mesh_data_obj.face_indices, mesh_data_obj.edge_indices)    

