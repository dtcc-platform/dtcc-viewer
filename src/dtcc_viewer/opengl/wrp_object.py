import numpy as np
from dtcc_model import MultiSurface
from dtcc_model import Object
from dtcc_model.object.object import GeometryType
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox, Shading
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import concatenate_meshes, surface_2_mesh
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_linestrings import LineStringsWrapper
from dtcc_viewer.opengl.submeshes import Submeshes
from shapely.geometry import LineString


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
    mesh_wrp_1: MeshWrapper = None
    mesh_wrp_2: MeshWrapper = None
    lsw: LineStringsWrapper = None

    def __init__(self, name: str, obj: Object) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh data.
        city : City
            City object from which to generate the mesh data to view.
        """
        self.name = name
        self.shading = Shading.WIRESHADED
        self.dict_data = {}

        # Extract meshes from the object and its children
        (mesh_1, submeshes_1) = self._extract_mesh_from_mesh(obj)
        (mesh_2, submeshes_2) = self._extract_mesh_from_multisuface(obj)

        if mesh_1 is not None:
            self.mesh_wrp_1 = MeshWrapper("Mesh", mesh_1, submeshes_1)
        if mesh_2 is not None:
            self.mesh_wrp_2 = MeshWrapper("Multi surface", mesh_2, submeshes_2)

        # Extract line strings from the object and its children
        lineStrings = self._extract_linestrings(obj)

        if lineStrings is not None:
            self.lineStringsWrapper = LineStringsWrapper("LineStrings", lineStrings)

        warning("ObjectWrapper not yet implemented!")

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp_1 is not None:
            self.mesh_wrp_1.preprocess_drawing(bb_global)
        if self.mesh_wrp_2 is not None:
            self.mesh_wrp_2.preprocess_drawing(bb_global)
        if self.lineStringsWrapper is not None:
            self.lineStringsWrapper.preprocess_drawing(bb_global)

    def _extract_linestrings(self, obj: Object):
        line_string = obj.flatten_geometry(GeometryType.LINESTRING)

        if isinstance(line_string, list):
            return line_string
        elif isinstance(line_string, LineString):
            return [line_string]
        else:
            return None

    def _extract_mesh_from_mesh(self, obj: Object):
        meshes = obj.flatten_geometry(GeometryType.MESH)
        if meshes is not None:
            if not isinstance(meshes, list):
                meshes = [meshes]
            mesh = concatenate_meshes(meshes)
            ids = [str(num) for num in np.arange(0, len(meshes)).tolist()]
            submeshes = Submeshes(meshes, ids)
            return mesh, submeshes

        return None, None

    def _extract_mesh_from_multisuface(self, obj: Object):
        ms_list = self.get_highest_lod_ms_list(obj)
        if ms_list is None:
            return None, None

        (meshes, results) = self._triangulate_multisurfaces(ms_list)
        mesh = concatenate_meshes(meshes)
        ids = [str(num) for num in np.arange(0, len(meshes)).tolist()]
        submeshes = Submeshes(meshes, ids)

        return mesh, submeshes

    def _triangulate_multisurfaces(self, ms_list: list[MultiSurface]):
        meshes = []
        results = []
        for ms in ms_list:
            for s in ms.surfaces:
                (mesh, result) = surface_2_mesh(s.vertices)
                results.append(result)
                if mesh is not None:
                    meshes.append(mesh)
        return meshes, results

    def get_highest_lod_ms_list(self, obj: Object):
        lods = [
            GeometryType.LOD3,
            GeometryType.LOD2,
            GeometryType.LOD1,
            GeometryType.LOD0,
        ]

        for lod in lods:
            ms_list = obj.flatten_geometry(lod)
            if ms_list is not None:
                if isinstance(ms_list, list):
                    return ms_list
                elif isinstance(ms_list, MultiSurface):
                    return [ms_list]

        return None
