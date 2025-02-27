import numpy as np
from dtcc_core.model import Mesh
from dtcc_viewer.utils import *
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.data_wrapper import LinesDataWrapper
from dtcc_viewer.opengl.wrp_linestring import MultiLineStringWrapper
from dtcc_core.model import MultiLineString
from dtcc_core.model import RoadNetwork
from pprint import PrettyPrinter
from typing import Any


class RoadNetworkWrapper(Wrapper):
    """Roadnetwork represented as a multilinestring for the purpous of rendering.

    This class represents road netowork for rendering in an OpenGL window. It encapsulates
    information about the mesh's vertices, face indices, edge indices, and coloring options,
    and provides methods to restructure the data of a Mesh object to a format that fits
    the OpenGL functions.

    """

    vertices: np.ndarray
    indices: np.ndarray
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox = None
    data_wrapper: LinesDataWrapper = None

    def __init__(
        self,
        name: str,
        roadnetwork: RoadNetwork,
        mts: int,
        data: Any = None,  # Dict, np.ndarray
    ) -> None:
        """Initialize the MeshWrapper object.

        Parameters
        ----------
        name : str
            The name of the mesh wrapper.
        roadnetwork : RoadNetwork
            RoadNetwork object for visualisation.
        mts: int
            Max texture size for the data.
        data : Any, optional
            Additional mesh data (dict or array) for color calculation (default is None).
        """
        self.name = name
        self.data_wrapper = None
        mls = roadnetwork.multilinestrings
        self.set_zero_z(mls)
        self.mls_wrp = MultiLineStringWrapper(name, mls, mts, data)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mls_wrp is not None:
            self.mls_wrp.preprocess_drawing(bb_global)

    def set_zero_z(self, mls: MultiLineString):
        for ls in mls.linestrings:
            if ls.vertices.shape[1] == 3:
                ls.vertices[:, 2] = 0.0

    def get_vertex_positions(self):
        if self.mls_wrp is not None:
            return self.mls_wrp.get_vertex_positions()
        return None
