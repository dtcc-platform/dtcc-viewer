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
    mesh_wrp: MeshWrapper

    def __init__(self, name: str, volume_mesh: VolumeMesh, mts: int) -> None:
        """Initialize a SurfaceWrapper object."""
        self.name = name
        mesh = self._create_mesh(volume_mesh)
        self.mesh_wrp = MeshWrapper(name, mesh, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_wrp.get_vertex_positions()

    def _create_mesh(self, volume_mesh: VolumeMesh) -> Mesh:

        vertices = volume_mesh.vertices
        faces = []
        for cell in volume_mesh.cells:
            faces.append([cell[0], cell[2], cell[1]])
            faces.append([cell[0], cell[1], cell[3]])
            faces.append([cell[1], cell[2], cell[3]])
            faces.append([cell[2], cell[0], cell[3]])

        faces = np.array(faces)
        return Mesh(vertices=vertices, faces=faces)
