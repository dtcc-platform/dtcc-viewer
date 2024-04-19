import numpy as np
from OpenGL.GL import *
from dtcc_viewer.opengl.wrp_city import CityWrapper
from dtcc_viewer.opengl.wrp_object import ObjectWrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_roadnetwork import RoadNetworkWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_linestrings import LineStringsWrapper
from dtcc_viewer.opengl.wrp_geometries import GeometriesWrapper
from dtcc_viewer.opengl.wrp_building import BuildingWrapper
from dtcc_viewer.opengl.wrp_raster import RasterWrapper, MultiRasterWrapper
from dtcc_viewer.opengl.utils import BoundingBox, Shading
from dtcc_model import Mesh, PointCloud, City, Object, Building, Raster, Geometry

# from dtcc_model.roadnetwork import RoadNetwork
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString
from typing import Any


class Scene:
    """Scene which contains a collection of objects to be rendered.

    This class is used to collect and pre-process data when rendering multiple objects
    at the same time.

    Attributes
    ----------
    city_wrappers : list[CityWrapper]
        List of CityWrapper objects representing cities to be drawn.
    mesh_wrappers : list[MeshWrapper]
        List of MeshWrapper objects representing meshes to be drawn.
    pcs_wrappers : list[PointCloudWrapper]
        List of PointCloudWrapper objects representing point clouds to be drawn.
    rdn_wrappers : list[RoadNetworkWrapper]
        List of RoadNetworkWrapper objects representing road networks to be drawn.
    bb : BoundingBox
        Bounding box for the entire collection of objects in the scene.
    max_tex_size : int
        Maximum texture size allowed by the graphics card.
    """

    obj_wrappers: list[ObjectWrapper]
    city_wrappers: list[CityWrapper]
    mesh_wrappers: list[MeshWrapper]
    pcs_wrappers: list[PointCloudWrapper]
    rnd_wrappers: list[RoadNetworkWrapper]
    lss_wrappers: list[LineStringsWrapper]
    bld_wrappers: list[BuildingWrapper]
    rst_wrappers: list[RasterWrapper]
    mrst_wrappers: list[MultiRasterWrapper]
    geom_wrappers: list[GeometriesWrapper]

    bb: BoundingBox
    mts: int

    def __init__(self):

        self.obj_wrappers = []
        self.city_wrappers = []
        self.mesh_wrappers = []
        self.pcs_wrappers = []
        self.rnd_wrappers = []
        self.lss_wrappers = []
        self.bld_wrappers = []
        self.bud_wrappers = []
        self.rst_wrappers = []
        self.mrst_wrappers = []
        self.geom_wrappers = []

        self.mts = glGetIntegerv(GL_MAX_TEXTURE_SIZE)
        print(self.mts)

        info("Max texture size: " + str(self.mts))

    def add_mesh(self, name: str, mesh: Mesh, data: Any = None):
        """Append a mesh with data and/or colors to the scene"""
        if mesh is not None:
            info(f"Mesh called - {name} - added to scene")
            mesh_w = MeshWrapper(name=name, mesh=mesh, mts=self.mts, data=data)
            self.mesh_wrappers.append(mesh_w)
        else:
            warning(f"Mesh called - {name} - is None and not added to scene")

    def add_city(self, name: str, city: City):
        """Append a city with data and/or colors to the scene"""
        if city is not None:
            info(f"City called - {name} - added to scene")
            city_w = CityWrapper(name=name, city=city, mts=self.mts)
            self.city_wrappers.append(city_w)
        else:
            warning(f"City called - {name} - is None and not added to scene")

    def add_object(self, name: str, obj: Object):
        """Append a generic object with data and/or colors to the scene"""
        if obj is not None:
            info(f"Object called - {name} - added to scene")
            obj_w = ObjectWrapper(name=name, obj=obj, mts=self.mts)
            self.obj_wrappers.append(obj_w)
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
            self.pcs_wrappers.append(pc_w)
        else:
            warning(f"Point could called - {name} - is None and not added to scene")

    def add_roadnetwork(
        self,
        name: str,
        rn: Any,
        data: np.ndarray = None,
    ):
        """Append a RoadNetwork object to the scene"""
        if rn is not None:
            info(f"Road network called - {name} - added to scene")
            rn_w = RoadNetworkWrapper(name=name, rn=rn, data=data)
            self.rnd_wrappers.append(rn_w)
        else:
            warning(f"Road network called - {name} - is None and not added to scene")

    def add_linestrings(
        self,
        name: str,
        lss: list[LineString],
        data: Any = None,
    ):
        """Append a line strings list to the scene"""
        if lss is not None:
            info(f"List of LineStrings called - {name} - added to scene")
            lss_w = LineStringsWrapper(name, lss, self.mts, data)
            self.lss_wrappers.append(lss_w)
        else:
            warning(f"Road network called - {name} - is None and not added to scene")

        pass

    def add_building(self, name: str, building: Building):
        if building is not None:
            info(f"Building called - {name} - added to scene")
            bld_w = BuildingWrapper(name, building, self.mts)
            self.bld_wrappers.append(bld_w)
        else:
            warning(f"Building called - {name} - is None and not added to scene")

    def add_raster(self, name: str, raster: Raster):
        max_size = 10000
        if raster is not None:
            if np.max(raster.data.shape) > max_size:
                info(f"Multi raster called - {name} - added to scene")
                mrst_w = MultiRasterWrapper(name=name, raster=raster, max_size=max_size)
                self.mrst_wrappers.append(mrst_w)
            else:
                info(f"Raster called - {name} - added to scene")
                rst_w = RasterWrapper(name=name, raster=raster)
                self.rst_wrappers.append(rst_w)
        else:
            warning(f"Raster called - {name} - is None and not added to scene")

    def add_geometries(self, name: str, geometries: list[Geometry]):
        """Append a list of geometries"""
        if geometries is not None:
            info(f"Geometry collection called - {name} - added to scene")
            geom_wrp = GeometriesWrapper(name, geometries, self.mts)
            self.geom_wrappers.append(geom_wrp)
        else:
            warning(f"Failed to add geometry collection called - {name} - to scene")

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

        for obj_w in self.obj_wrappers:
            obj_w.preprocess_drawing(self.bb)

        for city_w in self.city_wrappers:
            city_w.preprocess_drawing(self.bb)

        for mesh_w in self.mesh_wrappers:
            mesh_w.preprocess_drawing(self.bb)

        for pc_w in self.pcs_wrappers:
            pc_w.preprocess_drawing(self.bb)

        for rn_w in self.rnd_wrappers:
            rn_w.preprocess_drawing(self.bb)

        for lss_w in self.lss_wrappers:
            lss_w.preprocess_drawing(self.bb)

        for bld_w in self.bld_wrappers:
            bld_w.preprocess_drawing(self.bb)

        for rst_w in self.rst_wrappers:
            rst_w.preprocess_drawing(self.bb)

        for mrst_w in self.mrst_wrappers:
            mrst_w.preprocess_drawing(self.bb)

        for geom_w in self.geom_wrappers:
            geom_w.preprocess_drawing(self.bb)

        info(f"Scene preprocessing completed successfully")
        return True

    def _calculate_bb(self):
        """Calculate bounding box of the scene"""

        # Flat array of vertices [x1,y1,z1,x2,y2,z2, ...]
        vertices = np.array([])

        for city_w in self.city_wrappers:
            vertices = np.concatenate((vertices, city_w.get_vertex_positions()), axis=0)

        for geom_w in self.geom_wrappers:
            vertices = np.concatenate((vertices, geom_w.get_vertex_positions()), axis=0)

        for obj_w in self.obj_wrappers:
            vertices = np.concatenate((vertices, obj_w.get_vertex_positions()), axis=0)

        for mw in self.mesh_wrappers:
            vertices = np.concatenate((vertices, mw.get_vertex_positions()), axis=0)

        for pc_w in self.pcs_wrappers:
            vertices = np.concatenate((vertices, pc_w.get_vertex_positions()), axis=0)

        for rn_w in self.rnd_wrappers:
            vertices = np.concatenate((vertices, rn_w.get_vertex_positions()), axis=0)

        for lss_w in self.lss_wrappers:
            vertices = np.concatenate((vertices, lss_w.get_vertex_positions()), axis=0)

        for bld_w in self.bld_wrappers:
            vertices = np.concatenate((vertices, bld_w.get_vertex_positions()), axis=0)

        for rst_w in self.rst_wrappers:
            vertices = np.concatenate((vertices, rst_w.get_vertex_positions()), axis=0)

        for mrst_w in self.mrst_wrappers:
            vertices = np.concatenate((vertices, mrst_w.get_vertex_positions()), axis=0)

        if len(vertices) > 3:  # At least 1 vertex
            bb = BoundingBox(vertices)
            return bb
        else:
            warning("No vertices found in scene")
            return None

    def _offset_picking_ids(self) -> None:
        id_offset = 0
        id_offsets = []
        id_offsets.append(0)

        for mesh in self.meshes:
            id_offset += np.max(mesh.vertices[9::10]) + 1
            id_offsets.append(id_offset)

        for i, mesh in enumerate(self.meshes):
            mesh.vertices[9::10] += id_offsets[i]
