import numpy as np
from dtcc_model import Object, Surface, MultiSurface
from dtcc_model.object.object import GeometryType
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox, Shading
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes, concatenate_pcs
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_multilinestring import MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.wrapper import Wrapper
from shapely.geometry import LineString, MultiLineString


class ObjectWrapper(Wrapper):
    """ObjectWrapper restructures data for the purpous of rendering.

    This class wrapps a generic object for rendering in an OpenGL window. It enables the
    viewing of the object and all its childe objects a restructures the data for the
    purpous of rendering with OpenGL.

    Attributes
    ----------
    name : str
        The name of the object
    shading : MeshShading
        Shading setting for the rendering.
    bb_local : BoundingBox
        Bounding box for this object and its children.
    bb_global: BoundingBox
        Bounding box all objects in the entire scene.
    mesh_wrapper : MeshWrapper
        MeshWrapper for the object and all its children
    submeshes : list[Submesh]
        List of Submeshes used to defined clickable objects in the mesh
    """

    name: str
    shading: Shading
    bb_global: BoundingBox = None
    mesh_wrp_1: MeshWrapper = None
    mesh_wrp_2: MeshWrapper = None
    mesh_wrp_3: MeshWrapper = None
    lss_wrp: LineStringWrapper = None
    pc_wrp: PointCloudWrapper = None

    def __init__(self, name: str, obj: Object, mts: int) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh data.
        obj : Object
            Generic Object which can hold a range of different geometries.
        mts : int
            Max texture size for the OpenGL context.
        """
        self.name = name
        self.shading = Shading.WIRESHADED
        self.dict_data = {}

        # Extract meshes from the object and its children
        (mesh_1, parts_1) = self._extract_mesh_from_mesh(obj)
        (mesh_2, parts_2) = self._extract_mesh_from_ms(obj)

        quantities = obj.quantities

        if mesh_1 is not None:
            self.mesh_wrp_1 = MeshWrapper("MESH", mesh_1, mts, quantities, parts_1)
        if mesh_2 is not None:
            self.mesh_wrp_2 = MeshWrapper("MS", mesh_2, mts, quantities, parts_2)

        # Extract line strings from the object and its children
        lineStrings = self._extract_linestrings(obj)

        if lineStrings is not None:
            if isinstance(lineStrings, LineString):
                self.lss_wrp = LineStringWrapper("LineStrings", lineStrings, mts)
            elif isinstance(lineStrings, MultiLineString):
                self.lss_wrp = MultiLineStringWrapper("Multi LS", lineStrings, mts)

        # Extract line strings from the object and its children
        pc = self._extract_point_cloud(obj)
        if pc is not None:
            self.pc_wrp = PointCloudWrapper("PointCloud", pc, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp_1 is not None:
            self.mesh_wrp_1.preprocess_drawing(bb_global)
        if self.mesh_wrp_2 is not None:
            self.mesh_wrp_2.preprocess_drawing(bb_global)
        if self.lss_wrp is not None:
            self.lss_wrp.preprocess_drawing(bb_global)
        if self.pc_wrp is not None:
            self.pc_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        if self.mesh_wrp_1 is not None:
            vertex_pos = self.mesh_wrp_1.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        if self.mesh_wrp_2 is not None:
            vertex_pos = self.mesh_wrp_2.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        if self.lss_wrp is not None:
            vertex_pos = self.lss_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _extract_point_cloud(self, obj: Object):
        geom = obj.flatten_geometry(GeometryType.POINT_CLOUD)
        pcs = []
        if geom is not None:
            if isinstance(geom, list):
                for pc in geom:
                    if isinstance(pc, PointCloud):
                        pcs.append(pc)
                return concatenate_pcs(pcs)
            elif isinstance(geom, PointCloud):
                return geom
        return None

    def _extract_linestrings(self, obj: Object):
        line_string = obj.flatten_geometry(GeometryType.LINESTRING)

        if isinstance(line_string, LineString):
            return line_string
        elif isinstance(line_string, list):
            lss = []
            for ls in line_string:
                if isinstance(ls, LineString):
                    lss.append(ls)
            return MultiLineString(lss)
        else:
            return None

    def _extract_mesh_from_mesh(self, obj: Object):
        meshes = obj.flatten_geometry(GeometryType.MESH)
        if meshes is not None:
            if not isinstance(meshes, list):
                meshes = [meshes]
            mesh = concatenate_meshes(meshes)
            ids = [str(num) for num in np.arange(0, len(meshes)).tolist()]
            parts = Parts(meshes, ids)
            return mesh, parts

        return None, None

    def _extract_mesh_from_ms(self, obj: Object):
        ms_list = self.get_highest_lod_ms_list(obj)
        if ms_list is None:
            return None, None

        meshes = self._triangulate_multisurfaces(ms_list)
        if len(meshes) == 0:
            return None, None

        mesh = concatenate_meshes(meshes)
        ids = [str(num) for num in np.arange(0, len(meshes)).tolist()]
        parts = Parts(meshes, ids)

        return mesh, parts

    def _triangulate_multisurfaces(self, ms_list: list[MultiSurface]):
        meshes = []
        for ms in ms_list:
            mesh = ms.mesh()
            if mesh is not None:
                meshes.append(mesh)
        return meshes

    def _triangulate_surfaces(self, srf_list: list[Surface]):
        meshes = []
        for s in srf_list:
            mesh = s.mesh()
            if mesh is not None:
                meshes.append(mesh)
        return meshes

    def get_highest_lod_ms_list(self, obj: Object):
        lods = [
            GeometryType.LOD3,
            GeometryType.LOD2,
            GeometryType.LOD1,
            GeometryType.LOD0,
        ]
        mss = []
        for lod in lods:
            geom = obj.flatten_geometry(lod)
            if geom is not None:
                if isinstance(geom, list):
                    for ms in geom:
                        if isinstance(ms, MultiSurface):
                            mss.append(ms)
                elif isinstance(geom, MultiSurface):
                    mss.append(geom)

        return mss
