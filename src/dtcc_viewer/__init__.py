from .opengl import *
from .pointcloud import view as view_pointcloud
from .mesh import view as view_mesh
from .city import view as view_city
from .building import view as view_building
from .object import view as view_object
from .new_raster import view as view_raster
from .surface import view as view_surface
from .bounds import view as view_bounds
from .grid import view as view_grid
from .volume_grid import view as view_volume_grid
from .multisurface import view as view_multisurface
from .volume_mesh import view as view_volume_mesh
from .linestring import view as view_linestring
from .multilinestring import view as view_multilinestring
from .roadnetwork import view as view_roadnetwork

# from dtcc_model import Mesh, PointCloud, Object, Surface, MultiSurface, Bounds
# from dtcc_model import Raster, City, Building, Grid, VolumeGrid, VolumeMesh
# from dtcc_model import LineString, MultiLineString, RoadNetwork

from dtcc_core.model import (
  Mesh, 
  PointCloud, 
  Object, 
  Surface,
  MultiSurface,
  Bounds,
  Raster, 
  City, 
  Building, 
  Grid, 
  VolumeGrid, 
  VolumeMesh,
  LineString, 
  MultiLineString, 
  RoadNetwork
)

# Add model extensions
PointCloud.add_methods(view_pointcloud, "view")
Mesh.add_methods(view_mesh, "view")
City.add_methods(view_city, "view")
Building.add_methods(view_building, "view")
Object.add_methods(view_object, "view")
Raster.add_methods(view_raster, "view")
Surface.add_methods(view_surface, "view")
Bounds.add_methods(view_bounds, "view")
Grid.add_methods(view_grid, "view")
VolumeGrid.add_methods(view_volume_grid, "view")
MultiSurface.add_methods(view_multisurface, "view")
VolumeMesh.add_methods(view_volume_mesh, "view")
LineString.add_methods(view_linestring, "view")
MultiLineString.add_methods(view_multilinestring, "view")
RoadNetwork.add_methods(view_roadnetwork, "view")

# Classes and methods visible on the Docs page
__all__ = [
    "view_pointcloud",
    "view_city",
    "view_mesh",
    "view_building",
    "view_object",
    "view_raster",
    "Window",
    "Scene",
    "Shading",
]
