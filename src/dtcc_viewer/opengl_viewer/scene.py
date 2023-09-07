import numpy as np
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.utils import BoundingBox


class Scene:
    meshes: list[MeshData]
    pointclouds: list[PointCloudData]
    bb: BoundingBox

    def __init__(self):
        self.meshes = []
        self.pointclouds = []

    def add_mesh(self, mesh: MeshData):
        self.meshes.append(mesh)

    def add_meshes(self, meshes: list[MeshData]):
        self.meshes.extend(meshes)

    def add_pointcloud(self, pc: PointCloudData):
        self.pointclouds.append(pc)

    def add_pointclouds(self, pcs: list[PointCloudData]):
        self.pointclouds.extend(pcs)

    def add_pcs(self, pcs: list[PointCloudData]):
        self.pointclouds.extend(pcs)

    def preprocess_drawing(self):
        self._calculate_bb()
        self.bb.print()

        for mesh in self.meshes:
            mesh.preprocess_drawing(self.bb)

        for pc in self.pointclouds:
            pc.preprocess_drawing(self.bb)

    def _calculate_bb(self):
        all_vertices = np.array([[0, 0, 0]])

        for mesh in self.meshes:
            all_vertices = np.concatenate((all_vertices, mesh.vertices[:, 0:3]), axis=0)

        for pc in self.pointclouds:
            all_vertices = np.concatenate((all_vertices, pc.points), axis=0)

        # Remove the [0,0,0] row that was added to enable concatenate.
        all_vertices = np.delete(all_vertices, obj=0, axis=0)

        self.bb = BoundingBox(all_vertices)
