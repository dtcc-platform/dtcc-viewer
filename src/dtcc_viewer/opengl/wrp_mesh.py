import numpy as np
from dtcc_core.model import Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.data_wrapper import MeshDataWrapper
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrapper import Wrapper
from pprint import PrettyPrinter
from typing import Any


class MeshWrapper(Wrapper):
    """Mesh attributes and associated data structured for the purpous of rendering.

    This class represents mesh data for rendering in an OpenGL window. It encapsulates
    information about the mesh's vertices, face indices, edge indices, and coloring options,
    and provides methods to restructure the data of a Mesh object to a format that fits
    the OpenGL functions.

    Attributes
    ----------
    data_dict : dict
        Dictionary of data for color calculation.
    vertices : np.ndarray
        Array of flattened vertex data with extended attributes (x, y, z, d1, d2, d3, nx, ny, nz, id).
    faces : np.ndarray
        Array of flattened face indices.
    edges : np.ndarray
        Array of flattened edge indices.
    name : str
        The name of the mesh data.
    shading : MeshShading
        Shading setting for the mesh.
    bb_local : BoundingBox
        Bounding box for this mesh.
    bb_global: BoundingBox
        Bounding box all objects in the entire scene.
    """

    vertices: np.ndarray
    faces: np.ndarray
    edges: np.ndarray
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox = None
    parts: Parts = None
    data_wrapper: MeshDataWrapper = None

    def __init__(
        self,
        name: str,
        mesh: Mesh,
        mts: int,
        data: Any = None,  # Dict, np.ndarray
        parts: Parts = None,
    ) -> None:
        """Initialize the MeshWrapper object.

        Parameters
        ----------
        name : str
            The name of the mesh wrapper.
        mesh : Mesh
            The underlying Mesh object from which to generate the mesh data.
        mts: int
            Max texture size for the data.
        data : Any, optional
            Additional mesh data (dict or array) for color calculation (default is None).
        parts : Parts, optional
            Faces grouped into a parts object for clickability (default is None).
        shading : MeshShading, optional
            Shading option (default is MeshShading.wireshaded).
        """
        self.name = name
        self.dict_data = {}
        self.parts = parts
        self.data = []
        self.data_wrapper = None

        fields = self._get_fields_data(mesh)
        self._append_data(mesh, mts, fields, data, parts)
        self._restructure_mesh(mesh)

        if self.parts is None:
            info("Submesh is None -> faces are used as defualt submeshes")
            self._create_default_mesh_parts(mesh)
        else:
            self._create_ids_from_mesh_parts(self.parts)  # Picking ids

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mesh_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())
        self._reformat_mesh()

    def _append_data(
        self,
        mesh: Mesh,
        mts: int,
        fields: dict,
        data: Any = None,
        parts: Parts = None,
    ):

        self.data_wrapper = MeshDataWrapper(mesh, mts)
        results = []

        # Add data from parts
        if parts is not None:
            if parts.attributes is not None:
                attribute_keys = parts.get_unique_attribute_keys()
                for key in attribute_keys:
                    attribute = parts.get_attribute_data(key)
                    success = self.data_wrapper.add_parts_data(key, attribute, parts)
                    results.append(success)

        # Add data from fileds
        if fields is not None:
            for key, value in fields.items():
                success = self.data_wrapper.add_data(key, value)
                results.append(success)

        # Add additional data
        if data is not None:
            if type(data) == dict:
                for key, value in data.items():
                    success = self.data_wrapper.add_data(key, value)
                    results.append(success)
            elif type(data) == np.ndarray:
                success = self.data_wrapper.add_data("Data", data)
                results.append(success)

        # Add default data if no data is provided
        if not np.any(results):
            self.data_wrapper.add_data("Vertex Z", mesh.vertices[:, 2])
            self.data_wrapper.add_data("Vertex X", mesh.vertices[:, 0])
            self.data_wrapper.add_data("Vertex Y", mesh.vertices[:, 1])

    def _restructure_mesh(self, mesh: Mesh):
        array_length = len(mesh.faces) * 3 * 9
        new_vertices = np.zeros(array_length)
        face_verts = mesh.vertices[mesh.faces.flatten()]

        c1 = face_verts[:-1]
        c2 = face_verts[1:]
        mask = np.ones(len(c1), dtype=bool)
        mask[2::3] = False  # [True, True, False, True, True, False, ...]
        cross_vecs = (c2 - c1)[mask]  # (v2 - v1), (v3 - v2)
        cross_p = np.cross(cross_vecs[::2], cross_vecs[1::2])  # (v2 - v1) x (v3 - v2)
        cross_p = cross_p / np.linalg.norm(cross_p, axis=1)[:, np.newaxis]  # normalize

        # Vertex coords
        vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=bool)
        mask = np.tile(vertex_mask, array_length // len(vertex_mask) + 1)[:array_length]
        new_vertices[mask] = face_verts.flatten()

        # Texel indices
        new_vertices[3::9] = self.data_wrapper.texel_x
        new_vertices[4::9] = self.data_wrapper.texel_y

        # Normal vecs
        normal_mask = np.array([0, 0, 0, 0, 0, 1, 1, 1, 0], dtype=bool)
        mask = np.tile(normal_mask, array_length // len(normal_mask) + 1)[:array_length]
        new_vertices[mask] = np.tile(cross_p, 3).flatten()
        new_faces = np.arange(array_length // 9)

        # Ids - Add face index to vertices as a default id
        faces_indices = np.arange(len(mesh.faces))
        face_indices_in_vertex_shape = np.repeat(faces_indices, 3)
        new_vertices[8::9] = face_indices_in_vertex_shape

        # np.set_printoptions(precision=3, suppress=True)
        # pp(new_vertices.reshape(-1, 10))

        new_edges = np.zeros(len(mesh.faces) * 6)
        new_edges[0::6] = new_faces[0::3]
        new_edges[1::6] = new_faces[1::3]
        new_edges[2::6] = new_faces[1::3]
        new_edges[3::6] = new_faces[2::3]
        new_edges[4::6] = new_faces[2::3]
        new_edges[5::6] = new_faces[0::3]

        self.vertices = new_vertices
        self.faces = new_faces
        self.edges = new_edges

    def _move_mesh_to_origin(self, bb: BoundingBox):
        # [x, y, z, tx, ty, nx, ny ,nz, id]
        v_count = len(self.vertices) // 9
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
        recenter_vec = np.tile(recenter_vec, v_count)
        self.vertices += recenter_vec

    def _move_mesh_to_zero_z(self, bb: BoundingBox):
        self.vertices[2::9] -= bb.zmin

    def get_vertex_positions(self):
        """Get the vertex positions of the mesh."""
        vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 9
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _reformat_mesh(self):
        """Reformat the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl types
        self.vertices = np.array(self.vertices, dtype="float32")
        self.edges = np.array(self.edges, dtype="uint32")
        self.faces = np.array(self.faces, dtype="uint32")

    def _flatten_mesh(self):
        """Flatten the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl implementation
        self.vertices = np.array(self.vertices, dtype="float32").flatten()
        self.edges = np.array(self.edges, dtype="uint32").flatten()
        self.faces = np.array(self.faces, dtype="uint32").flatten()

    def _create_ids_from_mesh_parts(self, parts: Parts):
        # Restructures submesh ids to the face index structure
        face_per_part = parts.face_end_indices - parts.face_start_indices + 1
        ids_in_parts_shape = parts.ids
        ids_in_faces_shape = np.repeat(ids_in_parts_shape, face_per_part)

        # Restructure the face ids to the vertex structure
        ids_in_vertex_shape = np.repeat(ids_in_faces_shape, 3)
        n_vertices = len(self.vertices) // 9

        if len(ids_in_vertex_shape) != n_vertices:
            warning(f"Submesh ids and vertices missmatch")
        else:
            # Replace default id with submesh id in the vertices
            info("Replacing default face ids with submesh ids in the vertices")
            self.vertices[8::9] = ids_in_vertex_shape

    def _create_default_mesh_parts(self, mesh):
        self.parts = Parts([mesh], ["Default"])

    def update_ids_from_parts(self):
        face_ids = self.parts.get_face_ids()

        # New vertex structure with 3 unique vertices per face
        vertex_ids = np.repeat(face_ids, 3)
        self.vertices[8::9] = vertex_ids

    def _get_fields_data(self, mesh: Mesh):
        data_dict = {}

        for field in mesh.fields:
            if field.dim == 1:
                data_dict[field.name] = field.values
            elif field.dim != 1:
                warning("Viewer only supports scalar field in current implementation")
                warning(f"Field '{field.name}' has dimension != 1. Skipping.")

        return data_dict
