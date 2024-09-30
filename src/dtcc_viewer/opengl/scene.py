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
from dtcc_viewer.opengl.wrp_volume_mesh import VolumeMeshWrapper
from dtcc_viewer.opengl.wrp_roadnetwork import RoadNetworkWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.utils import BoundingBox, Shading
from dtcc_core.model import Mesh, PointCloud, City, Object, Building, Raster, VolumeMesh
from dtcc_core.model import Geometry, Surface, MultiSurface, Bounds, Grid, VolumeGrid
from dtcc_core.model import RoadNetwork, LineString, MultiLineString

# from dtcc_model.roadnetwork import RoadNetwork
from dtcc_viewer.logging import info, warning
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
        """
        Initialize the Scene.

        This method sets up the wrappers list and retrieves the maximum texture size
        supported by the graphics card.
        """
        self.wrappers = []
        self.mts = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
        info("Max texture size: " + str(self.mts))

    def add_mesh(self, name: str, mesh: Mesh, data: Any = None):
        """
        Add a mesh to the scene.

        Parameters
        ----------
        name : str
            Name of the mesh.
        mesh : Mesh
            Mesh object to be added.
        data : Any, optional
            Additional data associated with the mesh.
        """
        if mesh is not None and isinstance(mesh, Mesh) and self.has_geom(mesh, name):
            info(f"Mesh called '{name}' added to scene")
            self.wrappers.append(MeshWrapper(name, mesh, self.mts, data=data))
        else:
            warning(f"Failed to add Mesh called '{name}' to the scene")

    def add_multisurface(self, name: str, ms: MultiSurface):
        """
        Add a MultiSurface to the scene.

        Parameters
        ----------
        name : str
            Name of the MultiSurface.
        ms : MultiSurface
            MultiSurface object to be added.
        """
        if ms is not None and isinstance(ms, MultiSurface) and self.has_geom(ms, name):
            info(f"MultiSurface called '{name}' added to scene")
            self.wrappers.append(MultiSurfaceWrapper(name, ms, self.mts))
        else:
            warning(f"Failed to add MultiSurface called '{name}' to the scene")

    def add_surface(self, name: str, srf: Surface):
        """
        Add a surface to the scene.

        Parameters
        ----------
        name : str
            Name of the surface.
        surface : Surface
            Surface object to be added.
        """
        if srf is not None and isinstance(srf, Surface) and self.has_geom(srf, name):
            info(f"Surface called '{name}' added to scene")
            self.wrappers.append(SurfaceWrapper(name, srf, self.mts))
        else:
            warning(f"Failed to add Surface called '{name}' added to the scene")

    def add_city(self, name: str, city: City):
        """
        Add a city to the scene.

        Parameters
        ----------
        name : str
            Name of the city.
        city : City
            City object to be added.
        """
        if city is not None and isinstance(city, City) and self.has_geom(city, name):
            info(f"City called '{name}' added to scene")
            self.wrappers.append(CityWrapper(name, city, self.mts))
        else:
            warning(f"Failed to add City called '{name}' to the scene")

    def add_object(self, name: str, obj: Object):
        """
        Add an object to the scene.

        Parameters
        ----------
        name : str
            Name of the object.
        obj : Object
            Object to be added.
        """
        if obj is not None and isinstance(obj, Object):
            info(f"Object called '{name}' added to scene")
            self.wrappers.append(ObjectWrapper(name, obj, self.mts))
        else:
            warning(f"Failed to add Object called '{name}' to the scene")

    def add_pointcloud(
        self, name: str, pc: PointCloud, size: float = 0.2, data: np.ndarray = None
    ):
        """
        Add a point cloud to the scene.

        Parameters
        ----------
        name : str
            Name of the point cloud.
        pc : PointCloud
            PointCloud object to be added.
        size : float, optional
            Size of the points in the point cloud.
        data : np.ndarray, optional
            Additional data associated with the point cloud.
        """
        if pc is not None and isinstance(pc, PointCloud) and self.has_geom(pc, name):
            info(f"Point could called '{name}' added to scene")
            self.wrappers.append(PointCloudWrapper(name, pc, self.mts, size, data=data))
        else:
            warning(f"Failed to add PointCould called '{name}' to the scene")

    def add_linestring(self, name: str, ls: LineString, data: Any = None):
        """
        Add a line string to the scene.

        Parameters
        ----------
        name : str
            Name of the line string.
        ls : LineString
            LineString object to be added.
        data : Any, optional
            Additional data associated with the line string.
        """
        if ls is not None and isinstance(ls, LineString) and self.has_geom(ls, name):
            info(f"List of LineStrings called '{name}' added to scene")
            self.wrappers.append(LineStringWrapper(name, ls, self.mts, data))
        else:
            warning(f"Failed to add LineString '{name}' to the scene")

    def add_multilinestring(self, name: str, mls: MultiLineString, data: Any = None):
        """
        Add a multi-line string to the scene.

        Parameters
        ----------
        name : str
            Name of the multi-line string.
        mls : MultiLineString
            MultiLineString object to be added.
        data : Any, optional
            Additional data associated with the multi-line string.
        """
        if (
            mls is not None
            and isinstance(mls, MultiLineString)
            and self.has_geom(mls, name)
        ):
            info(f"MultiLineString called '{name}' added to scene")
            self.wrappers.append(MultiLineStringWrapper(name, mls, self.mts, data))
        else:
            warning(f"Failed to att MultiLineString called '{name}' to the scene")

    def add_building(self, name: str, building: Building):
        """
        Add a building to the scene.

        Parameters
        ----------
        name : str
            Name of the building.
        building : Building
            Building object to be added.
        """
        if (
            building is not None
            and isinstance(building, Building)
            and self.has_geom(building, name)
        ):
            info(f"Building called '{name}' added to scene")
            self.wrappers.append(BuildingWrapper(name, building, self.mts))
        else:
            warning(f"Failed to add Building called '{name}' to the scene")

    def add_raster(self, name: str, raster: Raster):
        """
        Add a raster to the scene.

        Parameters
        ----------
        name : str
            Name of the raster.
        raster : Raster
            Raster object to be added.
        """
        max_size = 16384
        if (
            raster is not None
            and isinstance(raster, Raster)
            and self.has_geom(raster, name)
        ):
            if np.max(raster.data.shape) > max_size:
                info(f"Multi raster called '{name}' added to scene")
                self.wrappers.append(MultiRasterWrapper(name, raster, max_size))
            else:
                info(f"Raster called '{name}' added to scene")
                self.wrappers.append(RasterWrapper(name, raster))
        else:
            warning(f"Failed to add raster called '{name}' to the scene")

    def add_geometries(self, name: str, geometries: list[Geometry]):
        """
        Add a collection of geometries to the scene.

        Parameters
        ----------
        name : str
            Name of the geometry collection.
        geometries : list[Geometry]
            List of Geometry objects to be added.
        """
        if geometries is not None and isinstance(geometries, list):
            info(f"Geometry collection called '{name}' added to scene")
            self.wrappers.append(GeometriesWrapper(name, geometries, self.mts))
        else:
            warning(f"Failed to add geometry collection called '{name}' to scene")

    def add_bounds(self, name: str, bounds: Bounds):
        """
        Add bounds to the scene.

        Parameters
        ----------
        name : str
            Name of the bounds.
        bounds : Bounds
            Bounds object to be added.
        """
        if (
            bounds is not None
            and isinstance(bounds, Bounds)
            and self.has_geom(bounds, name)
        ):
            info(f"Bounds called '{name}' added to scene")
            self.wrappers.append(BoundsWrapper(name, bounds, self.mts))
        else:
            warning(f"Failed to add bounds called '{name}' to scene")

    def add_grid(self, name: str, grid: Grid):
        """
        Add a grid to the scene.

        Parameters
        ----------
        name : str
            Name of the grid.
        grid : Grid
            Grid object to be added.
        """
        if grid is not None and isinstance(grid, Grid) and self.has_geom(grid, name):
            info(f"Grid called '{name}' added to scene")
            self.wrappers.append(GridWrapper(name, grid, self.mts))
        else:
            warning(f"Failed to add grid called '{name}' to scene")

    def add_volume_grid(self, name: str, grid: VolumeGrid):
        """
        Add a volume grid to the scene.

        Parameters
        ----------
        name : str
            Name of the volume grid.
        grid : VolumeGrid
            VolumeGrid object to be added.
        """
        if (
            grid is not None
            and isinstance(grid, VolumeGrid)
            and self.has_geom(grid, name)
        ):
            info(f"Grid called '{name}' added to scene")
            self.wrappers.append(VolumeGridWrapper(name, grid, self.mts))
        else:
            warning(f"Failed to add grid called '{name}' to scene")

    def add_volume_mesh(self, name: str, volume_mesh: VolumeMesh):
        """
        Add a volume mesh to the scene.

        Parameters
        ----------
        name : str
            Name of the volume mesh.
        volume_mesh : VolumeMesh
            VolumeMesh object to be added.
        """
        if (
            volume_mesh is not None
            and isinstance(volume_mesh, VolumeMesh)
            and self.has_geom(volume_mesh, name)
        ):
            info(f"Grid called '{name}' added to scene")
            self.wrappers.append(VolumeMeshWrapper(name, volume_mesh, self.mts))
        else:
            warning(f"Failed to add grid called '{name}' to scene")

    def add_roadnetwork(self, name: str, road_network: Any):
        """
        Add a road network to the scene.

        Parameters
        ----------
        name : str
            Name of the road network.
        road_network : Any
            RoadNetwork object to be added.
        """
        if (
            road_network is not None
            and isinstance(road_network, RoadNetwork)
            and self.has_geom(road_network, name)
        ):
            info(f"Road network called '{name}' added to scene")
            self.wrappers.append(RoadNetworkWrapper(name, road_network, self.mts))
        else:
            warning(f"Failed to add road network called '{name}' to scene")

    def preprocess_drawing(self):
        """
        Preprocess bounding box calculation for all scene objects.

        This method calculates the bounding box for the entire scene, including
        centering all objects in the scene, and preprocesses each wrapper object
        for drawing.
        """
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
        """
        Calculate the bounding box of the scene.

        This method calculates the bounding box based on the vertices of all wrapper
        objects in the scene.

        Returns
        -------
        BoundingBox or None
            The bounding box of the scene, or None if no vertices are found.
        """

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
        """
        Offset mesh parts IDs to enable clicking.

        This method offsets the IDs of mesh parts in the scene to ensure unique
        identifiers for each part, facilitating interactions like clicking.
        """
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
                for vmesh_wrp in wrp.vmesh_wrps:
                    if vmesh_wrp.mesh_vol_wrp is not None:
                        next_id = self.update_ids(vmesh_wrp.mesh_vol_wrp, next_id)
                    if vmesh_wrp.mesh_env_wrp is not None:
                        next_id = self.update_ids(vmesh_wrp.mesh_env_wrp, next_id)
            elif isinstance(wrp, BuildingWrapper):
                next_id = self.update_ids(wrp.mesh_wrp, next_id)
            elif isinstance(wrp, ObjectWrapper):
                if wrp.mesh_wrp_1 is not None:
                    next_id = self.update_ids(wrp.mesh_wrp_1, next_id)
                if wrp.mesh_wrp_2 is not None:
                    next_id = self.update_ids(wrp.mesh_wrp_2, next_id)
            elif isinstance(wrp, VolumeMeshWrapper):
                if wrp.mesh_vol_wrp is not None:
                    next_id = self.update_ids(wrp.mesh_vol_wrp, next_id)
                if wrp.mesh_env_wrp is not None:
                    next_id = self.update_ids(wrp.mesh_env_wrp, next_id)

    def update_ids(self, mesh_wrp: MeshWrapper, next_id):
        """
        Update IDs of a mesh wrapper's parts.

        Parameters
        ----------
        mesh_wrp : MeshWrapper
            MeshWrapper object whose part IDs need to be updated.
        next_id : int
            The next ID to be assigned.

        Returns
        -------
        int
            The updated next ID after assigning IDs to the mesh wrapper's parts.
        """
        max_id = np.max(mesh_wrp.parts.ids)
        mesh_wrp.parts.offset_ids(next_id)
        mesh_wrp.update_ids_from_parts()
        next_id += max_id + 1
        return next_id

    def has_geom(self, obj: Any, name: str):
        """
        Trying to catch objects without geometry.

        Returns
        -------
        bool
            True if the scene has geometry, False otherwise.
        """

        # Conditions for checking if an object has geometry
        conditions = {
            Mesh: lambda obj: len(obj.vertices) > 2 and len(obj.faces) > 0,
            MultiSurface: lambda obj: len(obj.surfaces) > 0,
            Surface: lambda obj: len(obj.vertices) > 2,
            City: lambda obj: len(obj.buildings) > 0 or obj.terrain is not None,
            MultiLineString: lambda obj: len(obj.linestrings) > 0,
            LineString: lambda obj: len(obj.vertices) > 1,
            PointCloud: lambda obj: len(obj.points) > 0,
            VolumeGrid: lambda obj: len(obj.coordinates()) > 2,
            Grid: lambda obj: len(obj.coordinates()) > 2,
            Building: lambda obj: len(obj.children) > 0 or len(obj.geometry) > 0,
            RoadNetwork: lambda obj: len(obj.vertices) > 0,
            VolumeMesh: lambda obj: len(obj.vertices) > 3 and len(obj.cells) > 0,
            Bounds: lambda obj: obj.width != 0.0 and obj.height != 0.0,
            Raster: lambda obj: len(obj.data) > 0,
        }

        if obj is not None:
            for obj_type, condition in conditions.items():
                if isinstance(obj, obj_type):
                    if condition(obj):
                        return True
                    else:
                        obj_class_name = obj.__class__.__name__
                        warning(f"{obj_class_name} called '{name}' has no geometry")
                        return False

        # Assume it has geometry if the object is None or not one of the specified types
        return True
