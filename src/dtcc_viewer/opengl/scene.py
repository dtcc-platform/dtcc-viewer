import numpy as np
from OpenGL.GL import *
from dtcc_viewer.opengl.wrp_city import CityWrapper
from dtcc_viewer.opengl.wrp_object import ObjectWrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper
from dtcc_viewer.opengl.wrp_multilinestring import MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_geometries import GeometriesWrapper
from dtcc_viewer.opengl.wrp_building import BuildingWrapper
from dtcc_viewer.opengl.wrp_bounds import BoundsWrapper
from dtcc_viewer.opengl.wrp_raster import RasterWrapper, MultiRasterWrapper
from dtcc_viewer.opengl.wrp_surface import SurfaceWrapper, MultiSurfaceWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.utils import BoundingBox, Shading
from dtcc_model import (
    Mesh,
    PointCloud,
    City,
    Object,
    Building,
    Raster,
    Geometry,
    Surface,
    MultiSurface,
    Bounds,
)

# from dtcc_model.roadnetwork import RoadNetwork
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString, MultiLineString
from typing import Any


class Scene:
    """Scene which contains a collection of objects to be rendered.

    This class is used to collect and pre-process data when rendering multiple objects
    at the same time.

    Attributes
    ----------
    wrappers : list[Wrapper]
        List of Wrapper objects representing drawable geometry.
    bb : BoundingBox
        Bounding box for the entire collection of objects in the scene.
    max_tex_size : int
        Maximum texture size allowed by the graphics card.
    """

    wrappers: list[Wrapper]

    bb: BoundingBox
    mts: int

    def __init__(self):
        self.wrappers = []
        self.mts = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
        info("Max texture size: " + str(self.mts))

    def add_mesh(self, name: str, mesh: Mesh, data: Any = None):
        if mesh is not None:
            info(f"Mesh called - {name} - added to scene")
            self.wrappers.append(MeshWrapper(name, mesh, self.mts, data=data))
        else:
            warning(f"Mesh called - {name} - is None and not added to scene")

    def add_multisurface(self, name: str, ms: MultiSurface):
        if ms is not None:
            info(f"MultiSurface called - {name} - added to scene")
            self.wrappers.append(MultiSurfaceWrapper(name, ms, self.mts))
        else:
            warning(f"MultiSurface called - {name} - is None and not added to scene")

    def add_surface(self, name: str, surface: Surface):
        if surface is not None:
            info(f"Surface called - {name} - added to scene")
            self.wrappers.append(SurfaceWrapper(name, surface, self.mts))
        else:
            warning(f"Surface called - {name} - is None and not added to scene")

    def add_city(self, name: str, city: City):
        """Append a city with data and/or colors to the scene"""
        if city is not None:
            info(f"City called - {name} - added to scene")
            self.wrappers.append(CityWrapper(name, city, self.mts))
        else:
            warning(f"City called - {name} - is None and not added to scene")

    def add_object(self, name: str, obj: Object):
        """Append a generic object with data and/or colors to the scene"""
        if obj is not None:
            info(f"Object called - {name} - added to scene")
            obj_w = ObjectWrapper(name=name, obj=obj, mts=self.mts)
            self.wrappers.append(obj_w)
        else:
            warning(f"Object called - {name} - is None and not added to scene")

    def add_pointcloud(
        self,
        name: str,
        pc: PointCloud,
        size: float = 0.2,
        data: np.ndarray = None,
    ):
        """Append a pointcloud with data to color the scene"""
        if pc is not None:
            info(f"Point could called - {name} - added to scene")
            pc_w = PointCloudWrapper(name, pc, self.mts, size, data=data)
            self.wrappers.append(pc_w)
        else:
            warning(f"Point could called - {name} - is None and not added to scene")

    def add_linestring(self, name: str, ls: LineString, data: Any = None):
        if ls is not None:
            info(f"List of LineStrings called - {name} - added to scene")
            self.wrappers.append(LineStringWrapper(name, ls, self.mts, data))
        else:
            warning(f"Road network called - {name} - is None and not added to scene")

    def add_multilinestring(self, name: str, mls: MultiLineString, data: Any = None):
        if mls is not None:
            info(f"MultiLineString called - {name} - added to scene")
            self.wrappers.append(MultiLineStringWrapper(name, mls, self.mts, data))
        else:
            warning(f"MultiLineString called - {name} - is None and not added to scene")

    def add_building(self, name: str, building: Building):
        if building is not None:
            info(f"Building called - {name} - added to scene")
            self.wrappers.append(BuildingWrapper(name, building, self.mts))
        else:
            warning(f"Building called - {name} - is None and not added to scene")

    def add_raster(self, name: str, raster: Raster):
        max_size = 10000
        if raster is not None:
            if np.max(raster.data.shape) > max_size:
                info(f"Multi raster called - {name} - added to scene")
                mrst_w = MultiRasterWrapper(name=name, raster=raster, max_size=max_size)
                self.wrappers.append(mrst_w)
            else:
                info(f"Raster called - {name} - added to scene")
                rst_w = RasterWrapper(name=name, raster=raster)
                self.wrappers.append(rst_w)
        else:
            warning(f"Raster called - {name} - is None and not added to scene")

    def add_geometries(self, name: str, geometries: list[Geometry]):
        if geometries is not None:
            info(f"Geometry collection called - {name} - added to scene")
            self.wrappers.append(GeometriesWrapper(name, geometries, self.mts))
        else:
            warning(f"Failed to add geometry collection called - {name} - to scene")

    def add_bounds(self, name: str, bounds: Bounds):
        if bounds is not None:
            info(f"Bounds called - {name} - added to scene")
            self.wrappers.append(BoundsWrapper(name, bounds, self.mts))
        else:
            warning(f"Failed to add bounds called - {name} - to scene")

    def preprocess_drawing(self):
        """Preprocess bounding box calculation for all scene objects"""

        # Calculate bounding box for the entire scene including the vector that is
        # used to center move everything to the origin.
        self.bb = self._calculate_bb()

        # Move the bounding box so that everything is in positive z-space. This move
        # will impact all the preprocessing below.
        self.bb.move_to_zero_z()

        if self.bb is None:
            warning("No bounding box found for the scene.")
            return False

        for wrapper in self.wrappers:
            wrapper.preprocess_drawing(self.bb)

        info(f"Scene preprocessing completed successfully")
        return True

    def _calculate_bb(self):
        """Calculate bounding box of the scene"""

        # Flat array of vertices [x1,y1,z1,x2,y2,z2, ...]
        vertices = np.array([])

        for wrp in self.wrappers:
            vertices = np.concatenate((vertices, wrp.get_vertex_positions()), axis=0)

        if len(vertices) > 3:  # At least 1 vertex
            bb = BoundingBox(vertices)
            return bb
        else:
            warning("No vertices found in scene")
            return None
