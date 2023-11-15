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
        self.dict_data = {}
        self.dict_colors = {}
        self.dict_color_by = {}

        self._generate_mesh_colors(mesh, data, colors)
        self._restructure_dicts(mesh)
        self._restructure_mesh(mesh)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mesh_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.vertices)
        self._flatten_mesh()

    def _generate_mesh_colors(
        self, mesh: Mesh, data: Any = None, in_colors: np.ndarray = None
    ):
        """Generate mesh colors based on the provided data."""

        n_vertex_colors = len(mesh.vertex_colors)
        n_face_colors = len(mesh.face_colors)
        n_vertices = len(mesh.vertices)
        n_faces = len(mesh.faces)
        n_data = 0

        # First priority is coloring by provided data dict.
        if isinstance(data, dict):
            info(f"Coloring mesh by data dictionary")
            if self._generate_dict_colors(data, n_vertices, n_faces):
                return True

        # Second priority is coloring by provided color array.
        if in_colors is not None:
            info(f"Coloring mesh by input colors")
            n_input_colors = len(in_colors)
            colors_from_input = np.array(self._normalise_colors(in_colors))
            key = "From color array"
            # self.colors = colors_from_input
            if n_input_colors == n_vertices:
                self.dict_data[key] = None
                self.dict_colors[key] = colors_from_input
                self.dict_color_by[key] = ColorBy.vertex
                return True
            elif n_input_colors == n_faces:
                self.dict_data[key] = None
                self.dict_colors[key] = colors_from_input
                self.dict_color_by[key] = ColorBy.face
                return True
            else:
                warning(f"Input colors do not match vertex/face count: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # If there is data for coloring
        if data is not None:
            info(f"Coloring mesh by data")
            n_data = len(data)
            key = "From data array"
            colors_from_data = calc_colors_rainbow(data)
            if n_data == n_vertices:  # Generate colors base on provided vertex data
                self.dict_data[key] = np.array(data)
                self.dict_colors[key] = colors_from_data
                self.dict_color_by[key] = ColorBy.vertex
                return True
            elif n_data == n_faces:  # Generate colors base on provided face data
                self.dict_data[key] = np.array(data)
                self.dict_colors[key] = colors_from_data
                self.dict_color_by[key] = ColorBy.face
                return True
            else:
                warning(f"Color data does not match vertex of face count: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # No colors provided. Colors are then retrieved from the mesh either base on
        # vertices or face colors.
        if in_colors is None and data is None:
            info(f"Coloring appended mesh colors")
            key = "From mesh colors"
            if n_vertex_colors == n_vertices:
                self.dict_data[key] = None
                self.dict_colors[key] = self._normalise_colors(mesh.vertex_colors)
                self.dict_color_by[key] = ColorBy.vertex
                return True
            elif n_face_colors == n_faces:
                self.dict_data[key] = None
                self.dict_colors[key] = self._normalise_colors(mesh.face_colors)
                self.dict_color_by[key] = ColorBy.face
                return True
            else:
                info(f"No valid colors found embeded in mesh called: {self.name}")
                info(f"Default colors are used -> i.e. coloring per vertex z-value")

        # If no vertex of face colors are appended to the mesh and no data is provided
        # the mesh is colored by vertex height.
        info(f"Coloring mesh by default colors")
        key = "Default colors"
        default_data = mesh.vertices[:, 2]
        self.dict_data[key] = default_data
        self.dict_color_by[key] = ColorBy.vertex
        self.dict_colors[key] = calc_colors_rainbow(default_data)

        # No colors provided, no colors appeded to the mesh and no data provided
        # the returned colors are then based on z-height of the vertices.
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
                colors = calc_colors_rainbow(row_data)
                self.dict_data[key] = np.array(row_data)
                self.dict_colors[key] = colors
                self.dict_color_by[key] = ColorBy.vertex
            elif len(row_data) == n_face:
                colors = calc_colors_rainbow(row_data)
                self.dict_data[key] = np.array(row_data)
                self.dict_colors[key] = colors
                self.dict_color_by[key] = ColorBy.face

        if len(self.dict_colors) == 0:
            warning(f"Dict data in {self.name} doesn't match vertex/face count:")
            info("Coloring per vertex z-value")
            return False

        return True

    def _restructure_dicts(self, mesh: Mesh):
        # Structure the color data in the dict so that there are three colors for each
        # face. This is necessary in order to be able to color each face individually.
        # This structure is also neede for the vertices so that each face can have
        # individual normals so that shading can be computed correctly.

        new_dict_colors = dict.fromkeys(self.dict_colors.keys())
        new_dict_data = dict.fromkeys(self.dict_colors.keys())
        d1, d2, d3 = 0, 0, 0
        for key in self.dict_colors.keys():
            new_dict_colors[key] = []

        for key in self.dict_data.keys():
            if self.dict_data[key] is not None:
                new_dict_data[key] = []
            else:
                new_dict_data[key] = None

        for face_index, face in enumerate(mesh.faces):
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

            for key in self.dict_data.keys():
                color_row_by = self.dict_color_by[key]
                if self.dict_data[key] is not None:
                    if color_row_by == ColorBy.vertex:
                        d1 = self.dict_data[key][face[0]]
                        d2 = self.dict_data[key][face[1]]
                        d3 = self.dict_data[key][face[2]]
                        new_dict_data[key].extend([d1, d2, d3])
                    elif color_row_by == ColorBy.face:
                        d1 = self.dict_data[key][face_index]
                        new_dict_data[key].extend([d1, d1, d1])

        # Saving data with the new format
        for key in self.dict_colors.keys():
            self.dict_colors[key] = np.array(new_dict_colors[key])
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

        # Set the color of the mesh to the first color in the dict
        first_key = list(self.dict_colors.keys())[0]

        # The restructuring makes sure that each faces has its own vertices. That is
        # nessary in order to be able to color each face individually and to be able to
        # use individual face normals for each mesh.
        for face_index, face in enumerate(mesh.faces):
            v1 = mesh.vertices[face[0], :]
            v2 = mesh.vertices[face[1], :]
            v3 = mesh.vertices[face[2], :]

            # For each face there are 9 values for the r,g,b of each vertex
            color_index1 = face_index * 9 + 0
            color_index2 = face_index * 9 + 3
            color_index3 = face_index * 9 + 6

            c1 = self.dict_colors[first_key][color_index1 : color_index1 + 3]
            c2 = self.dict_colors[first_key][color_index2 : color_index2 + 3]
            c3 = self.dict_colors[first_key][color_index3 : color_index3 + 3]

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
