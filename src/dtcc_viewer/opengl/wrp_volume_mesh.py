import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_model import VolumeMesh, Mesh
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from typing import Any


class VolumeMeshWrapper(Wrapper):

    name: str
    mesh_vol_wrp: MeshWrapper = None
    mesh_env_wrp: MeshWrapper = None

    def __init__(self, name: str, volume_mesh: VolumeMesh, mts: int) -> None:
        """Initialize a SurfaceWrapper object."""
        self.name = name
        mesh_vol = self._create_mesh(volume_mesh)
        mesh_env = self._extract_mesh_envelope(mesh_vol)

        self.mesh_vol_wrp = MeshWrapper(name, mesh_vol, mts)

        if mesh_env is not None:
            self.mesh_env_wrp = MeshWrapper("Volume mesh envelop", mesh_env, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_vol_wrp is not None:
            self.mesh_vol_wrp.preprocess_drawing(bb_global)

        if self.mesh_env_wrp is not None:
            self.mesh_env_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_vol_wrp.get_vertex_positions()

    def _create_mesh(self, volume_mesh: VolumeMesh) -> Mesh:

        vertices = volume_mesh.vertices
        faces = []
        for cell in volume_mesh.cells:
            faces.append([cell[0], cell[2], cell[1]])
            faces.append([cell[0], cell[1], cell[3]])
            faces.append([cell[0], cell[3], cell[2]])
            faces.append([cell[1], cell[2], cell[3]])

        faces = np.array(faces)
        return Mesh(vertices=vertices, faces=faces)

    def _extract_mesh_envelope(self, mesh: Mesh) -> Mesh:

        faces_sorted = np.sort(mesh.faces, axis=1)
        faces_unique_mask = self.find_duplicates(faces_sorted)

        true_count = np.count_nonzero(faces_unique_mask)
        print("Number of faces: ", len(faces_sorted))
        print("Number of unique faces: ", true_count)

        faces = mesh.faces[faces_unique_mask, :]
        faces_flat = faces.flatten()
        unique_vertex_indices = np.unique(faces_flat)
        old_vertex_indices = unique_vertex_indices

        old_2_new = {}
        for i, old_vi in enumerate(old_vertex_indices):
            old_2_new[old_vi] = i

        new_vertices = mesh.vertices[unique_vertex_indices, :]
        new_faces = np.zeros(faces.shape, dtype=int)

        for i in range(faces.shape[0]):
            new_faces[i, :] = [old_2_new[old_vi] for old_vi in faces[i, :]]

        mesh = Mesh(vertices=new_vertices, faces=new_faces)

        return mesh

    def find_duplicates(self, faces):
        # Convert vertices to a structured array to hash them efficiently
        faces_view = faces.view(
            np.dtype((np.void, faces.dtype.itemsize * faces.shape[1]))
        )

        # Find unique vertices and their indices
        # unique_vertices, inverse_indices = np.unique(vertices_view, return_inverse=True)

        vals, idx, inv, counts = np.unique(
            faces_view, return_index=True, return_counts=True, return_inverse=True
        )

        occurrences = counts[inv]

        # Find duplicate vertices based on inverse indices
        unique_mask = occurrences == 1

        return unique_mask
