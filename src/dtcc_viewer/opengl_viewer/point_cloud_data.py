import numpy as np
from dtcc_model import PointCloud, Mesh
from dtcc_viewer.utils import *

class PointCloudData:

    points: np.ndarray          #[n_points x 3]
    colors :np.ndarray       #[n_points x 3]
    pc_avrg_pt: np.ndarray      #[1 x 3]
    name: str

    def __init__(self, name:str, pc:PointCloud, pc_data: np.ndarray, recenter_vec: np.ndarray) -> None:
            
        self.colors = generate_pc_colors(pc, pc_data)                            # TODO: Move functions here 
        [self.points, self.colors] = restructure_pc(pc, self.colors)  
        self.points = move_pc_to_origin_multi(self.points, recenter_vec)
        [self.points, self.colors] = flatten_pc(self.points, self.colors)