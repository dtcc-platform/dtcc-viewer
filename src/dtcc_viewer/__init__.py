from .opengl_viewer import *
from .pointcloud_opengl import view as view_pointcloud
from .mesh_opengl import view as view_mesh
from .citymodel import view as view_city

from dtcc_model import PointCloud
from dtcc_model import Mesh
from dtcc_model import City

# Add model extensions
PointCloud.add_methods(view_pointcloud, "view")
Mesh.add_methods(view_mesh, "view")
City.add_methods(view_city, "view")

__all__ = [
    "view_pointcloud",
    "view_city",
    "view_mesh",
    "Camera",
    "Window",
    "PointCloudData",
    "PointCloudGL",
    "MeshGL",
    "MeshData",
    "Interaction",
    "Scene",
    "Gui",
    "GuiParameters",
    "GuiParametersMesh",
    "GuiParametersPC",
    "GuiParameters",
]
