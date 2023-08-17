import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData

def view(pc:PointCloud, mesh:Mesh = None, pc_data:np.ndarray = None, mesh_data:np.ndarray = None):
    
    window = Window(1200, 800)

    if (mesh is None):
        recenter_vec = calc_recenter_vector(pc=pc)
        pc_data_obj = PointCloudData("Point Cloud View", pc, pc_data, recenter_vec)    
        window.render_point_cloud(pc_data_obj.points, pc_data_obj.colors)
    else:
        recenter_vec = calc_recenter_vector(mesh, pc)
        mesh_data_obj = MeshData("Mesh View", mesh, mesh_data, recenter_vec)
        pc_data_obj = PointCloudData("Point Cloud View", pc, pc_data, recenter_vec)    
        window.render_pc_and_mesh(pc_data_obj.points, pc_data_obj.colors, mesh_data_obj.vertices, mesh_data_obj.face_indices, mesh_data_obj.edge_indices)    

