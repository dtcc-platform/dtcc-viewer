from .citymodel import view as view_citymodel
from .mesh_opengl import view as view_mesh
from .pointcloud_opengl import view as view_pointcloud

from dtcc_model import CityModel
from dtcc_model import Mesh
from dtcc_model import PointCloud

CityModel.add_processors(view_citymodel, "view")
Mesh.add_processors(view_mesh, "view")
PointCloud.add_processors(view_pointcloud, "view")