import numpy as np
from dtcc_model import NewCity, MultiSurface, Surface, NewBuilding, Mesh, Terrain
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
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
    bb_local: BoundingBox
    bb_global: BoundingBox = None
    building_mw: MeshWrapper
    building_submeshes: list[Submesh]
    terrain_mw: MeshWrapper
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
        (mesh, submeshes) = self._generate_mesh_data(city)

        info("Buldings mesh generated")

        # Create MeshWrapper objects for buildings and terrain
        # self.terrain_mw = MeshWrapper("terrain", terrain_mesh, shading=shading)
        self.building_mw = MeshWrapper("buildings", mesh, shading=shading)

    def preprocess_drawing(self, bb_global: BoundingBox):
        # self.terrain_mw.preprocess_drawing(bb_global)
        self.bb_local = BoundingBox(self.building_mw.vertices)
        self.building_mw.preprocess_drawing(bb_global)

    def _get_terrain_mesh(self, city: NewCity):
        terrain_meshes = []
        for child in city.children.get(Terrain, []):
            terrain_mesh = child.geometry.get(GeometryType.MESH, None)
            if terrain_mesh is not None:
                terrain_meshes.append(terrain_mesh)

        terrain_mesh = concatenate_meshes(terrain_meshes)

        return terrain_mesh

    def _generate_mesh_data(self, city: NewCity):
        # Generate mesh data for terrain
        # terrain_mesh = self._get_terrain_mesh(city)
        # pp("Terrain mesh:")
        # pp(terrain_mesh)
        min = np.array([1e10, 1e10, 1e10])
        max = np.array([1e-10, 1e-10, 1e-10])
        counter = 0
        tot_f_count = 0
        all_blding_meshes = []
        submeshes = []
        s_fail_count = 0
        # Generate mesh data for buildings
        for building in city.buildings:
            buildnig_id = counter
            building_meshes = []
            flat_geom = building.flatten_geometry(GeometryType.LOD2)
            if isinstance(flat_geom, MultiSurface):
                for s in flat_geom.surfaces:
                    max = np.maximum(max, np.max(s.vertices, axis=0))
                    min = np.minimum(min, np.min(s.vertices, axis=0))
                    (mesh, normal) = surface_2_mesh(s.vertices)
                    if mesh is not None:
                        building_meshes.append(mesh)
                    else:
                        s_fail_count += 1

            if len(building_meshes) > 0:
                # Concatenate all building meshes into one mesh
                building_mesh = concatenate_meshes(building_meshes)
                all_blding_meshes.append(building_mesh)

                bld_f_count = len(building_mesh.faces)
                tot_f_count += bld_f_count
                face_index_1 = (tot_f_count - bld_f_count) - 1
                face_index_2 = tot_f_count - 1

                # Clickable subset of the mesh, here at the level of a building
                submesh = Submesh(face_index_1, face_index_2, buildnig_id)
                submesh.add_meta_data("id", building.id)
                submeshes.append(submesh)

                counter += 1

        print("Min point:" + str(min))
        print("Max point:" + str(max))
        print("Failed surface meshing count: " + str(s_fail_count))

        mesh = concatenate_meshes(all_blding_meshes)

        return mesh, submeshes
