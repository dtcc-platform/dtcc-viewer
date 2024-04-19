import numpy as np
from time import time
from collections import Counter
from dtcc_model import City, MultiSurface, Building, Mesh, Terrain
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.submeshes import Submeshes
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_builder import *
from dtcc_builder.meshing import mesh_multisurfaces
import dtcc_builder as builder


class CityWrapper:
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
    building_mw: MeshWrapper = None
    building_submeshes: Submeshes
    terrain_mw: MeshWrapper = None
    terrain_submeshes: Submeshes

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
        (t_mesh, t_submeshes) = self._get_terrain_mesh(city)
        (b_mesh, b_submeshes) = self._generate_building_mesh(city)

        quantities = city.quantities

        # Set the global ids for the entire scene
        if t_submeshes is not None:
            offset = np.max(t_submeshes.ids) + 1
            if b_submeshes is not None:
                b_submeshes.offset_ids(offset)

        if t_mesh is not None:
            name = "terrain"
            self.terrain_mw = MeshWrapper(name, t_mesh, mts, quantities, t_submeshes)

        if b_mesh is not None:
            name = "buildings"
            self.building_mw = MeshWrapper(name, b_mesh, mts, quantities, b_submeshes)

        info("CityWrapper initialized")

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.terrain_mw is not None:
            self.terrain_mw.preprocess_drawing(bb_global)

        if self.building_mw is not None:
            self.building_mw.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertices = np.array([])

        if self.terrain_mw is not None:
            vertex_pos = self.terrain_mw.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        if self.building_mw is not None:
            vertex_pos = self.building_mw.get_vertex_positions()
            vertices = np.concatenate((vertices, vertex_pos), axis=0)

        return vertices

    def _get_terrain_mesh(self, city: City):
        meshes = []
        uuids = []
        terrain_list = city.children[Terrain]

        for terrain in terrain_list:
            mesh = terrain.geometry.get(GeometryType.MESH, None)
            uuid = terrain.id
            if mesh is not None:
                meshes.append(mesh)
                uuids.append(uuid)

        if len(meshes) == 0:
            info("No terrain mesh found in city model")
            return None, None
        else:
            submeshes = Submeshes(meshes, uuids)
            mesh = concatenate_meshes(meshes)
            info(f"Terrain mesh with {len(mesh.faces)} faces was found")
            return mesh, submeshes

        return None, None

    def _generate_building_mesh(self, city: City):
        uuids = []
        mss = []
        for building in city.buildings:
            uuid = building.id
            ms = self.get_highest_lod_building(building)
            if isinstance(ms, MultiSurface):
                mss.append(ms)
                uuids.append(uuid)

        tic = time()
        meshes = [ms.mesh() for ms in mss]
        info(f"Meshing complete. Time elapsed: {time() - tic:0.4f} seconds")

        # tic = time()
        # meshes2 = mesh_multisurfaces(mss)
        # info(f"Time elapsed: {time() - tic:0.4f} seconds")

        if len(meshes) == 0:
            info("No building meshes found in city model")
            return None, None
        else:
            submeshes = Submeshes(meshes, uuids)
            mesh = concatenate_meshes(meshes)
            info(f"Mesh with {len(mesh.faces)} faces was retrieved from buildings")
            return mesh, submeshes

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
