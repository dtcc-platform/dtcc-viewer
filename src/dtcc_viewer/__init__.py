from .opengl import *
from .pointcloud import view as view_pointcloud
from .mesh import view as view_mesh
from .roadnetwork import view as view_roadnetwork
from .city import view as view_city
from .building import view as view_building
from .object import view as view_object
from .roster import view as view_raster

from dtcc_model import Mesh, PointCloud, Object, RoadNetwork
from dtcc_model import Raster, NewCity, NewBuilding

# Add model extensions
PointCloud.add_methods(view_pointcloud, "view")
Mesh.add_methods(view_mesh, "view")
RoadNetwork.add_methods(view_roadnetwork, "view")
NewCity.add_methods(view_city, "view")
NewBuilding.add_methods(view_building, "view")
Object.add_methods(view_object, "view")
Raster.add_methods(view_raster, "view")

# Classes and methods visible on the Docs page
__all__ = [
    "view_pointcloud",
    "view_city",
    "view_mesh",
    "view_roadnetwork",
    "view_building",
    "view_object",
    "view_raster",
    "Window",
    "Scene",
    "Shading",
]
