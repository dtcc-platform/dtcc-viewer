import numpy as np
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.roadnetwork_data import RoadNetworkData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
from dtcc_model import Mesh, PointCloud, RoadNetwork


class Scene:
    """Scene which contains a collection of objects to be rendered.

    This class is used to collect and pre-process data when rendering multiple objects
    at the same time.

    Attributes
    ----------
    meshes : list[MeshData]
        List of MeshData objects representing meshes to be drawn.
    point_clouds : list[PointCloudData]
        List of PointCloudData objects representing point clouds to be drawn.
    bb : BoundingBox
        Bounding box for the entire collection of objects in the scene.
    """

    meshes: list[MeshData]
    pointclouds: list[PointCloudData]
    road_networks: list[RoadNetworkData]
    bb: BoundingBox

    def __init__(self):
        self.meshes = []
        self.pointclouds = []
        self.road_networks = []

    def add_mesh(
        self,
        name: str,
        mesh: Mesh,
        data: np.ndarray = None,
        colors: np.ndarray = None,
        shading: MeshShading = MeshShading.wireshaded,
    ):
        """Append a mesh with data and/or colors to the scene"""
        mesh_data = MeshData(
            name=name, mesh=mesh, data=data, colors=colors, shading=shading
        )
        self.meshes.append(mesh_data)

    def add_mesh_data(self, mesh: MeshData):
        """Append a MeshData object to the secene"""
        self.meshes.append(mesh)

    def add_mesh_data_list(self, meshes: list[MeshData]):
        """Append a list of MeshData objects to the scene"""
        self.meshes.extend(meshes)

    def add_pointcloud(
        self,
        name: str,
        pc: PointCloud,
        size: float = 0.2,
        data: np.ndarray = None,
        colors: np.ndarray = None,
    ):
        """Append a pointcloud with data and/or colors to the scene"""
        pc_data = PointCloudData(name=name, pc=pc, size=size, data=data, colors=colors)
        self.pointclouds.append(pc_data)

    def add_pointcloud_data(self, pc: PointCloudData):
        """Append a PointCloudData object to the scene"""
        self.pointclouds.append(pc)

    def add_pointcloud_data_list(self, pcs: list[PointCloudData]):
        """Append a list of PointCloudData objects to the scene"""
        self.pointclouds.extend(pcs)

    def add_roadnetwork(
        self,
        name: str,
        rn: RoadNetwork,
        data: np.ndarray = None,
        colors: np.ndarray = None,
    ):
        """Append a RoadNetwork object to the scene"""
        rn_data = RoadNetworkData(name=name, rn=rn, data=data, colors=colors)
        self.road_networks.append(rn_data)

    def add_roadnetwork_data(self, roadnetwork: RoadNetworkData):
        """Append a RoadNetwork object to the scene"""
        self.road_networks.append(roadnetwork)

    def add_roadnetwork_data_list(self, roadnetwork_list: list[RoadNetworkData]):
        """Append a RoadNetwork object to the secene"""
        self.road_networks.extend(roadnetwork_list)

    def preprocess_drawing(self):
        """Preprocess bounding box calculation for all scene objects"""

        self._calculate_bb()

        for mesh in self.meshes:
            mesh.preprocess_drawing(self.bb)

        for pc in self.pointclouds:
            pc.preprocess_drawing(self.bb)

        for rn in self.road_networks:
            rn.preprocess_drawing(self.bb)

            # rn.bb_global.print()

    def _calculate_bb(self):
        """Calculate bounding box of the scene"""

        all_vertices = np.array([[0, 0, 0]])

        for mesh in self.meshes:
            all_vertices = np.concatenate((all_vertices, mesh.vertices[:, 0:3]), axis=0)

        for pc in self.pointclouds:
            all_vertices = np.concatenate((all_vertices, pc.points), axis=0)

        for rn in self.road_networks:
            all_vertices = np.concatenate((all_vertices, rn.vertices[:, 0:3]), axis=0)

        # Remove the [0,0,0] row that was added to enable concatenate.
        all_vertices = np.delete(all_vertices, obj=0, axis=0)

        self.bb = BoundingBox(all_vertices)
