import numpy as np
from dtcc_viewer.opengl.utils import BoundingBox
from abc import ABC, abstractmethod
from dtcc_core.model import Geometry


class Wrapper(ABC):
    """Abstract base class for wrappers."""

    name: str

    @abstractmethod
    def preprocess_drawing(self, bb_global: BoundingBox):
        pass

    @abstractmethod
    def get_vertex_positions(self):
        pass
