from .citymodel import view as view_citymodel
from .mesh_opengl import view as view_mesh
from .pointcloud_opengl import view as view_pointcloud

from dtcc_model import City as CityModel # FIXME: Renamed to City
from dtcc_model import Mesh
from dtcc_model import PointCloud

CityModel.add_methods(view_citymodel, "view") # FIXME: --> view_city()
Mesh.add_methods(view_mesh, "view")
PointCloud.add_methods(view_pointcloud, "view")
