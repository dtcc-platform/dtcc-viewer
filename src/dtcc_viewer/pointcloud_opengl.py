import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.window import Window

def view(pc:PointCloud, mesh:Mesh = None, pc_data:np.ndarray = None, mesh_data:np.ndarray = None):
    
    window = Window(1200, 800)

    pc_colors = generate_pc_colors(pc, pc_data)
    [points, pc_colors] = restructure_pc(pc, pc_colors)  
    [points, pc_avrg_pt] = move_pc_to_origin(points, pc)
    [points, pc_colors] = flatten_pc(points, pc_colors)

    if (mesh is None):
        window.render_particles(points, pc_colors)
    else:
        [color_by, mesh_colors] = generate_mesh_colors(mesh, mesh_data)
        [vertices, face_indices, edge_indices] = restructure_mesh(mesh, color_by, mesh_colors)
        [vertices, mesh_avrg_pt] = move_mesh_to_origin(vertices, pc_avrg_pt)
        [vertices, edge_indices, face_indices] = flatten_mesh(vertices, edge_indices, face_indices)
    
        window.render_particles_and_mesh(points, pc_colors, vertices, face_indices, edge_indices)

