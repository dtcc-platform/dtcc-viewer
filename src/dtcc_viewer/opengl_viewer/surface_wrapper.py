import numpy as np
from dtcc_model import Mesh, Surface
from dtcc_model import Bounds
from dtcc_viewer.utils import *
from dtcc_viewer.colors import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
from dtcc_viewer.logging import info, warning


class SurfaceWrapper:
    """Mesh attributes and associated data structured for the purpous of rendering.

    This class represents mesh data for rendering in an OpenGL window. It encapsulates
    information about the mesh's vertices, face indices, edge indices, and coloring options,
    and provides methods to restructure the data of a Mesh object to a format that fits
    the OpenGL functions.
    """

    color_by: int
    colors: np.ndarray
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
        surface: Surface,
        data: np.ndarray = None,
        colors: np.ndarray = None,
        shading: MeshShading = MeshShading.wireshaded,
    ) -> None:
        """Initialize the SurfaceWrapper object."""
        self.name = name
        self.shading = shading

        self._generate_colors(surface, data, colors)
        self._generate_mesh(surface)
        self._restructure_mesh(surface)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_mesh_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.vertices)
        self._flatten_mesh()

    def _generate_colors(
        self, mesh: Mesh, data: np.ndarray = None, colors: np.ndarray = None
    ):
        """Generate mesh colors based on the provided data."""
        pass

    def _normalise_colors(self, colors: np.ndarray):
        """Normalize colors to the range [0, 1] if necessary."""
        # If the max color value is larger then 1 it is assumed that the color range is 0-255
        max = np.max(colors)
        if max > 1.0:
            colors /= 255.0
        return colors

    def _generate_mesh(self, surface: Surface):
        # Triangultion of the Surface

        pass

    def _restructure_mesh(self, mesh: Mesh):
        """Restructure the mesh data for OpenGL rendering."""

        # Vertex format that suits the opengl data structure:
        # [x, y, z, r, g, b, nx, ny ,nz]

        pass

    def _move_mesh_to_origin_multi(self, bb: BoundingBox):
        # [x, y, z, r, g, b, nx, ny ,nz]
        recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
        self.vertices += recenter_vec

    def _flatten_mesh(self):
        # Making sure the datatypes are aligned with opengl implementation
        self.vertices = np.array(self.vertices, dtype="float32").flatten()
        self.edge_indices = np.array(self.edge_indices, dtype="uint32").flatten()
        self.face_indices = np.array(self.face_indices, dtype="uint32").flatten()
