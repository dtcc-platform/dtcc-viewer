import numpy as np
from dtcc_model import Mesh
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, Shading, Submeshes
from dtcc_viewer.logging import info, warning
from pprint import PrettyPrinter


class MeshWrapper:
    """Mesh attributes and associated data structured for the purpous of rendering.

    This class represents mesh data for rendering in an OpenGL window. It encapsulates
    information about the mesh's vertices, face indices, edge indices, and coloring options,
    and provides methods to restructure the data of a Mesh object to a format that fits
    the OpenGL functions.

    Attributes
    ----------
    color_by : int
        Color mode based on ColorBy enumeration (e.g., ColorBy.vertex_colors).
    mesh_colors : np.ndarray
        Array of vertex colors for the mesh.
    vertices : np.ndarray
        Array of flattened vertex data with extended attributes (x, y, z, r, g, b, nx, ny, nz).
    face_indices : np.ndarray
        Array of flattened face indices.
    edge_indices : np.ndarray
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

    dict_data: dict
    vertices: np.ndarray
    faces: np.ndarray
    edges: np.ndarray
    name: str
    shading: Shading
    bb_local: BoundingBox
    bb_global: BoundingBox = None
    submeshes: Submeshes = None

    def __init__(
        self,
        name: str,
        mesh: Mesh,
        data: Any = None,  # Dict or np.ndarray
        submeshes: Submeshes = None,
        shading: Shading = Shading.wireshaded,
    ) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh wrapper.
        mesh : Mesh
            The underlying Mesh object from which to generate the mesh data.
        data : Any, optional
            Additional mesh data (dict or array) for color calculation (default is None).
        colors : np.ndarray, optional
            Colors for vertices or faces (default is None).
        submeshes : Submeshes, optional
            Faces grouped into a submeshes object for clickability (default is None).
        shading : MeshShading, optional
            Shading option (default is MeshShading.wireshaded).
        """
        self.name = name
        self.shading = shading
        self.dict_data = {}

        self._restructure_data(mesh, data)
        self._restructure_mesh(mesh)

        if submeshes is None:
            info("Submesh is None faces are used as defualt submeshes")
        else:
            self._create_ids_from_submeshes(submeshes)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mesh_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.get_vertex_positions())
        self._reformat_mesh()

    def _restructure_data(self, mesh: Mesh, data: Any):
        # Structure the data in the dict so that there are three data slots for each
        # vertex, and three uniqie vertces for each face. This is necessary in order
        # to enable to color each face individually. This structure is also needed for
        # the vertices so that each face can have individual normals so that shading
        # can be computed correctly.

        n_faces = len(mesh.faces)

        new_dict = {
            "slot0": np.zeros(n_faces * 3),
            "slot1": np.zeros(n_faces * 3),
            "slot2": np.zeros(n_faces * 3),
        }

        if type(data) == dict:
            self.dict_data = self._restructure_data_dict(mesh, data, new_dict)
        elif type(data) == np.ndarray:
            self.dict_data = self._restructure_data_array(mesh, data, new_dict)
        else:
            info("No data provided for mesh.")
            info("Default (x ,y ,z) - coords per vertex data appended.")
            face_verts = mesh.vertices[mesh.faces.flatten()]
            new_dict["slot0"] = face_verts[:, 0]
            new_dict["slot1"] = face_verts[:, 1]
            new_dict["slot2"] = face_verts[:, 2]
            self.dict_data = new_dict

    def _restructure_data_array(self, mesh: Mesh, data: np.ndarray, new_dict: dict):
        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)

        if len(data) == n_vertices:
            face_data = data[mesh.faces.flatten()]
            new_dict["slot0"] = face_data
        elif len(data) == n_faces:
            face_indices = np.arange(0, len(mesh.faces))
            face_indices = np.repeat(face_indices, 3)  # Repeat to match vertex count
            face_data = data[face_indices]
            new_dict["slot0"] = face_data
        else:
            pass

        return new_dict

    def _restructure_data_dict(self, mesh: Mesh, data_dict: dict, new_dict: dict):
        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)
        data_slots = len(new_dict)
        counter = 0

        for key in data_dict.keys():
            data = data_dict[key]
            if counter < data_slots:
                if len(data) == n_vertices:
                    # Data matching the number of vertices
                    face_data = data[mesh.faces.flatten()]
                    new_dict["slot" + str(counter)] = face_data
                elif len(data) == n_faces:
                    # Data matching the number of faces
                    face_indices = np.arange(0, len(mesh.faces))
                    face_indices = np.repeat(face_indices, 3)
                    face_data = data[face_indices]
                    new_dict["slot" + str(counter)] = face_data
                else:
                    info(f"Data for {key} does not match vertex or face count")
            else:
                info(f"Data for {key} does not fit in available slots")
            counter += 1

        return new_dict

    def _restructure_mesh(self, mesh: Mesh):
        array_length = len(mesh.faces) * 3 * 10
        new_vertices = np.zeros(array_length)
        face_verts = mesh.vertices[mesh.faces.flatten()]

        c1 = face_verts[:-1]
        c2 = face_verts[1:]
        mask = np.ones(len(c1), dtype=bool)
        mask[2::3] = False  # [True, True, False, True, True, False, ...]
        cross_vecs = (c2 - c1)[mask]  # (v2 - v1), (v3 - v2)
        cross_p = np.cross(cross_vecs[::2], cross_vecs[1::2])  # (v2 - v1) x (v3 - v2)
        cross_p = cross_p / np.linalg.norm(cross_p, axis=1)[:, np.newaxis]  # normalize
        vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0], dtype=bool)
        data_mask = np.array([0, 0, 0, 1, 1, 1, 0, 0, 0, 0], dtype=bool)
        normal_mask = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 0], dtype=bool)
        id_mask = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1], dtype=bool)
        mask = np.tile(vertex_mask, array_length // len(vertex_mask) + 1)[:array_length]
        new_vertices[mask] = face_verts.flatten()
        mask = np.tile(data_mask, array_length // len(data_mask) + 1)[:array_length]
        new_vertices[mask] = np.array([0.0, 0.0, 0.0] * len(mesh.faces) * 3).flatten()
        mask = np.tile(normal_mask, array_length // len(normal_mask) + 1)[:array_length]
        new_vertices[mask] = np.tile(cross_p, 3).flatten()
        new_faces = np.arange(array_length // 10)

        # Add face index to vertices as a default id
        faces_indices = np.arange(len(mesh.faces))
        face_indices_in_vertex_shape = np.repeat(faces_indices, 3)
        mask = np.tile(id_mask, array_length // len(normal_mask) + 1)[:array_length]
        new_vertices[mask] = face_indices_in_vertex_shape

        # np.set_printoptions(precision=3, suppress=True)
        # pp(new_vertices.reshape(-1, 10))

        # Insert data from restructured dict
        new_vertices[3::10] = self.dict_data["slot0"]
        new_vertices[4::10] = self.dict_data["slot1"]
        new_vertices[5::10] = self.dict_data["slot2"]

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
        # [x, y, z, r, g, b, nx, ny ,nz]
        v_count = len(self.vertices) // 10
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0, 0]), axis=0)
        recenter_vec = np.tile(recenter_vec, v_count)
        self.vertices += recenter_vec

    def get_vertex_positions(self):
        """Get the vertex positions of the mesh."""
        vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0], dtype=bool)
        v_count = len(self.vertices) // 10
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

    def _create_ids_from_submeshes(self, submeshes: Submeshes):
        # Restructures submesh ids to the face index structure
        face_per_submesh = submeshes.face_end_indices - submeshes.face_start_indices + 1
        ids_in_submesh_shape = submeshes.ids + submeshes.id_offset
        ids_in_faces_shape = np.repeat(ids_in_submesh_shape, face_per_submesh)

        # Restructure the face ids to the vertex structure
        ids_in_vertex_shape = np.repeat(ids_in_faces_shape, 3)
        n_vertices = len(self.vertices) // 10

        if len(ids_in_vertex_shape) != n_vertices:
            warning(f"Submesh ids and vertices missmatch")
        else:
            # Replace default id with submesh id in the vertices
            info("Replacing default face ids with submesh ids in the vertices")
            id_mask = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1], dtype=bool)
            mask = np.tile(id_mask, len(self.vertices) // 10)[: len(self.vertices)]
            self.vertices[mask] = ids_in_vertex_shape

    def _create_default_submeshes(self, mesh):
        # The default structure is such that each face is represented as a submesh
        # which makes the faces clickable in the viewer.

        # faces = [f1v1, f1v2, f1v3, f2v1, f2v2, f2v3, ...]
        n_faces = len(self.faces) // 3

        # Start and end indices are the same, only one face is grouped in each submesh
        start_faces = np.arange(0, n_faces)
        end_faces = np.arange(0, n_faces)
        id = np.arange(0, n_faces)
        self.submeshes = Submeshes(start_faces, end_faces, id)
