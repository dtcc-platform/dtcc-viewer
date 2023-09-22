import numpy as np
from dtcc_model import RoadNetwork
from dtcc_viewer.utils import *
from dtcc_viewer.opengl_viewer.utils import BoundingBox


class RoadNetworkData:
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
    colors: np.ndarray  # [n_points x 3]
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox

    def __init__(
        self,
        name: str,
        rn: RoadNetwork,
        data: np.ndarray = None,
        colors: np.ndarray = None,
    ) -> None:
        """Initialize a PointCloudData object.

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

        self.name = name
        self.colors = self._generate_rn_colors(rn, rn_data=data, rn_colors=colors)
        [self.vertices, self.indices] = self._restructure_road_network(rn, self.colors)

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.bb_global = bb_global
        self.vertices = self._move_rn_to_origin_multi(self.vertices, self.bb_global)
        self.bb_local = BoundingBox(self.vertices)
        self.vertices, self.indices = self._flatten(self.vertices, self.indices)

    def _move_rn_to_origin_multi(self, vertices: np.ndarray, bb: BoundingBox = None):
        if bb is not None:
            recenter_vec = np.concatenate((bb.center_vec, [0, 0, 0, 0, 0, 0]), axis=0)
            vertices += recenter_vec

        return vertices

    def _restructure_road_network(self, roadnetwork: RoadNetwork, colors: np.ndarray):
        new_indices = []
        for road in roadnetwork.roads:
            for i in range(len(road.road_vertices) - 1):
                v1 = road.road_vertices[i]
                v2 = road.road_vertices[i + 1]
                new_indices.append([v1, v2])

        new_vertices = np.zeros([len(roadnetwork.vertices), 9])

        # Vertex structure for OpenGL shaders: [x, y, z, r, g, b, nx, ny ,nz]
        for i in range(len(roadnetwork.vertices)):
            c = colors[i, :]
            v = roadnetwork.vertices[i, :]  # has only x and y coordinates!
            n = np.array([0, 0, 1])
            new_vertices[i, 0:2] = v
            new_vertices[i, 3:6] = c
            new_vertices[i, 6:9] = n

        return new_vertices, new_indices

    def _generate_rn_colors(
        self,
        rn: RoadNetwork,
        rn_data: np.ndarray = None,
        rn_colors: np.ndarray = None,
    ) -> np.ndarray:
        """Generate colors for the point cloud based on the provided data.

        Parameters
        ----------
        rn : RoadNetwork
            The RoadNetwork object to generate colors for.
        rn_data : np.ndarray, optional
            Additional data for color calculation (default is None).
        rn_colors : np.ndarray, optional
            Predifined colors (default is None).

        Returns
        -------
        np.ndarray
            Array of colors for the road network vertices
        """
        colors = []
        n_points = len(rn.vertices)

        if rn_colors is not None:
            n_rn_colors = len(rn_colors)
            if n_rn_colors == n_points:
                colors = np.array(rn_colors)
                return colors
            else:
                print(
                    "WARNING: Road network colors provided does not match vertex count!"
                )

        if rn_data is not None:
            if len(rn.vertices) == len(rn_data):
                colors = calc_colors_rainbow(rn_data)
            else:
                print("WARNING: Provided color data does not match the vertex count!")
                print("Default colors are used instead -> i.e. coloring per z-value")
                z = rn.vertices[:, 2]
                colors = calc_colors_rainbow(z)
        else:
            print("No data provided for point cloud -> colors are set based on y-value")
            z = rn.vertices[:, 1]  # Color by height if no data is provided
            colors = calc_colors_rainbow(z)

        colors = np.array(colors)
        colors = colors[:, 0:3]
        return colors

    def _flatten(self, vertices: np.ndarray, indices: np.ndarray):
        """Flatten the mesh data arrays for OpenGL compatibility.

        Parameters
        ----------
        vertices : np.ndarray
            Array of mesh vertices.
        edge_indices : np.ndarray
            Array of edge indices.

        Returns
        -------
        np.ndarray
            Flattened vertex array.
        np.ndarray
            Flattened edge indices array.
        """
        # Making sure the datatypes are aligned with opengl implementation
        vertices = np.array(vertices, dtype="float32").flatten()
        indices = np.array(indices, dtype="uint32").flatten()

        return vertices, indices
