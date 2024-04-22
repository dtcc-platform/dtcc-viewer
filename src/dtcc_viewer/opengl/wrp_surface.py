import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_model import Surface, MultiSurface
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from typing import Any


class SurfaceWrapper(Wrapper):

    name: str
    mesh_wrp: MeshWrapper

    def __init__(self, name: str, surface: Surface, mts: int) -> None:
        """Initialize a SurfaceWrapper object."""
        self.name = name
        mesh = surface.mesh()
        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts)
        else:
            warning(f"Surface called - {name} - could not be converted to mesh.")

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_wrp.get_vertex_positions()


class MultiSurfaceWrapper(Wrapper):

    name: str
    mesh_wrp: MeshWrapper

    def __init__(self, name: str, multi_surface: MultiSurface, mts: int) -> None:
        """Initialize a MultiSurfaceWrapper object."""
        self.name = name
        mesh = multi_surface.mesh()
        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts)
        else:
            warning(f"MultiSurface called - {name} - could not be converted to mesh.")

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_wrp.get_vertex_positions()
