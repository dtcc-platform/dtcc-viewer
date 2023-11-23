import numpy as np
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper
from dtcc_viewer.opengl_viewer.roadnetwork_wrapper import RoadNetworkWrapper
from dtcc_viewer.opengl_viewer.pointcloud_wrapper import PointCloudWrapper
from dtcc_viewer.opengl_viewer.utils import BoundingBox, MeshShading
from dtcc_model import Mesh, PointCloud, RoadNetwork
from dtcc_viewer.logging import info, warning
from typing import Any


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

    mesh_wrappers: list[MeshWrapper]
    pcs_wrappers: list[PointCloudWrapper]
    roadn_wrappers: list[RoadNetworkWrapper]
    bb: BoundingBox

    def __init__(self):
        self.mesh_wrappers = []
        self.pcs_wrappers = []
        self.roadn_wrappers = []

    def add_mesh(
        self,
        name: str,
        mesh: Mesh,
        data: Any = None,
        shading: MeshShading = MeshShading.wireshaded,
    ):
        """Append a mesh with data and/or colors to the scene"""
        if mesh is not None:
            info(f"Mesh called - {name} - added to scene")
            mesh_w = MeshWrapper(name=name, mesh=mesh, data=data, shading=shading)
            self.mesh_wrappers.append(mesh_w)
        else:
            warning(f"Mesh called - {name} - is None and not added to scene")

    def add_pointcloud(
        self,
        name: str,
        pc: PointCloud,
        size: float = 0.2,
        data: np.ndarray = None,
    ):
        """Append a pointcloud with data to color the scene"""
        if pc is not None:
            info(f"Point could called - {name} - added to scene")
            pc_w = PointCloudWrapper(name=name, pc=pc, size=size, data=data)
            self.pcs_wrappers.append(pc_w)
        else:
            warning(f"Point could called - {name} - is None and not added to scene")

    def add_roadnetwork(
        self,
        name: str,
        rn: RoadNetwork,
        data: np.ndarray = None,
        colors: np.ndarray = None,
    ):
        """Append a RoadNetwork object to the scene"""
        if rn is not None:
            info(f"Road network called - {name} - added to scene")
            rn_w = RoadNetworkWrapper(name=name, rn=rn, data=data, colors=colors)
            self.roadn_wrappers.append(rn_w)
        else:
            warning(f"Road network called - {name} - is None and not added to scene")

    def preprocess_drawing(self):
        """Preprocess bounding box calculation for all scene objects"""

        self._calculate_bb()

        for mesh in self.mesh_wrappers:
            mesh.preprocess_drawing(self.bb)

        for pc in self.pcs_wrappers:
            pc.preprocess_drawing(self.bb)

        for rn in self.roadn_wrappers:
            rn.preprocess_drawing(self.bb)

        info(f"Scene preprocessing completed")

    def _calculate_bb(self):
        """Calculate bounding box of the scene"""

        all_vertices = np.array([[0, 0, 0]])

        for mesh_w in self.mesh_wrappers:
            all_vertices = np.concatenate(
                (all_vertices, mesh_w.vertices[:, 0:3]), axis=0
            )

        for pc_w in self.pcs_wrappers:
            all_vertices = np.concatenate((all_vertices, pc_w.points), axis=0)

        for rn_w in self.roadn_wrappers:
            all_vertices = np.concatenate((all_vertices, rn_w.vertices[:, 0:3]), axis=0)

        # Remove the [0,0,0] row that was added to enable concatenate.
        all_vertices = np.delete(all_vertices, obj=0, axis=0)

        self.bb = BoundingBox(all_vertices)
