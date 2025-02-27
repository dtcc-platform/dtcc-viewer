import numpy as np
from time import time
from collections import Counter
from dtcc_core.model import Geometry, Mesh, Surface, MultiSurface, PointCloud, Bounds
from dtcc_core.model import VolumeMesh, Grid, VolumeGrid
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_core.model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_grid import GridWrapper, VolumeGridWrapper
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_linestring import MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_bounds import BoundsWrapper
from dtcc_viewer.opengl.wrp_surface import SurfaceWrapper, MultiSurfaceWrapper
from dtcc_viewer.opengl.wrp_volume_mesh import VolumeMeshWrapper
from dtcc_core.model import LineString, MultiLineString
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_core.builder import *
from dtcc_core.builder.meshing import mesh_multisurfaces
import dtcc_core.builder as builder


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
    mls_wrps : list[MultiLineStringWrapper]
        MultiLineStringWrapper for multi line strings
    lss_wrps : list[LineStringWrapper]
        LineStringWrapper for a line string
    mesh_wrps : list[MeshWrapper]
        MeshWrapper for buildings
    pc_wrps : list[PointCloudWrapper]
        PointCloudWrapper for point clouds
    ms_wrps : list[MultiSurfaceWrapper]
        MultiSurfaceWrapper for multi surfaces
    srf_wrps : list[SurfaceWrapper]
        SurfaceWrapper for surfaces
    bnds_wrps : list[BoundsWrapper]
        BoundsWrapper for bounds
    vmesh_wrps : list[VolumeMeshWrapper]
        VolumeMeshWrapper for volume meshes
    grd_wrps : list[GridWrapper]
        GridWrapper for grids
    vgrd_wrps : list[VolumeGridWrapper]
        VolumeGridWrapper for volume grids
    """

    name: str
    mls_wrps: list[MultiLineStringWrapper]
    lss_wrps: list[LineStringWrapper]
    mesh_wrps: list[MeshWrapper]
    pc_wrps: list[PointCloudWrapper]
    ms_wrps: list[MultiSurfaceWrapper]
    srf_wrps: list[SurfaceWrapper]
    bnds_wrps: list[BoundsWrapper]
    vmesh_wrps: list[VolumeMeshWrapper]
    grd_wrps: list[GridWrapper]
    vgrd_wrps: list[VolumeGridWrapper]

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

        (mhs, mls, lss, pcs, mss, srfs, bds, vmsh, grds, vgrds) = self._sort_geometries(
            geometries
        )

        self.mesh_wrps = self._create_mesh_wrappers(mhs, mts)
        self.srf_wrps = self._create_srf_wrappers(srfs, mts)
        self.ms_wrps = self._create_ms_wrappers(mss, mts)
        self.pc_wrps = self._create_pc_wrappers(pcs, mts)
        self.mls_wrps = self._create_mls_wrappers(mls, mts)
        self.lss_wrps = self._create_ls_wrappers(lss, mts)
        self.bnds_wrps = self._create_bnd_wrappers(bds, mts)
        self.vmesh_wrps = self._create_vmesh_wrappers(vmsh, mts)
        self.grd_wrps = self._create_grd_wrappers(grds, mts)
        self.vgrd_wrps = self._create_vgrd_wrappers(vgrds, mts)

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

        for ls_wrp in self.lss_wrps:
            ls_wrp.preprocess_drawing(bb_global)

        for bnd_wrp in self.bnds_wrps:
            bnd_wrp.preprocess_drawing(bb_global)

        for vmesh_wrp in self.vmesh_wrps:
            vmesh_wrp.preprocess_drawing(bb_global)

        for grd_wrp in self.grd_wrps:
            grd_wrp.preprocess_drawing(bb_global)

        for vgrd_wrp in self.vgrd_wrps:
            vgrd_wrp.preprocess_drawing(bb_global)

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

        for ls_wrp in self.lss_wrps:
            vertex_pos = ls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for bnd_wrp in self.bnds_wrps:
            vertex_pos = bnd_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for mls_wrp in self.mls_wrps:
            vertex_pos = mls_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for vmesh_wrp in self.vmesh_wrps:
            vertex_pos = vmesh_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for grd_wrp in self.grd_wrps:
            vertex_pos = grd_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for vgrd_wrp in self.vgrd_wrps:
            vertex_pos = vgrd_wrp.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _sort_geometries(self, geometries: list[Geometry]):
        msh = []
        mls = []
        lss = []
        pcs = []
        mss = []
        srfs = []
        bds = []
        vmsh = []
        grds = []
        vgrds = []

        for geometry in geometries:
            if isinstance(geometry, Mesh):
                msh.append(geometry)
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
            elif isinstance(geometry, VolumeMesh):
                vmsh.append(geometry)
            elif isinstance(geometry, Grid):
                grds.append(geometry)
            elif isinstance(geometry, VolumeGrid):
                vgrds.append(geometry)
            else:
                warning(f"Type {type(geometry)} is not of type Geometry. Skipping.")

        return msh, mls, lss, pcs, mss, srfs, bds, vmsh, grds, vgrds

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

    def _create_vmesh_wrappers(self, wmhs: list[VolumeMesh], mts: int):
        vmesh_wrps = []
        for i, vmsh in enumerate(wmhs):
            if vmsh is not None:
                vmesh_wrps.append(VolumeMeshWrapper(f"volume mesh {i}", vmsh, mts))

        return vmesh_wrps

    def _create_grd_wrappers(self, wgd: list[Grid], mts: int):
        grd_wrps = []
        for i, gd in enumerate(wgd):
            if gd is not None:
                grd_wrps.append(GridWrapper(f"grid {i}", gd, mts))

        return grd_wrps

    def _create_vgrd_wrappers(self, wgd: list[VolumeGrid], mts: int):
        vgrd_wrps = []
        for i, gd in enumerate(wgd):
            if gd is not None:
                vgrd_wrps.append(VolumeGridWrapper(f"volume grid {i}", gd, mts))

        return vgrd_wrps
