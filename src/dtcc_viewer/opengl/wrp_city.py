import numpy as np
from collections import Counter
from dtcc_model import City, MultiSurface, Surface, Building, Mesh, Terrain
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl.utils import BoundingBox, Shading, Results, Submeshes
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import Submesh, concatenate_meshes, surface_2_mesh
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper


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
    shading : MeshShading
        Shading setting for the mesh.
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
    shading: Shading
    bb_global: BoundingBox = None
    building_mw: MeshWrapper = None
    building_submeshes: Submeshes
    terrain_mw: MeshWrapper = None
    terrain_submeshes: Submeshes

    def __init__(self, name: str, city: City) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh data.
        city : City
            City object from which to generate the mesh data to view.
        shading : MeshShading, optional
            Shading option (default is MeshShading.wireshaded).
        """
        self.name = name
        self.shading = Shading.wireshaded  # Default shading
        self.dict_data = {}

        # Read the city model and generate the mesh geometry for buildings and terrain
        (t_mesh, t_submeshes) = self._get_terrain_mesh(city)
        (b_mesh, b_submeshes) = self._generate_building_mesh(city)

        # Set the global ids for the entire scene
        if t_submeshes is not None:
            offset = np.max(t_submeshes.ids) + 1
            b_submeshes.offset_ids(offset)

        if t_mesh is not None:
            self.terrain_mw = MeshWrapper("terrain", t_mesh, submeshes=t_submeshes)

        if b_mesh is not None:
            self.building_mw = MeshWrapper("buildings", b_mesh, submeshes=b_submeshes)

        info("CityWrapper initialized")

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.terrain_mw is not None:
            self.terrain_mw.preprocess_drawing(bb_global)

        if self.building_mw is not None:
            self.building_mw.preprocess_drawing(bb_global)

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
        meshes = []
        uuids = []
        results = []

        # Generate mesh data for buildings
        for building in city.buildings:
            building_meshes = []
            uuid = building.id
            flat_geom = self.get_highest_lod_building(building)
            if isinstance(flat_geom, MultiSurface):
                for srf in flat_geom.surfaces:
                    (mesh, result) = surface_2_mesh(srf.vertices)
                    results.append(result)
                    if mesh is not None:
                        building_meshes.append(mesh)

            if len(building_meshes) > 0:
                # Concatenate all building mesh parts into one building mesh
                building_mesh = concatenate_meshes(building_meshes)
                meshes.append(building_mesh)
                uuids.append(uuid)

        results_type_count = Counter(results)
        info("Results from triangluation:")
        for result_type, count in results_type_count.items():
            info(f" - {result_type.name}: {count}")

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
