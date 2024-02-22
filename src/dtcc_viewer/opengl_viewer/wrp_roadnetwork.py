import numpy as np
from dtcc_model import RoadNetwork
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox
from dtcc_viewer.logging import info, warning


class RoadNetworkWrapper:
    """Road network attributes and data structured for the purpous of rendering.

    This class is used to store a road network with associated data and colors
    for visualization purposes. The class also provides methods to restructure
    the data to a format that fits the OpenGL functions.

    Attributes
    ----------
    vertices : np.ndarray
        Array of vertex coordinates in the format [n_points x 3].
    colors : np.ndarray
        Array of colors associated with each vertex in the format [n_points x 3].
    name : str
        Name of road network.
    """

    vertices: np.ndarray  # [n_vertices x 3] = [v1,v2,v3,v4,.. n_vertices]
    indices: np.ndarray  # [n_roads x 2] = [[v3, v2,], [v5, v2]...]
    dict_data: dict
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self,
        name: str,
        rn: RoadNetwork,
        data: np.ndarray = None,
    ) -> None:
        """Initialize a Road network wrapper object.

        Parameters
        ----------
        name : str
            Name of the point cloud data.
        rn : RoadNetwork
            The RoadNetwork object to be drawn.
        data : np.ndarray
            Additional data for coloring.
        colors : np.ndarray
            Predefined colors matching the vertex data.

        Returns
        -------
        None
        """
        self.dict_data = {}
        self.name = name
        self._restructure_data(rn, data)
        self._restructure_road_network(rn)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self._move_rn_to_origin_multi(self.bb_global)
        self.bb_local = BoundingBox(self.vertices)
        self._reformat()

    def _move_rn_to_origin_multi(self, bb: BoundingBox = None):
        if bb is not None:
            v_count = len(self.vertices) // 9
            recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
            recenter_vec_tiled = np.tile(recenter_vec, v_count)
            self.vertices += recenter_vec_tiled

    def _restructure_data(self, rn: RoadNetwork, data: np.ndarray = None):
        """Generate colors for the point cloud based on the provided data."""

        n_points = len(rn.vertices)

        new_dict = {
            "slot0": np.zeros(n_points),
            "slot1": np.zeros(n_points),
            "slot2": np.zeros(n_points),
        }

        if type(data) == dict:
            self.dict_data = self._restructure_data_dict(rn, data, new_dict)
        elif type(data) == np.ndarray:
            self.dict_data = self._restructure_data_array(rn, data, new_dict)
        else:
            info("No data provided for mesh.")
            info("Default (x, y, z) - coords per vertex data appended.")
            new_dict["slot0"] = rn.vertices[:, 0]
            new_dict["slot1"] = rn.vertices[:, 1]
            self.dict_data = new_dict

    def _restructure_data_dict(self, rn: RoadNetwork, data: dict, new_dict: dict):
        n_vertices = len(rn.vertices)
        data_slots = len(new_dict)
        counter = 0

        for key in data.keys():
            data = data[key]
            if counter < data_slots:
                if len(data) == n_vertices:
                    new_dict["slot" + str(counter)] = data
                else:
                    info(f"Data for {key} does not match vertex or face count")
            else:
                info(f"Data for {key} does not fit in available slots")
            counter += 1

        return new_dict

    def _restructure_data_array(
        self, rn: RoadNetwork, data: np.ndarray, new_dict: dict
    ):
        if len(data) == len(rn.vertices):
            new_dict["slot0"] = data
        else:
            pass

        return new_dict

    def _restructure_road_network(self, roadnetwork: RoadNetwork):
        new_indices = []
        for road in roadnetwork.roads:
            for i in range(len(road.road_vertices) - 1):
                v1 = road.road_vertices[i]
                v2 = road.road_vertices[i + 1]
                new_indices.append([v1, v2])

        new_vertices = np.zeros([len(roadnetwork.vertices), 9]).flatten()

        new_vertices[0::9] = roadnetwork.vertices[:, 0]
        new_vertices[1::9] = roadnetwork.vertices[:, 1]
        new_vertices[3::9] = self.dict_data["slot0"]
        new_vertices[4::9] = self.dict_data["slot1"]
        new_vertices[5::9] = self.dict_data["slot2"]

        self.vertices = np.array(new_vertices, dtype="float32").flatten()
        self.indices = np.array(new_indices, dtype="uint32").flatten()

    def get_vertex_positions(self):
        """Get the vertex positions"""
        vertex_mask = np.array(
            [True, True, True, False, False, False, False, False, False]
        )
        v_count = len(self.vertices) // 9
        vertex_pos_mask = np.tile(vertex_mask, v_count)
        vertex_pos = self.vertices[vertex_pos_mask]
        return vertex_pos

    def _reformat(self):
        """Flatten the mesh data arrays for OpenGL compatibility."""
        # Making sure the datatypes are aligned with opengl implementation
        self.vertices = np.array(self.vertices, dtype="float32")
        self.indices = np.array(self.indices, dtype="uint32")
