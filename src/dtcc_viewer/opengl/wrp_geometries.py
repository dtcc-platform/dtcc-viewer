import numpy as np
from time import time
from collections import Counter
from dtcc_model import Geometry, Mesh, Surface, MultiSurface, PointCloud, Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.submeshes import Submeshes
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_linestrings import LineStringsWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from shapely.geometry import LineString
from dtcc_builder import *
from dtcc_builder.meshing import mesh_multisurfaces
import dtcc_builder as builder


class GeometriesWrapper:
    """GeometriesWrapper restructures a list of geomety for visualisation.

    This class wrapps a list of geometry objects for visualisation. It encapsulates
    information about buildings, roads etc, various meta data and provides methods to
    create a Mesh representation for the purpous of rendering.
    the OpenGL functions.

    Attributes
    ----------
    name : str
        The name of the geometry collection
    bb_local : BoundingBox
        Bounding box for this geometry collection.
    bb_global: BoundingBox
        Bounding box all objects in the entire scene.
    mesh_wrps : list[MeshWrapper]
        MeshWrapper for buildings
    lss_wrps : list[LineStringWrapper]
        LineStringWrapper for line strings
    pc_wrps : list[PointCloudWrapper]
        PointCloudWrapper for point clouds
    """

    name: str
    bb_global: BoundingBox = None
    lss_wrp: LineStringsWrapper
    mesh_wrps: list[MeshWrapper]
    pc_wrps: list[PointCloudWrapper]
    ms_wrps: list[MeshWrapper]
    srf_wrps: list[MeshWrapper]

    def __init__(self, name: str, geometries: list[Geometry], mts: int) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the geometry collection.
        geometries : list[Geometry]
            List of geometries.
        mts : int
            Max texture size (mts) for the OpenGL context.
        """
        self.name = name

        (meshes, lss, pcs, mss, srfs) = self._sort_geometries(geometries)

        self.mesh_wrps = self._create_mesh_wrappers(meshes, mts)
        self.srf_wrps = self._create_srf_wrappers(srfs, mts)
        self.ms_wrps = self._create_ms_wrappers(mss, mts)
        self.pc_wrps = self._create_pc_wrappers(pcs, mts)
        self.lss_wrp = self._create_lss_wrappers(lss, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        for mesh_wrp in self.mesh_wrps:
            mesh_wrp.preprocess_drawing(bb_global)

        for srf_wrp in self.srf_wrps:
            srf_wrp.preprocess_drawing(bb_global)

        for ms_wrp in self.ms_wrps:
            ms_wrp.preprocess_drawing(bb_global)

        for pc_wrp in self.pc_wrps:
            pc_wrp.preprocess_drawing(bb_global)

        if self.lss_wrp is not None:
            self.lss_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        for mesh_wrp in self.mesh_wrps:
            vertex_pos = mesh_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for srf_wrp in self.srf_wrps:
            vertex_pos = srf_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for ms_wrp in self.ms_wrps:
            vertex_pos = ms_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for pc_wrp in self.pc_wrps:
            vertex_pos = pc_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        if self.lss_wrp is not None:
            vertex_pos = self.lss_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _sort_geometries(self, geometries: list[Geometry]):
        meshes = []
        lss = []
        pcs = []
        mss = []
        srfs = []

        for geometry in geometries:
            if isinstance(geometry, Mesh):
                meshes.append(geometry)
            elif isinstance(geometry, PointCloud):
                pcs.append(geometry)
            elif isinstance(geometry, MultiSurface):
                mss.append(geometry)
            elif isinstance(geometry, Surface):
                srfs.append(geometry)
            elif isinstance(geometry, LineString):
                lss.append(geometry)

        return meshes, lss, pcs, mss, srfs

    def _create_mesh_wrappers(self, meshes: list[Mesh], mts: int):
        mesh_wrps = []
        for i, mesh in enumerate(meshes):
            mesh_wrps.append(MeshWrapper(f"mesh {i}", mesh, mts))

        return mesh_wrps

    def _create_ms_wrappers(self, mss: list[MultiSurface], mts: int):
        mss_wrps = []
        for i, ms in enumerate(mss):
            mesh = ms.mesh()
            mss_wrps.append(MeshWrapper(f"multi surface {i}", mesh, mts))

        return mss_wrps

    def _create_srf_wrappers(self, srfs: list[Surface], mts: int):
        srf_wrps = []
        for i, srf in enumerate(srfs):
            mesh = srf.mesh()
            srf_wrps.append(MeshWrapper(f"surface {i}", mesh, mts))

        return srf_wrps

    def _create_pc_wrappers(self, pcs: list[PointCloud], mts: int):
        pc_wrps = []
        for i, pc in enumerate(pcs):
            pc_wrps.append(PointCloudWrapper(f"point colud {i}", pc, mts))

        return pc_wrps

    def _create_lss_wrappers(self, lss: list[LineString], mts: int):
        lss_wrp = LineStringsWrapper(f"line strings", lss, mts)
        return lss_wrp
