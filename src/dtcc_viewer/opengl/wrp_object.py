import numpy as np
from collections import Counter
from dtcc_model import NewCity, MultiSurface, Surface, NewBuilding, Mesh, Terrain
from dtcc_model import Bounds, Object
from dtcc_model.object.object import GeometryType
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl.utils import BoundingBox, Shading, Results
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import Submesh, concatenate_meshes, surface_2_mesh
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper


class ObjectWrapper:
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
    bb_local: BoundingBox = None
    bb_global: BoundingBox = None
    mesh_wrapper: MeshWrapper = None
    submeshes: list[Submesh]

    def __init__(
        self,
        name: str,
        obj: Object,
        shading: Shading = Shading.wireshaded,
        lod: GeometryType = GeometryType.LOD2,
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

        # Extract meshes from the object and its children
        meshes = self._extract_mesh_from_mesh(obj)
        meshes_ms = self._extract_mesh_from_multisuface(obj, lod)
        meshes.extend(meshes_ms)
        mesh = concatenate_meshes(meshes)
        submeshes = self._create_submeshes(meshes)

        if mesh is not None:
            self.mesh_wrapper = MeshWrapper("Object mesh", mesh, shading=shading)

        # Extract line strings from the object and its children
        # lineStrings = self._extract_linestrings(obj, lod)

        warning("ObjectWrapper not yet implemented!")

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrapper is not None:
            self.mesh_wrapper.preprocess_drawing(bb_global)

    def _extract_linestrings(self, obj: Object, lod: GeometryType):
        lineString = obj.flatten_geometry(GeometryType.LINESTRING)

        polygon = obj.flatten_geometry(GeometryType.POLYGON)
        bounds = obj.flatten_geometry(GeometryType.BOUNDS)

        pass

    def _extract_geometry(self, geom_type: GeometryType, obj: Object):
        geometries = []
        geom = obj.flatten_geometry(geom_type, None)
        geometries.append(geom)
        for child_list in obj.children.values():
            for child in child_list:
                child_geom = child.geometry.get(GeometryType.MESH, None)
                if child_geom is not None:
                    geometries.append(child_geom)

        return geometries

    def _extract_mesh_from_mesh(self, obj: Object):
        meshes = self._extract_geometry(GeometryType.MESH, obj)
        return meshes

    def _extract_mesh_from_multisuface(self, obj: Object, lod: GeometryType):
        if lod == GeometryType.LOD1:
            ms_list = self._extract_geometry(GeometryType.LOD1, obj)
            (meshes, results) = self._triangulate_multisurfaces(ms_list)
        elif lod == GeometryType.LOD2:
            ms_list = self._extract_geometry(GeometryType.LOD2, obj)
            (meshes, results) = self._triangulate_multisurfaces(ms_list)
        elif lod == GeometryType.LOD3:
            ms_list = self._extract_geometry(GeometryType.LOD3, obj)
            (meshes, results) = self._triangulate_multisurfaces(ms_list)

        results_type_count = Counter(results)
        info("Results from triangluation:")
        for result_type, count in results_type_count.items():
            info(f" - {result_type.name}: {count}")

        return meshes

    def _triangulate_multisurfaces(ms_list: list[MultiSurface]):
        meshes = []
        results = []
        for ms in ms_list:
            for s in ms.surfaces:
                (mesh, result) = surface_2_mesh(s.vertices)
                results.append(result)
                if mesh is not None:
                    meshes.append(mesh)
        return meshes, results

    def _create_submeshes(meshes: list[Mesh]):
        submeshes = []
        f_start = 0
        for i, mesh in enumerate(meshes):
            f_count = len(mesh.faces)
            submesh = Submesh(f_start, f_start + f_count, i)
            f_start += f_count
            submeshes.append(submesh)

        return submeshes
