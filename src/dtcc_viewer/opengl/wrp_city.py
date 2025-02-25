import numpy as np
from time import time
from collections import Counter
from dtcc_core.model import City, MultiSurface, Surface, Building, Mesh, Terrain
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_core.model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_core.builder import *
from dtcc_core.builder.meshing import mesh_multisurfaces
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.wrp_grid import GridWrapper, VolumeGridWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
import dtcc_core.builder as builder

from dtcc_viewer.logging import info, debug

from tqdm import tqdm


class CityWrapper(Wrapper):
    """CityWrapper restructures data for the purpous of rendering.

    This class wrapps a city object for rendering in an OpenGL window. It encapsulates
    information about buildings, roads etc, various meta data and provides methods to
    create a Mesh representation for the purpous of rendering.
    the OpenGL functions.

    Attributes
    ----------
    name : str
        The name of the city
    bb_local : BoundingBox
        Bounding box for this mesh.
    bb_global: BoundingBox
        Bounding box all objects in the entire scene.
    building_mw : MeshWrapper
        MeshWrapper for buildings
    building_submeshes : list[Submesh]
        List of Submeshes used to defined clickable objects in the buildings mesh
    terrain_mw : MeshWrapper
        MeshWrapper for terrain
    terrain_submeshes : list[Submesh]
        List of Submeshes used to defined clickable objects in the terrain mesh
    """

    name: str
    bb_global: BoundingBox = None
    mesh_bld: MeshWrapper = None
    mesh_ter: MeshWrapper = None
    grid_wrps: list[GridWrapper] = []
    vgrid_wrps: list[VolumeGridWrapper] = []
    pc_wrps: list[PointCloudWrapper] = []

    def __init__(self, name: str, city: City, mts: int) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh data.
        city : City
            City object from which to generate the mesh data to view.
        mts : int
            Max texture size (mts) for the OpenGL context.
        """
        self.name = name
        self.dict_data = {}

        # Read the city model and generate the mesh geometry for buildings and terrain
        (mesh_t, parts_t) = self._get_terrain_mesh(city)
        (mesh_b, parts_b) = self._generate_building_mesh(city)

        if mesh_t is not None:
            self.mesh_ter = MeshWrapper("terrain", mesh_t, mts, None, parts_t)

        if mesh_b is not None:
            self.mesh_bld = MeshWrapper("buildings", mesh_b, mts, None, parts_b)

        grids = self._get_grids(city)
        for i, grid in enumerate(grids):
            if grid is not None:
                self.grid_wrps.append(GridWrapper(f"grid {i}", grid, mts))

        vgrids = self._get_volume_grids(city)
        for vgrid in vgrids:
            if vgrid is not None:
                self.vgrid_wrps.append(VolumeGridWrapper(f"vgrid {i}", vgrid, mts))

        pcs = self._get_pcs(city)
        for i, pc in enumerate(pcs):
            if pc is not None:
                self.pc_wrps.append(PointCloudWrapper(f"pc {i}", pc, mts))

        info("CityWrapper initialized")

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_ter is not None:
            self.mesh_ter.preprocess_drawing(bb_global)

        if self.mesh_bld is not None:
            self.mesh_bld.preprocess_drawing(bb_global)

        for grid in self.grid_wrps:
            grid.preprocess_drawing(bb_global)

        for vgrid in self.vgrid_wrps:
            vgrid.preprocess_drawing(bb_global)

        for pc in self.pc_wrps:
            pc.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        if self.mesh_ter is not None:
            vertex_pos = self.mesh_ter.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        if self.mesh_bld is not None:
            vertex_pos = self.mesh_bld.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for grid in self.grid_wrps:
            vertex_pos = grid.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for vgrid in self.vgrid_wrps:
            vertex_pos = vgrid.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        for pc in self.pc_wrps:
            vertex_pos = pc.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _get_terrain_mesh(self, city: City):
        meshes = []
        uuids = []
        attributes = []
        terrain_list = city.children[Terrain]

        for terrain in terrain_list:
            mesh = terrain.geometry.get(GeometryType.MESH, None)
            uuid = terrain.id
            if mesh is not None:
                meshes.append(mesh)
                uuids.append(uuid)
                attributes.append(terrain.attributes)

        if len(meshes) == 0:
            info("No terrain mesh found in city model")
            return None, None
        else:
            submeshes = Parts(meshes, uuids)
            mesh = concatenate_meshes(meshes)
            info(f"Terrain mesh with {len(mesh.faces)} faces was found")
            return mesh, submeshes

        return None, None

    def _generate_building_mesh(self, city: City):
        uuids = []
        mss = []
        attributes = []
        for building in tqdm(
            city.buildings, desc="Perparing buildings", unit=" building", ncols=120
        ):
            uuid = building.id
            ms = self.get_highest_lod_building(building)
            if isinstance(ms, MultiSurface):
                mss.append(ms)
                uuids.append(uuid)
                attributes.append(building.attributes)
            elif isinstance(ms, Surface):
                mss.append(MultiSurface(surfaces=[ms]))
                uuids.append(uuid)
                attributes.append(building.attributes)

        info(f"Found {len(mss)} building(s) in city model")

        valid_meshes = []
        valid_uuids = []
        valid_attrib = []
        tic = time()
        for i, ms in enumerate(mss):
            mesh = ms.mesh(clean=False)
            if mesh is not None:
                valid_meshes.append(mesh)
                valid_uuids.append(uuids[i])
                valid_attrib.append(attributes[i])

        info(f"Meshing complete. Time elapsed: {time() - tic:0.4f} seconds")

        if len(valid_meshes) == 0:
            info("No building meshes found in city model")
            return None, None
        else:
            parts = Parts(valid_meshes, valid_uuids, valid_attrib)
            mesh = concatenate_meshes(valid_meshes)
            info(f"Mesh with {len(mesh.faces)} faces was retrieved from buildings")
            return mesh, parts

        return None, None

    def get_highest_lod_building(self, building: Building):
        lods = [
            GeometryType.LOD3,
            GeometryType.LOD2,
            GeometryType.LOD1,
            GeometryType.LOD0,
        ]

        for lod in lods:
            flat_geom = building.flatten_geometry(lod)
            if flat_geom is not None:
                return flat_geom

        return None

    def _get_grids(self, city: City):
        geom = city.geometry.get("grid", None)  # TODO: Change to geometry type
        if type(geom) != list:
            geom = [geom]

        info(f"Found {len(geom)} grid(s) in city model")
        return geom

    def _get_volume_grids(self, city: City):
        geom = city.geometry.get("volume_grid", None)  # TODO: Change to geometry type
        if type(geom) != list:
            geom = [geom]

        info(f"Found {len(geom)} volume grid(s) in city model")
        return geom

    def _get_pcs(self, city: City):
        geom = city.geometry.get(GeometryType.POINT_CLOUD, None)

        if type(geom) != list:
            geom = [geom]

        info(f"Found {len(geom)} pc(s) in city model")
        return geom
