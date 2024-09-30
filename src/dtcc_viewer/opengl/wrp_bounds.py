import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from dtcc_core.model import LineString
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper
from dtcc_viewer.opengl.wrapper import Wrapper
from typing import Any


class BoundsWrapper(Wrapper):
    """Wrapper for rendering a list of LineString.

    This class is used to store a list of LineStrings and associated data for
    the purpous of visualization. The class provides methods to restructure
    the data to a format that fits the OpenGL functions.

    Attributes
    ----------
    name : str
        Name of the line strings collection.
    lss_wrp : LineStringsWrapper
        LineStringWrapper for line strings.
    """

    name: str
    ls_wrp: LineStringWrapper

    def __init__(self, name: str, bounds: Bounds, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name

        ls = self._create_linestring(bounds)
        self.ls_wrp = LineStringWrapper(name, ls, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.ls_wrp is not None:
            self.ls_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.ls_wrp.get_vertex_positions()

    def _create_linestring(self, bounds: Bounds):
        vertices = np.array(
            [
                [bounds.xmin, bounds.ymin, 0],
                [bounds.xmin, bounds.ymax, 0],
                [bounds.xmax, bounds.ymax, 0],
                [bounds.xmax, bounds.ymin, 0],
                [bounds.xmin, bounds.ymin, 0],
            ]
        )

        return LineString(vertices=vertices)
