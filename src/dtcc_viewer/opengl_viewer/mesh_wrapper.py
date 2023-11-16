import numpy as np
from dtcc_model import Mesh
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
from dtcc_viewer.logging import info, warning


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
            The name of the mesh data.
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
        self._move_mesh_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.vertices)
        self._flatten_mesh()

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

    def _restructure_mesh(self, mesh: Mesh):
        """Restructure the mesh data for OpenGL rendering."""

        # Vertex format that suits the opengl data structure:
        # [x, y, z, r, g, b, nx, ny ,nz]
        new_faces = []
        new_vertices = []
        new_edges = []
        v_index = 0

        # The restructuring makes sure that each faces has its own vertices. That is
        # nessary in order to be able to color each face individually and to be able to
        # use individual face normals for each mesh.
        for face in mesh.faces:
            v1 = mesh.vertices[face[0], :]
            v2 = mesh.vertices[face[1], :]
            v3 = mesh.vertices[face[2], :]

            # Magenta as predefined color for faces
            c = np.array([1.0, 0.0, 1.0])

            v1 = np.concatenate((v1, c), axis=0)
            v2 = np.concatenate((v2, c), axis=0)
            v3 = np.concatenate((v3, c), axis=0)

            f_normal = np.cross(v2[0:3] - v1[0:3], v3[0:3] - v1[0:3])
            f_normal = f_normal / np.linalg.norm(f_normal)

            v1 = np.concatenate((v1, f_normal), axis=0)
            v2 = np.concatenate((v2, f_normal), axis=0)
            v3 = np.concatenate((v3, f_normal), axis=0)

            new_vertices.append(v1)
            new_vertices.append(v2)
            new_vertices.append(v3)

            new_faces.append([v_index, v_index + 1, v_index + 2])
            new_edges.append([v_index, v_index + 1])
            new_edges.append([v_index + 1, v_index + 2])
            new_edges.append([v_index + 2, v_index])

            v_index += 3

        self.vertices = np.array(new_vertices)
        self.faces = np.array(new_faces)
        self.edges = np.array(new_edges)

    def _move_mesh_to_origin_multi(self, bb: BoundingBox):
        # [x, y, z, r, g, b, nx, ny ,nz]
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
        self.vertices += recenter_vec

    def _flatten_mesh(self):
        """Flatten the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl implementation
        self.vertices = np.array(self.vertices, dtype="float32").flatten()
        self.edges = np.array(self.edges, dtype="uint32").flatten()
        self.faces = np.array(self.faces, dtype="uint32").flatten()
