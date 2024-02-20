from .opengl_viewer import *
from .pointcloud_opengl import view as view_pointcloud
from .mesh_opengl import view as view_mesh
from .roadnetwork_opengl import view as view_roadnetwork
from .city_opengl import view as view_city

# from .citymodel import view as view_city


from dtcc_model import Mesh, PointCloud, City, RoadNetwork, NewCity

# Add model extensions
PointCloud.add_methods(view_pointcloud, "view")
Mesh.add_methods(view_mesh, "view")
RoadNetwork.add_methods(view_roadnetwork, "view")
NewCity.add_methods(view_city, "view")

# Classes and methods visible on the Docs page
__all__ = [
    "view_pointcloud",
    "view_city",
    "view_mesh",
    "view_roadnetwork",
    "Window",
    "Scene",
    "Shading",
]
