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
            self.mesh_env_wrp = MeshWrapper("volume mesh envelop", mesh_env, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_vol_wrp is not None:
            self.mesh_vol_wrp.preprocess_drawing(bb_global)

        if self.mesh_env_wrp is not None:
            self.mesh_env_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_vol_wrp.get_vertex_positions()

    def _create_mesh(self, volume_mesh: VolumeMesh) -> Mesh:
        vertices = volume_mesh.vertices
        faces = np.zeros((volume_mesh.cells.shape[0] * 4, 3), dtype=int)
        for i, cell in enumerate(volume_mesh.cells):
            faces[i * 4 + 0, :] = np.array([cell[0], cell[2], cell[1]])
            faces[i * 4 + 1, :] = np.array([cell[0], cell[1], cell[3]])
            faces[i * 4 + 2, :] = np.array([cell[0], cell[3], cell[2]])
            faces[i * 4 + 3, :] = np.array([cell[3], cell[2], cell[1]])

        return Mesh(vertices=vertices, faces=faces)

    def _correct_winding(self, f: np.ndarray, vs: np.ndarray, mpt: np.ndarray):
        # Too slow to be used
        normal = np.cross(vs[f[1], :] - vs[f[0], :], vs[f[2], :] - vs[f[0], :])
        normal = normal / np.linalg.norm(normal)
        if np.dot(normal, mpt - vs[f[0], :]) > 0:
            return f
        else:
            return f[::-1]

    def _extract_mesh_envelope(self, mesh: Mesh) -> Mesh:
        faces_sorted = np.sort(mesh.faces, axis=1)
        faces_unique_mask = self.find_unique(faces_sorted)
        mesh = get_sub_mesh_from_mask(faces_unique_mask, mesh)
        true_count = np.count_nonzero(faces_unique_mask)
        info(f"Envelope extraction for VolumeMesh found {true_count} envelope faces")

        return mesh

    def find_unique(self, data):
        # Convert vertices to a structured array to hash them efficiently
        copy = data.view(np.dtype((np.void, data.dtype.itemsize * data.shape[1])))
        vals, inv, counts = np.unique(copy, return_counts=True, return_inverse=True)
        occurrences = counts[inv]
        unique_mask = occurrences == 1
        return unique_mask
