import numpy as np
from time import time
from collections import Counter
from dtcc_model import Geometry, Mesh, Surface, MultiSurface, PointCloud, Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_linestring import MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_bounds import BoundsWrapper
from dtcc_viewer.opengl.wrp_surface import SurfaceWrapper, MultiSurfaceWrapper
from shapely.geometry import LineString, MultiLineString
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_builder import *
from dtcc_builder.meshing import mesh_multisurfaces
import dtcc_builder as builder


class GeometriesWrapper(Wrapper):
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
    mls_wrps: list[MultiLineStringWrapper]
    ls_wrps: list[LineStringWrapper]
    mesh_wrps: list[MeshWrapper]
    pc_wrps: list[PointCloudWrapper]
    ms_wrps: list[MultiSurfaceWrapper]
    srf_wrps: list[SurfaceWrapper]
    bnds_wrps: list[BoundsWrapper]

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

        (meshes, mls, lss, pcs, mss, srfs, bds) = self._sort_geometries(geometries)

        self.mesh_wrps = self._create_mesh_wrappers(meshes, mts)
        self.srf_wrps = self._create_srf_wrappers(srfs, mts)
        self.ms_wrps = self._create_ms_wrappers(mss, mts)
        self.pc_wrps = self._create_pc_wrappers(pcs, mts)
        self.mls_wrps = self._create_mls_wrappers(mls, mts)
        self.ls_wrps = self._create_ls_wrappers(lss, mts)
        self.bnds_wrps = self._create_bnd_wrappers(bds, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        for mesh_wrp in self.mesh_wrps:
            mesh_wrp.preprocess_drawing(bb_global)

        for srf_wrp in self.srf_wrps:
            srf_wrp.preprocess_drawing(bb_global)

        for ms_wrp in self.ms_wrps:
            ms_wrp.preprocess_drawing(bb_global)

        for pc_wrp in self.pc_wrps:
            pc_wrp.preprocess_drawing(bb_global)

        for mls_wrp in self.mls_wrps:
            mls_wrp.preprocess_drawing(bb_global)

        for ls_wrp in self.ls_wrps:
            ls_wrp.preprocess_drawing(bb_global)

        for bnd_wrp in self.bnds_wrps:
            bnd_wrp.preprocess_drawing(bb_global)

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

        for ms_wrp in self.ms_wrps:
            vertex_pos = ms_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for ls_wrp in self.ls_wrps:
            vertex_pos = ls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for bnd_wrp in self.bnds_wrps:
            vertex_pos = bnd_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for mls_wrp in self.mls_wrps:
            vertex_pos = mls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _sort_geometries(self, geometries: list[Geometry]):
        meshes = []
        mls = []
        lss = []
        pcs = []
        mss = []
        srfs = []
        bds = []

        for geometry in geometries:
            if isinstance(geometry, Mesh):
                meshes.append(geometry)
            elif isinstance(geometry, PointCloud):
                pcs.append(geometry)
            elif isinstance(geometry, MultiSurface):
                mss.append(geometry)
            elif isinstance(geometry, Surface):
                srfs.append(geometry)
            elif isinstance(geometry, MultiLineString):
                mls.append(geometry)
            elif isinstance(geometry, LineString):
                lss.append(geometry)
            elif isinstance(geometry, Bounds):
                bds.append(geometry)
            else:
                warning(f"Type {type(geometry)} is not of type Geometry. Skipping.")

        return meshes, mls, lss, pcs, mss, srfs, bds

    def _create_mesh_wrappers(self, meshes: list[Mesh], mts: int):
        mesh_wrps = []
        for i, mesh in enumerate(meshes):
            if mesh is not None:
                mesh_wrps.append(MeshWrapper(f"mesh {i}", mesh, mts))

        return mesh_wrps

    def _create_ms_wrappers(self, mss: list[MultiSurface], mts: int):
        mss_wrps = []
        for i, ms in enumerate(mss):
            mss_wrps.append(MultiSurfaceWrapper(f"multi surface {i}", ms, mts))

        return mss_wrps

    def _create_srf_wrappers(self, srfs: list[Surface], mts: int):
        srf_wrps = []
        for i, srf in enumerate(srfs):
            srf_wrps.append(SurfaceWrapper(f"surface {i}", srf, mts))

        return srf_wrps

    def _create_pc_wrappers(self, pcs: list[PointCloud], mts: int):
        pc_wrps = []
        for i, pc in enumerate(pcs):
            if pc is not None:
                pc_wrps.append(PointCloudWrapper(f"point colud {i}", pc, mts))

        return pc_wrps

    def _create_mls_wrappers(self, mls: list[MultiLineString], mts: int):
        mls_wrps = []
        for i, mls in enumerate(mls):
            if mls is not None:
                mls_wrps.append(
                    MultiLineStringWrapper(f"multi line strings {i}", mls, mts)
                )
        return mls_wrps

    def _create_ls_wrappers(self, lss: list[LineString], mts: int):
        ls_wrps = []
        for i, ls in enumerate(lss):
            if ls is not None:
                ls_wrps.append(LineStringWrapper(f"line strings {i}", ls, mts))

        return ls_wrps

    def _create_bnd_wrappers(self, bds: list[Bounds], mts: int):
        bnd_wrps = []
        for i, bd in enumerate(bds):
            if bd is not None:
                bnd_wrps.append(BoundsWrapper(f"bounds {i}", bd, mts))

        return bnd_wrps
