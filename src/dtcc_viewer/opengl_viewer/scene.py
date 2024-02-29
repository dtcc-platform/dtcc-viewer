import numpy as np
from dtcc_viewer.opengl_viewer.wrp_city import CityWrapper
from dtcc_viewer.opengl_viewer.wrp_object import ObjectWrapper
from dtcc_viewer.opengl_viewer.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl_viewer.wrp_roadnetwork import RoadNetworkWrapper
from dtcc_viewer.opengl_viewer.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl_viewer.wrp_linestrings import LineStringsWrapper
from dtcc_viewer.opengl_viewer.utils import BoundingBox, Shading
from dtcc_model import Mesh, PointCloud, RoadNetwork, City, Object
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
    """

    obj_wrappers: list[ObjectWrapper]
    city_wrappers: list[CityWrapper]
    mesh_wrappers: list[MeshWrapper]
    pcs_wrappers: list[PointCloudWrapper]
    rnd_wrappers: list[RoadNetworkWrapper]
    lss_wrappers: list[LineStringsWrapper]
    bb: BoundingBox

    def __init__(self):
        self.obj_wrappers = []
        self.city_wrappers = []
        self.mesh_wrappers = []
        self.pcs_wrappers = []
        self.rnd_wrappers = []
        self.lss_wrappers = []

    def add_mesh(
        self,
        name: str,
        mesh: Mesh,
        data: Any = None,
        shading: Shading = Shading.wireshaded,
    ):
        """Append a mesh with data and/or colors to the scene"""
        if mesh is not None:
            info(f"Mesh called - {name} - added to scene")
            mesh_w = MeshWrapper(name=name, mesh=mesh, data=data, shading=shading)
            self.mesh_wrappers.append(mesh_w)
        else:
            warning(f"Mesh called - {name} - is None and not added to scene")

    def add_city(
        self,
        name: str,
        city: City,
        shading: Shading = Shading.wireshaded,
    ):
        """Append a city with data and/or colors to the scene"""
        if city is not None:
            info(f"City called - {name} - added to scene")
            city_w = CityWrapper(name=name, city=city, shading=shading)
            self.city_wrappers.append(city_w)
        else:
            warning(f"City called - {name} - is None and not added to scene")

    def add_object(
        self,
        name: str,
        obj: Object,
        shading: Shading = Shading.wireshaded,
    ):
        """Append a generic object with data and/or colors to the scene"""
        if obj is not None:
            info(f"Object called - {name} - added to scene")
            obj_w = ObjectWrapper(name=name, obj=obj, shading=shading)
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
            pc_w = PointCloudWrapper(name=name, pc=pc, size=size, data=data)
            self.pcs_wrappers.append(pc_w)
        else:
            warning(f"Point could called - {name} - is None and not added to scene")

    def add_roadnetwork(
        self,
        name: str,
        rn: RoadNetwork,
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
            lss_w = LineStringsWrapper(name=name, lss=lss, data=data)
            self.lss_wrappers.append(lss_w)
        else:
            warning(f"Road network called - {name} - is None and not added to scene")

        pass

    def preprocess_drawing(self):
        """Preprocess bounding box calculation for all scene objects"""

        # Calculate bounding box for the entire scene including the vector that is
        # used to center move everything to the origin.
        self.bb = self._calculate_bb()

        if self.bb is None:
            warning("No bounding box found for scene.")
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

        info(f"Scene preprocessing completed successfully")
        return True

    def _calculate_bb(self):
        """Calculate bounding box of the scene"""

        # Flat array of vertices [x1,y1,z1,x2,y2,z2, ...]
        vertices = np.array([])

        for obj_w in self.obj_wrappers:
            if obj_w.mesh_wrapper is not None:
                vertex_pos = obj_w.mesh_wrapper.get_vertex_positions()
                vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for city_w in self.city_wrappers:
            if city_w.terrain_mw is not None:
                vertex_pos = city_w.terrain_mw.get_vertex_positions()
                vertices = np.concatenate((vertices, vertex_pos), axis=0)

            if city_w.building_mw is not None:
                vertex_pos = city_w.building_mw.get_vertex_positions()
                vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for mw in self.mesh_wrappers:
            vertex_pos = mw.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for pc_w in self.pcs_wrappers:
            vertices = np.concatenate((vertices, pc_w.points), axis=0)

        for rn_w in self.rnd_wrappers:
            vertex_pos = rn_w.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for lss_w in self.lss_wrappers:
            vertex_pos = lss_w.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

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
