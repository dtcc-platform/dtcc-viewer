import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_core.model import VolumeMesh, Mesh
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
        data_dict = self._calc_mesh_quality(volume_mesh)
        mesh_env = self._extract_mesh_envelope(mesh_vol)
        self.mesh_vol_wrp = MeshWrapper(name, mesh_vol, mts, data_dict)

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

        info(f"Mesh with {len(vertices)} vertices and {len(faces)} faces created.")
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

    def _calc_mesh_quality(self, volume_mesh: VolumeMesh):
        data_dict = {}
        aspect_ratios = np.zeros(volume_mesh.cells.shape[0])
        cell_volume = np.zeros(volume_mesh.cells.shape[0])

        for i, cell in enumerate(volume_mesh.cells):
            v0 = volume_mesh.vertices[cell[0]]
            v1 = volume_mesh.vertices[cell[1]]
            v2 = volume_mesh.vertices[cell[2]]
            v3 = volume_mesh.vertices[cell[3]]
            (aspect_ratio, volume) = self._tet_aspect_ratio(v0, v1, v2, v3)
            aspect_ratios[i] = aspect_ratio
            cell_volume[i] = volume

        data_dict["Aspect Ratio (R/r)"] = np.repeat(aspect_ratios, 4)
        data_dict["Volume"] = np.repeat(cell_volume, 4)
        info("Volume mesh quality metrics calculated.")
        return data_dict

    def _tet_volume(self, v0, v1, v2, v3):
        """
        Calculate the volume of a tetrahedron.
        """
        return np.abs(np.dot((v3 - v0), np.cross(v1 - v0, v2 - v0))) / 6.0

    def _tet_aspect_ratio(self, v0, v1, v2, v3):
        # Compute the edge lengths

        a = np.linalg.norm(v0 - v1)
        b = np.linalg.norm(v0 - v2)
        c = np.linalg.norm(v0 - v3)
        d = np.linalg.norm(v1 - v2)
        e = np.linalg.norm(v1 - v3)
        f = np.linalg.norm(v2 - v3)

        # Compute the tet volume
        volume = np.abs(np.dot(np.cross(v1 - v0, v2 - v0), v3 - v0)) / 6.0

        # Compute the radius of the circumscribed sphere
        R = np.sqrt((a * b * c * d * e * f) / (2 * volume)) / 2.0

        # Compute the radius of the inscribed sphere
        r = (3 * volume) / (a * b * c + a * d * e + b * d * f + c * e * f)

        # Compute the aspect ratio
        aspect_ratio = R / r

        return aspect_ratio, volume
