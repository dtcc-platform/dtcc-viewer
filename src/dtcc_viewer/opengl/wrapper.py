import numpy as np
from dtcc_model import City, MultiSurface, Building, Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.submeshes import Submeshes
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.utils import surface_2_mesh, concatenate_meshes
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from abc import ABC, abstractmethod


class Wrapper(ABC):
    """Abstract base class for wrappers."""

    name: str

    @abstractmethod
    def preprocess_drawing(self, bb_global: BoundingBox):
        pass

    @abstractmethod
    def get_vertex_positions(self):
        pass
