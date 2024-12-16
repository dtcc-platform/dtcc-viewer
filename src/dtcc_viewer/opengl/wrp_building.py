from distutils.command.build import build

import numpy as np
from dtcc_core.model import City, MultiSurface, Building, Mesh, Surface
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.logging import info, warning
# from dtcc_viewer.opengl.utils import surface_2_mesh, concatenate_meshes
from dtcc_core.model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrapper import Wrapper

from dtcc_core.builder.meshing import mesh_multisurface, mesh_surface, mesh_multisurfaces

class BuildingWrapper(Wrapper):
    """BuildingWrapper restructures data for a building for the purpous of rendering.

    This class wraps a building object for rendering in an OpenGL window. It
    encapsulates various meta data and provides methods to create a Mesh representation
    for the purpous of rendering. the OpenGL functions.

    Attributes
    ----------
    name : str
        The name of the city
    bb_global: BoundingBox
        Bounding box all objects in the entire scene.
    mesh_wrapper : MeshWrapper
        MeshWrapper for the building
    """

    name: str
    bb_global: BoundingBox = None
    mesh_wrp: MeshWrapper = None

    def __init__(self, name: str, building: Building, mts: int) -> None:
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

        mesh = self._get_building_mesh(building)

        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts)

    def _get_building_mesh(self, building: Building):
        flat_geom = self._get_highest_lod_building(building)

        building_meshes = []
        flat_geom = self._get_highest_lod_building(building)
        building_meshes = None
        if isinstance(flat_geom, MultiSurface):
           building_meshes = mesh_multisurface(flat_geom)
        elif isinstance(flat_geom, Surface):
            building_meshes = mesh_surface(flat_geom)
        elif isinstance(flat_geom, Mesh):
            building_meshes = flat_geom
        if building_meshes is not None:
            return building_meshes
        return None

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp is not None:
            self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        vertex_pos = self.mesh_wrp.get_vertex_positions()
        return vertex_pos

    def _get_terrain_mesh(self, city: City):
        pass

    def _generate_building_mesh(self, city: City):
        pass

    def _get_highest_lod_building(self, building: Building):
        lods = [
            GeometryType.MESH,
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
