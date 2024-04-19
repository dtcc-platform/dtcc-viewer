import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.logging import info, warning
from shapely.geometry import LineString, Point
from dtcc_viewer.opengl.wrp_linestrings import LineStringsWrapper
from typing import Any


class BoundsWrapper:
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
    lss_wrp: LineStringsWrapper

    def __init__(self, name: str, bounds: Bounds, mts: int) -> None:
        """Initialize a line string wrapper object."""
        self.name = name

        ls = self._create_linestring(bounds)
        lss = [ls]

        self.lss_wrp = LineStringsWrapper(name, lss, mts)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.lss_wrp is not None:
            self.lss_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.lss_wrp.get_vertex_positions()

    def _create_linestring(self, bounds: Bounds):
        pt1 = Point(bounds.xmin, bounds.ymin, 0)
        pt2 = Point(bounds.xmin, bounds.ymax, 0)
        pt3 = Point(bounds.xmax, bounds.ymax, 0)
        pt4 = Point(bounds.xmax, bounds.ymin, 0)

        return LineString([pt1, pt2, pt3, pt4, pt1])
