import numpy as np
from dtcc_model import Mesh
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
from dtcc_viewer.logging import info, warning


class MeshData:
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
        colors: np.ndarray = None,
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
        self.dict_colors = {}
        self.dict_color_by = {}

        [self.color_by, self.colors] = self._generate_mesh_colors(mesh, data, colors)
        [self.vertices, self.faces, self.edges] = self._restructure_mesh(mesh)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self.vertices = self._move_mesh_to_origin_multi(self.vertices, self.bb_global)
        self.bb_local = BoundingBox(self.vertices)

        [self.vertices, self.edges, self.faces] = self._flatten_mesh(
            self.vertices, self.edges, self.faces
        )

    def _generate_mesh_colors(
        self, mesh: Mesh, data: Any = None, input_colors: np.ndarray = None
    ):
        """Generate mesh colors based on the provided data.

        Parameters
        ----------
        mesh : Mesh
            The Mesh object from which to generate colors.
        data : np.ndarray or dictionaty, optional
            Array or dictinary of data for color calculation (default is None).

        Returns
        -------
        int
            Color mode based on ColorBy enumeration (e.g., ColorBy.vertex_colors).
        np.ndarray
            Array of vertex colors for the mesh.
        """

        n_vertex_colors = len(mesh.vertex_colors)
        n_face_colors = len(mesh.face_colors)
        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)
        n_data = 0

        # First priority is coloring by provided data dict.
        if isinstance(data, dict):
            info(f"Coloring mesh by data dictionary")
            if self._generate_dict_colors(data, n_vertices, n_faces):
                keys = list(self.dict_colors.keys())
                colors_from_dict = self.dict_colors[keys[0]]
                color_by = ColorBy.dict
                return color_by, colors_from_dict

        # Second priority is coloring by provided color array.
        if input_colors is not None:
            info(f"Coloring mesh by input colors")
            n_input_colors = len(input_colors)
            colors_from_input = self._normalise_colors(input_colors)
            colors_from_input = np.array(input_colors)
            if n_input_colors == n_vertices:
                color_by = ColorBy.vertex
                return color_by, colors_from_input
            elif n_input_colors == n_faces:
                color_by = ColorBy.face
                return color_by, colors_from_input
            else:
                warning(f"Input colors do not match vertex/face count: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # If there is data for coloring
        if data is not None:
            info(f"Coloring mesh by data")
            n_data = len(data)
            colors_from_data = calc_colors_rainbow(data)
            if n_data == n_vertices:  # Generate colors base on provided vertex data
                color_by = ColorBy.vertex
                return color_by, colors_from_data
            elif n_data == n_faces:  # Generate colors base on provided face data
                color_by = ColorBy.face
                return color_by, colors_from_data
            else:
                warning(f"Color data does not match vertex of face count: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # No colors provided. Colors are then retrieved from the mesh either base on
        # vertices or face colors.
        if input_colors is None and data is None:
            info(f"Coloring appended mesh colors")
            if n_vertex_colors == n_vertices:
                color_by = ColorBy.vertex
                colors_from_mesh = self._normalise_colors(mesh.vertex_colors)
                return color_by, colors_from_mesh
            elif n_face_colors == n_faces:
                color_by = ColorBy.face
                colors_from_mesh = self._normalise_colors(mesh.face_colors)
                return color_by, colors_from_mesh
            else:
                info(f"No valid colors found embeded in mesh called: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # If no vertex of face colors are appended to the mesh and no data is provided
        # the mesh is colored by vertex height.
        info(f"Coloring mesh by default colors")
        color_by = ColorBy.vertex
        default_data = mesh.vertices[:, 2]
        colors_default = np.array(calc_colors_rainbow(default_data))

        # No colors provided, no colors appeded to the mesh and no data provided
        # the returned colors are then based on z-height of the vertices.
        return color_by, colors_default

    def _normalise_colors(self, colors: np.ndarray):
        """Normalize colors to the range [0, 1] if necessary.

        Parameters
        ----------
        colors : np.ndarray
            Array of colors to normalize.

        Returns
        -------
        np.ndarray
            Normalized array of colors.
        """
        # If the max color value is larger then 1 it is assumed that the color range is 0-255
        max = np.max(colors)
        if max > 1.0:
            colors /= 255.0
        return colors

    def _generate_dict_colors(self, data_dict: dict, n_vert: int, n_face: int):
        # return default colors to be added to the mesh
        keys = data_dict.keys()
        self.dict_colors = {}
        self.dict_color_by = {}
        for key in keys:
            row_data = data_dict[key]
            if len(row_data) == n_vert:
                colors = calc_colors_rainbow(row_data)
                self.dict_colors[key] = colors
                self.dict_color_by[key] = ColorBy.vertex
            elif len(row_data) == n_face:
                colors = calc_colors_rainbow(row_data)
                self.dict_colors[key] = colors
                self.dict_color_by[key] = ColorBy.face

        if len(self.dict_colors) == 0:
            warning(f"Dict data in {self.name} doesn't match vertex/face count:")
            info("Coloring per vertex z-value")
            return False

        return True

    def _restructure_mesh(self, mesh: Mesh):
        """Restructure the mesh data for OpenGL rendering.

        Parameters
        ----------
        mesh : Mesh
            The Mesh object to restructure.
        color_by : ColorBy
            Color mode based on ColorBy enumeration.
        colors : np.ndarray
            Array of vertex colors for the mesh.

        Returns
        -------
        np.ndarray
            Array of flattened vertex data.
        np.ndarray
            Array of flattened face indices.
        np.ndarray
            Array of flattened edge indices.
        """

        # Vertex format that suits the opengl data structure:
        # [x, y, z, r, g, b, nx, ny ,nz]
        new_dict_colors = dict.fromkeys(self.dict_colors.keys())
        new_faces = []
        new_vertices = []
        new_edges = []
        v_index = 0
        white = [0.9, 0.9, 0.9]
        c1 = white
        c2 = white
        c3 = white
        for key in self.dict_colors.keys():
            new_dict_colors[key] = []

        # The restructuring makes sure that each faces has its own vertices. That is
        # nessary in order to be able to color each face individually and to be able to
        # use individual face normals for each mesh.
        for face_index, face in enumerate(mesh.faces):
            v1 = mesh.vertices[face[0], :]
            v2 = mesh.vertices[face[1], :]
            v3 = mesh.vertices[face[2], :]

            if self.color_by == ColorBy.vertex:
                # c1, c2, c3 are different colors to color the mesh by vertex
                c1 = self.colors[face[0]]
                c2 = self.colors[face[1]]
                c3 = self.colors[face[2]]
            elif self.color_by == ColorBy.face:
                # c1, c2, c3 are the same color to make the face color uniform
                c1 = self.colors[face_index]
                c2 = self.colors[face_index]
                c3 = self.colors[face_index]

            for key in self.dict_colors.keys():
                color_row_by = self.dict_color_by[key]
                if color_row_by == ColorBy.vertex:
                    c1 = self.dict_colors[key][face[0]]
                    c2 = self.dict_colors[key][face[1]]
                    c3 = self.dict_colors[key][face[2]]
                elif color_row_by == ColorBy.face:
                    c1 = self.dict_colors[key][face_index]
                    c2 = self.dict_colors[key][face_index]
                    c3 = self.dict_colors[key][face_index]
                arr = np.concatenate((c1, c2, c3))
                new_dict_colors[key].extend(arr)

            v1 = np.concatenate((v1, c1), axis=0)
            v2 = np.concatenate((v2, c2), axis=0)
            v3 = np.concatenate((v3, c3), axis=0)

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

        for key in self.dict_colors.keys():
            self.dict_colors[key] = np.array(new_dict_colors[key])  # .flatten()

        return np.array(new_vertices), np.array(new_faces), np.array(new_edges)

    def _move_mesh_to_origin_multi(self, vertices: np.ndarray, bb: BoundingBox):
        # [x, y, z, r, g, b, nx, ny ,nz]
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
        vertices += recenter_vec

        return vertices

    def _flatten_mesh(
        self, vertices: np.ndarray, face_indices: np.ndarray, edge_indices: np.ndarray
    ):
        """Flatten the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl implementation
        vertices = np.array(vertices, dtype="float32").flatten()
        edge_indices = np.array(edge_indices, dtype="uint32").flatten()
        face_indices = np.array(face_indices, dtype="uint32").flatten()

        return vertices, face_indices, edge_indices
