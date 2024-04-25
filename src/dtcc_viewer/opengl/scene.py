import numpy as np
from OpenGL.GL import *
from dtcc_viewer.opengl.wrp_city import CityWrapper
from dtcc_viewer.opengl.wrp_object import ObjectWrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_grid import GridWrapper, VolumeGridWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper, MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_geometries import GeometriesWrapper
from dtcc_viewer.opengl.wrp_building import BuildingWrapper
from dtcc_viewer.opengl.wrp_bounds import BoundsWrapper
from dtcc_viewer.opengl.wrp_raster import RasterWrapper, MultiRasterWrapper
from dtcc_viewer.opengl.wrp_surface import SurfaceWrapper, MultiSurfaceWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.utils import BoundingBox, Shading
from dtcc_model import Mesh, PointCloud, City, Object, Building, Raster
from dtcc_model import Geometry, Surface, MultiSurface, Bounds, Grid, VolumeGrid

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
    mts : int
        Maximum texture size (mts) allowed by the graphics card.
    """

    wrappers: list[Wrapper]
    bb: BoundingBox
    mts: int

    def __init__(self):
        self.wrappers = []
        self.mts = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
        info("Max texture size: " + str(self.mts))

    def add_mesh(self, name: str, mesh: Mesh, data: Any = None):
        if mesh is not None and isinstance(mesh, Mesh):
            info(f"Mesh called - {name} - added to scene")
            self.wrappers.append(MeshWrapper(name, mesh, self.mts, data=data))
        else:
            warning(f"Failed to add Mesh called - {name} - to the scene")

    def add_multisurface(self, name: str, ms: MultiSurface):
        if ms is not None and isinstance(ms, MultiSurface):
            info(f"MultiSurface called - {name} - added to scene")
            self.wrappers.append(MultiSurfaceWrapper(name, ms, self.mts))
        else:
            warning(f"Failed to add MultiSurface called - {name} - to the scene")

    def add_surface(self, name: str, surface: Surface):
        if surface is not None and isinstance(surface, Surface):
            info(f"Surface called - {name} - added to scene")
            self.wrappers.append(SurfaceWrapper(name, surface, self.mts))
        else:
            warning(f"Failed to add Surface called - {name} - added to the scene")

    def add_city(self, name: str, city: City):
        if city is not None and isinstance(city, City):
            info(f"City called - {name} - added to scene")
            self.wrappers.append(CityWrapper(name, city, self.mts))
        else:
            warning(f"Failed to add City called - {name} - to the scene")

    def add_object(self, name: str, obj: Object):
        if obj is not None and isinstance(obj, Object):
            info(f"Object called - {name} - added to scene")
            self.wrappers.append(ObjectWrapper(name, obj, self.mts))
        else:
            warning(f"Failed to add Object called - {name} - to the scene")

    def add_pointcloud(
        self, name: str, pc: PointCloud, size: float = 0.2, data: np.ndarray = None
    ):
        if pc is not None and isinstance(pc, PointCloud):
            info(f"Point could called - {name} - added to scene")
            self.wrappers.append(PointCloudWrapper(name, pc, self.mts, size, data=data))
        else:
            warning(f"Failed to add PointCould called - {name} - to the scene")

    def add_linestring(self, name: str, ls: LineString, data: Any = None):
        if ls is not None and isinstance(ls, LineString):
            info(f"List of LineStrings called - {name} - added to scene")
            self.wrappers.append(LineStringWrapper(name, ls, self.mts, data))
        else:
            warning(f"Failed to add LineString - {name} - to the scene")

    def add_multilinestring(self, name: str, mls: MultiLineString, data: Any = None):
        if mls is not None and isinstance(mls, MultiLineString):
            info(f"MultiLineString called - {name} - added to scene")
            self.wrappers.append(MultiLineStringWrapper(name, mls, self.mts, data))
        else:
            warning(f"Failed to att MultiLineString called - {name} - to the scene")

    def add_building(self, name: str, building: Building):
        if building is not None and isinstance(building, Building):
            info(f"Building called - {name} - added to scene")
            self.wrappers.append(BuildingWrapper(name, building, self.mts))
        else:
            warning(f"Failed to add Building called - {name} - to the scene")

    def add_raster(self, name: str, raster: Raster):
        max_size = 10000
        if raster is not None and isinstance(raster, Raster):
            if np.max(raster.data.shape) > max_size:
                info(f"Multi raster called - {name} - added to scene")
                self.wrappers.append(MultiRasterWrapper(name, raster, max_size))
            else:
                info(f"Raster called - {name} - added to scene")
                self.wrappers.append(RasterWrapper(name, raster))
        else:
            warning(f"Failed to add raster called - {name} - to the scene")

    def add_geometries(self, name: str, geometries: list[Geometry]):
        if geometries is not None and isinstance(geometries, list):
            if all(isinstance(item, Geometry) for item in geometries):
                info(f"Geometry collection called - {name} - added to scene")
                self.wrappers.append(GeometriesWrapper(name, geometries, self.mts))
            else:
                warning(f"Failed to add geometry collection called - {name} - to scene")
        else:
            warning(f"Failed to add geometry collection called - {name} - to scene")

    def add_bounds(self, name: str, bounds: Bounds):
        if bounds is not None and isinstance(bounds, Bounds):
            info(f"Bounds called - {name} - added to scene")
            self.wrappers.append(BoundsWrapper(name, bounds, self.mts))
        else:
            warning(f"Failed to add bounds called - {name} - to scene")

    def add_grid(self, name: str, grid: Grid):
        if grid is not None and isinstance(grid, Grid):
            info(f"Grid called - {name} - added to scene")
            self.wrappers.append(GridWrapper(name, grid, self.mts))
        else:
            warning(f"Failed to add grid called - {name} - to scene")

    def add_volume_grid(self, name: str, grid: VolumeGrid):
        if grid is not None and isinstance(grid, VolumeGrid):
            info(f"Grid called - {name} - added to scene")
            self.wrappers.append(VolumeGridWrapper(name, grid, self.mts))
        else:
            warning(f"Failed to add grid called - {name} - to scene")

    def preprocess_drawing(self):
        """Preprocess bounding box calculation for all scene objects"""

        # Calculate bounding box for the entire scene including the vector that is
        # used to center move everything to the origin.
        self.bb = self._calculate_bb()

        if self.bb is None:
            warning("No bounding box found for the scene.")
            return False

        for wrapper in self.wrappers:
            wrapper.preprocess_drawing(self.bb)

        self.bb.move_to_center()

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
            warning("No vertices found in the scene")
            return None

    def offset_mesh_part_ids(self):
        """Offset submesh ids to enable clicking"""
        next_id = 0
        for wrp in self.wrappers:
            if isinstance(wrp, MeshWrapper):
                next_id = self.update_ids(wrp, next_id)
            elif isinstance(wrp, MultiSurfaceWrapper):
                next_id = self.update_ids(wrp.mesh_wrp, next_id)
            elif isinstance(wrp, MultiSurfaceWrapper):
                next_id = self.update_ids(wrp.mesh_wrp, next_id)
            elif isinstance(wrp, CityWrapper):
                if wrp.mesh_ter is not None:
                    next_id = self.update_ids(wrp.mesh_ter, next_id)
                if wrp.mesh_bld is not None:
                    next_id = self.update_ids(wrp.mesh_bld, next_id)
            elif isinstance(wrp, GeometriesWrapper):
                for mesh_wrp in wrp.mesh_wrps:
                    next_id = self.update_ids(mesh_wrp, next_id)
                for ms_wrp in wrp.ms_wrps:
                    next_id = self.update_ids(ms_wrp.mesh_wrp, next_id)
                for srf_wrp in wrp.srf_wrps:
                    next_id = self.update_ids(srf_wrp.mesh_wrp, next_id)
            elif isinstance(wrp, BuildingWrapper):
                next_id = self.update_ids(wrp.mesh_wrp, next_id)
            elif isinstance(wrp, ObjectWrapper):
                if wrp.mesh_wrp_1 is not None:
                    next_id = self.update_ids(wrp.mesh_wrp_1, next_id)
                if wrp.mesh_wrp_2 is not None:
                    next_id = self.update_ids(wrp.mesh_wrp_2, next_id)

    def update_ids(self, mesh_wrp: MeshWrapper, next_id):
        max_id = np.max(mesh_wrp.parts.ids)
        mesh_wrp.parts.offset_ids(next_id)
        mesh_wrp.update_ids_from_parts()
        next_id += max_id + 1
        return next_id
