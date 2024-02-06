import numpy as np
from dtcc_model import Mesh
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
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

    color_by: int
    colors: np.ndarray
    dict_color_by: dict
    dict_colors: dict
    dict_data: dict
    vertices: np.ndarray
    faces: np.ndarray
    edges: np.ndarray
    name: str
    shading: MeshShading
    bb_local: BoundingBox
    bb_global: BoundingBox = None

    def __init__(
        self,
        name: str,
        mesh: Mesh,
        data: np.ndarray = None,
        shading: MeshShading = MeshShading.wireshaded,
    ) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh wrapper.
        mesh : Mesh
            The underlying Mesh object from which to generate the mesh data.
        data : np.ndarray, optional
            Additional mesh data for color calculation (default is None).
        colors : np.ndarray, optional
            Colors for vertices or faces (default is None).
        shading : MeshShading, optional
            Shading option (default is MeshShading.wireshaded).
        """
        self.name = name
        self.shading = shading
        self.dict_data = {}

        self._generate_mesh_colors(mesh, data)
        self._restructure_dicts(mesh)
        self._restructure_mesh(mesh)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mesh_to_origin(self.bb_global)
        self.bb_local = BoundingBox(self.vertices)
        self._reformat_mesh()

    def _generate_mesh_colors(self, mesh: Mesh, data: Any = None):
        """Generate mesh colors based on the provided data."""

        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)
        n_data = 0

        # First priority is coloring by provided data dict.
        if isinstance(data, dict):
            info(f"Coloring mesh by data dictionary")
            if self._generate_dict_colors(data, n_vertices, n_faces):
                return True

        # If there is data for coloring
        if data is not None:
            info(f"Coloring mesh by data")
            n_data = len(data)
            key = "Data array"
            if n_data == n_vertices:  # Generate colors base on provided vertex data
                self.dict_data[key] = np.array(data)
                return True
            elif n_data == n_faces:  # Generate colors base on provided face data
                self.dict_data[key] = np.array(data)
                return True
            else:
                warning(f"Color data does not match vertex of face count: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # If no vertex of face colors are appended to the mesh and no data is provided
        # the mesh is colored by vertex height.
        info(f"Coloring mesh by default colors")
        key = "Default colors"
        default_data = mesh.vertices[:, 2]
        self.dict_data[key] = default_data

        return True

    def _normalise_colors(self, colors: np.ndarray):
        """Normalize colors to the range [0, 1] if necessary."""
        # If the max color value is larger then 1 it is assumed that the color range is 0-255
        max = np.max(colors)
        if max > 1.0:
            colors /= 255.0
        return colors

    def _generate_dict_colors(self, data_dict: dict, n_vert: int, n_face: int):
        # return default colors to be added to the mesh
        keys = data_dict.keys()
        for key in keys:
            row_data = data_dict[key]
            if len(row_data) == n_vert:
                self.dict_data[key] = np.array(row_data)
            elif len(row_data) == n_face:
                self.dict_data[key] = np.array(row_data)

        return True

    def _restructure_dicts(self, mesh: Mesh):
        # Structure the color data in the dict so that there are three colors for each
        # face. This is necessary in order to be able to color each face individually.
        # This structure is also neede for the vertices so that each face can have
        # individual normals so that shading can be computed correctly.

        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)
        d1, d2, d3 = 0, 0, 0
        new_dict_data = dict.fromkeys(self.dict_data.keys())

        for key in self.dict_data.keys():
            if self.dict_data[key] is not None:
                new_dict_data[key] = []
            else:
                new_dict_data[key] = None

        for face_index, face in enumerate(mesh.faces):
            for key in self.dict_data.keys():
                if self.dict_data[key] is not None:
                    data = self.dict_data[key]
                    if len(data) == n_vertices:
                        d1 = data[face[0]]
                        d2 = data[face[1]]
                        d3 = data[face[2]]
                        new_dict_data[key].extend([d1, d2, d3])
                    elif len(data) == n_faces:
                        d1 = data[face_index]
                        new_dict_data[key].extend([d1, d1, d1])

        # Saving data with the new format
        for key in self.dict_data.keys():
            if self.dict_data[key] is not None:
                self.dict_data[key] = np.array(new_dict_data[key])

        return True

    def _restructure_dicts_2(self, mesh: Mesh):
        # Structure the color data in the dict so that there are three colors for each
        # face. This is necessary in order to be able to color each face individually.
        # This structure is also neede for the vertices so that each face can have
        # individual normals so that shading can be computed correctly.

        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)
        d1, d2, d3 = 0, 0, 0
        new_dict_data = dict.fromkeys(self.dict_data.keys())

        for key in self.dict_data.keys():
            if self.dict_data[key] is not None:
                new_dict_data[key] = []
            else:
                new_dict_data[key] = None

        for face_index, face in enumerate(mesh.faces):
            for key in self.dict_data.keys():
                if self.dict_data[key] is not None:
                    data = self.dict_data[key]
                    if len(data) == n_vertices:
                        d1 = data[face[0]]
                        d2 = data[face[1]]
                        d3 = data[face[2]]
                        new_dict_data[key].extend([d1, d2, d3])
                    elif len(data) == n_faces:
                        d1 = data[face_index]
                        new_dict_data[key].extend([d1, d1, d1])

        # Saving data with the new format
        for key in self.dict_data.keys():
            if self.dict_data[key] is not None:
                self.dict_data[key] = np.array(new_dict_data[key])

        return True

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
        vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=bool)
        color_mask = np.array([0, 0, 0, 1, 1, 1, 0, 0, 0], dtype=bool)
        normal_mask = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1], dtype=bool)
        mask = np.tile(vertex_mask, array_length // len(vertex_mask) + 1)[:array_length]
        new_vertices[mask] = face_verts.flatten()
        mask = np.tile(color_mask, array_length // len(color_mask) + 1)[:array_length]
        new_vertices[mask] = np.array([1.0, 0.0, 1.0] * len(mesh.faces) * 3).flatten()
        mask = np.tile(normal_mask, array_length // len(normal_mask) + 1)[:array_length]
        new_vertices[mask] = np.tile(cross_p, 3).flatten()
        new_faces = np.arange(array_length // 9)

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
        v_count = len(self.vertices) // 9
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
        recenter_vec = np.tile(recenter_vec, v_count)
        self.vertices += recenter_vec

    def get_vertex_positions(self):
        """Get the vertex positions of the mesh."""
        vertex_mask = np.array(
            [True, True, True, False, False, False, False, False, False]
        )
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
