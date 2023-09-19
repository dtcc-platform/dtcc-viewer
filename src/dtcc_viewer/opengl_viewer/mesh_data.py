import numpy as np
from dtcc_model import Mesh
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox


class MeshData:
    """Mesh attributes and associated data structured for the purpous of rendering.

    This class represents mesh data for rendering in an OpenGL window. It encapsulates
    information about the mesh's vertices, face indices, edge indices, and coloring options,
    and provides methods to restructure the data of a Mesh object to a format that fits
    the OpenGL functions.

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

    recenter_vec : np.ndarray, optional
        Vector for recentering the mesh (default is None).

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

    """

    color_by: int
    mesh_colors: np.ndarray
    vertices: np.ndarray
    face_indices: np.ndarray
    edge_indices: np.ndarray
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox = None

    def __init__(
        self,
        name: str,
        mesh: Mesh,
        data: np.ndarray = None,
        colors: np.ndarray = None,
    ) -> None:
        """Initialize the MeshData object.

        Parameters
        ----------
        name : str
            The name of the mesh data.
        mesh : Mesh
            The underlying Mesh object from which to generate the mesh data.
        mesh_data : np.ndarray, optional
            Additional mesh data for color calculation (default is None).
        recenter_vec : np.ndarray, optional
            Vector for recentering the mesh (default is None).
        bb_global : BoundingBox, optional
            A bounding box for all geometry in a collection (default is None).
        """
        self.name = name

        [self.color_by, self.mesh_colors] = self._generate_mesh_colors(
            mesh, data, colors
        )
        [self.vertices, self.face_indices, self.edge_indices] = self._restructure_mesh(
            mesh, self.color_by, self.mesh_colors
        )

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self.vertices = self._move_mesh_to_origin_multi(self.vertices, self.bb_global)
        self.bb_local = BoundingBox(self.vertices)

        [self.vertices, self.edge_indices, self.face_indices] = self._flatten_mesh(
            self.vertices, self.edge_indices, self.face_indices
        )

    def _generate_mesh_colors(
        self, mesh: Mesh, data: np.ndarray = None, mesh_colors: np.ndarray = None
    ):
        """Generate mesh colors based on the provided data.

        Parameters
        ----------
        mesh : Mesh
            The Mesh object from which to generate colors.
        data : np.ndarray, optional
            Additional data for color calculation (default is None).

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

        # If no vertex of face colors are appended to the mesh and no data is provided
        # the mesh is colored by vertex height.
        color_by = ColorBy.vertex_height
        default_data = mesh.vertices[:, 2]
        colors = calc_colors_rainbow(default_data)

        # First priority is coloring by provided color array.
        if mesh_colors is not None:
            n_mesh_colors = len(mesh_colors)
            colors = self._normalise_colors(mesh_colors)
            colors = np.array(colors)
            if n_mesh_colors == n_vertices:
                color_by = ColorBy.vertex_colors
                return color_by, colors
            elif n_mesh_colors == n_faces:
                color_by = ColorBy.face_colors
                return color_by, colors
            else:
                print(
                    "WARNING: Provided mesh colors does not match vertex or face count for mesh : "
                    + self.name
                )

        # No colors provided and no data for color calculations. Colors are retrieved
        # from the mesh either base on vertices or face colors.
        if mesh_colors is None and data is None:
            if n_vertex_colors == n_vertices:
                color_by = ColorBy.vertex_colors
                colors = self._normalise_colors(mesh.vertex_colors)
            elif n_face_colors == n_faces:
                color_by = ColorBy.face_colors
                colors = self._normalise_colors(mesh.face_colors)
            else:
                print(
                    "INFO: No valid colors found embeded in mesh object with name: "
                    + self.name
                )
                print("Coloring per vertex z-value")
        # If there is data for coloring
        else:
            n_data = len(data)
            if n_data == n_vertices:  # Generate colors base on provided vertex data
                color_by = ColorBy.vertex_data
                colors = calc_colors_rainbow(data)
            elif n_data == n_faces:  # Generate colors base on provided face data
                color_by = ColorBy.face_data
                colors = calc_colors_rainbow(data)
            else:
                print(
                    "WARNING: Provided color data for mesh does not match vertex of face count for mesh with name: "
                    + self.name
                )
                print(
                    "Default colors are used instead -> i.e. coloring per vertex z-value"
                )

        return color_by, np.array(colors)

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

    def _restructure_mesh(self, mesh: Mesh, color_by: ColorBy, colors: np.ndarray):
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
        new_faces = []
        new_vertices = []
        new_edges = []
        v_index = 0
        white = [0.9, 0.9, 0.9]
        c1 = white
        c2 = white
        c3 = white

        # print(color_by)

        for face_index, face in enumerate(mesh.faces):
            v1 = mesh.vertices[face[0], :]
            v2 = mesh.vertices[face[1], :]
            v3 = mesh.vertices[face[2], :]

            if (
                color_by == ColorBy.vertex_colors
                or color_by == ColorBy.vertex_data
                or color_by == ColorBy.vertex_height
            ):
                c1 = colors[face[0], 0:3]
                c2 = colors[face[1], 0:3]
                c3 = colors[face[2], 0:3]
            elif color_by == ColorBy.face_colors or color_by == ColorBy.face_data:
                c1 = colors[face_index, 0:3]
                c2 = colors[face_index, 0:3]
                c3 = colors[face_index, 0:3]

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

        return np.array(new_vertices), np.array(new_faces), np.array(new_edges)

    def _move_mesh_to_origin_multi(self, vertices: np.ndarray, bb: BoundingBox):
        # [x, y, z, r, g, b, nx, ny ,nz]
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
        vertices += recenter_vec

        return vertices

    def _flatten_mesh(
        self, vertices: np.ndarray, face_indices: np.ndarray, edge_indices: np.ndarray
    ):
        """Flatten the mesh data arrays for OpenGL compatibility.

        Parameters
        ----------
        vertices : np.ndarray
            Array of mesh vertices.
        face_indices : np.ndarray
            Array of face indices.
        edge_indices : np.ndarray
            Array of edge indices.

        Returns
        -------
        np.ndarray
            Flattened vertex array.
        np.ndarray
            Flattened face indices array.
        np.ndarray
            Flattened edge indices array.
        """
        # Making sure the datatypes are aligned with opengl implementation
        vertices = np.array(vertices, dtype="float32").flatten()
        edge_indices = np.array(edge_indices, dtype="uint32").flatten()
        face_indices = np.array(face_indices, dtype="uint32").flatten()

        return vertices, face_indices, edge_indices
