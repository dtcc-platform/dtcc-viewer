import numpy as np
from collections import Counter
from dtcc_model import NewCity, MultiSurface, Surface, NewBuilding, Mesh, Terrain
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading, Results
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl_viewer.utils import Submesh, concatenate_meshes, surface_2_mesh
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper


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
    shading: MeshShading
    bb_global: BoundingBox = None
    building_mw: MeshWrapper = None
    building_submeshes: list[Submesh]
    terrain_mw: MeshWrapper = None
    terrain_submeshes: list[Submesh]

    def __init__(
        self,
        name: str,
        city: NewCity,
        shading: MeshShading = MeshShading.wireshaded,
    ) -> None:
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
        self.shading = shading
        self.dict_data = {}

        submeshes = []

        # Read the city model and generate the mesh geometry for buildings and terrain
        (building_mesh, submeshes) = self._generate_building_mesh(city)

        terrain_mesh = self._get_terrain_mesh(city)

        if terrain_mesh is not None:
            self.terrain_mw = MeshWrapper("terrain", terrain_mesh, shading=shading)

        if building_mesh is not None:
            self.building_mw = MeshWrapper("buildings", building_mesh, shading=shading)

        info("CityWrapper initialized")

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.terrain_mw is not None:
            self.terrain_mw.preprocess_drawing(bb_global)

        if self.building_mw is not None:
            self.building_mw.preprocess_drawing(bb_global)

    def _get_terrain_mesh(self, city: NewCity):
        meshes = []
        terrain_list = city.children[Terrain]

        for terrain in terrain_list:
            mesh = terrain.geometry.get(GeometryType.MESH, None)
            if mesh is not None:
                meshes.append(mesh)

        if len(meshes) == 0:
            info("No terrain mesh found in city model")
            return None
        else:
            mesh = concatenate_meshes(meshes)
            info(
                f"Terrain mesh with {len(mesh.faces)} faces and {len(mesh.vertices)} vertices generated "
            )
            return mesh

    def _generate_building_mesh(self, city: NewCity):
        counter = 0
        tot_f_count = 0
        submeshes = []
        all_meshes = []
        results = []
        meshing_fail_count = 0
        meshing_attm_count = 0
        count_tria = 0
        # Generate mesh data for buildings
        for building in city.buildings:
            buildnig_id = counter
            building_meshes = []
            flat_geom = building.flatten_geometry(GeometryType.LOD2)
            if isinstance(flat_geom, MultiSurface):
                for s in flat_geom.surfaces:
                    (mesh, result) = surface_2_mesh(s.vertices)
                    meshing_attm_count += 1
                    results.append(result)
                    if mesh is not None:
                        building_meshes.append(mesh)
                    else:
                        meshing_fail_count += 1

            if len(building_meshes) > 0:
                # Concatenate all building meshes into one mesh
                building_mesh = concatenate_meshes(building_meshes)
                all_meshes.append(building_mesh)

                bld_f_count = len(building_mesh.faces)
                tot_f_count += bld_f_count
                face_index_1 = (tot_f_count - bld_f_count) - 1
                face_index_2 = tot_f_count - 1

                # Clickable subset of the mesh, here at the level of a building
                submesh = Submesh(face_index_1, face_index_2, buildnig_id)
                submesh.add_meta_data("id", building.id)
                submeshes.append(submesh)
                counter += 1

        results_type_count = Counter(results)
        info("Results from triangluation:")
        for result_type, count in results_type_count.items():
            info(f" - {result_type.name}: {count}")

        if len(all_meshes) == 0:
            info("No building meshes found in city model")
            return None, None
        else:
            mesh = concatenate_meshes(all_meshes)
            info(
                f"Building mesh with {len(mesh.faces)} faces and {len(mesh.vertices)} vertices generated "
            )

        return mesh, submeshes
