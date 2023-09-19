# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
from pprint import pp
from dtcc_viewer import *
from dtcc_viewer.colors import color_maps
from dtcc_viewer.opengl_viewer.mesh_gl import MeshGL
from dtcc_viewer.opengl_viewer.point_cloud_gl import PointCloudGL
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.utils import *
from dtcc_model import Mesh
from dtcc_io import pointcloud, meshes

from dtcc_viewer.opengl_viewer.window import Window


class TestOpenGLViewer:
    def setup_method(self):
        # Creating a quad with 2 triangles where 2 vertices are shared
        self.vertices = np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 1.0, 1.0],
                [1.0, 1.0, 2.0],
                [1.0, 0.0, 3.0],
            ]
        )

        self.faces = np.array([[0, 1, 2], [2, 3, 0]])
        self.edges = np.array([[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [0, 2]])

        # Vertices in the format of opengl functions (should be flattened first thou).
        # [x, y, z, r, g, b, nx, ny, n z]
        self.vertices_gl = np.array(
            [
                [0, 0, 0, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026],
                [0, 1, 1, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026],
                [1, 1, 2, 1, 0, 0, 0.57735026, 0.57735026, -0.57735026],
                [1, 1, 2, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135],
                [1, 0, 3, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135],
                [0, 0, 0, 0, 0, 1, 0.90453404, -0.30151135, -0.30151135],
            ]
        )

        self.faces_gl = np.array(self.faces, dtype="uint32").flatten()
        self.edges_gl = np.array(self.edges, dtype="uint32").flatten()

    def test_mesh_2(self):
        # Creating a dtcc_model mesh
        mesh = Mesh(vertices=self.vertices, faces=self.faces)
        bb = BoundingBox(mesh.vertices)
        data = mesh.vertices[:, 0]
        mesh_data_obj = MeshData("name", mesh=mesh, data=data)
        mesh_data_obj.preprocess_drawing(bb)
        assert len(self.vertices_gl.flatten()) == len(mesh_data_obj.vertices)

    def test_mesh_4(self):
        # Testing conversion from obj to MeshGL object
        mesh = meshes.load_mesh("data/models/cube.obj")
        bb = BoundingBox(mesh.vertices)
        data = mesh.vertices[:, 0]
        mesh_data_obj = MeshData("name", mesh=mesh, data=data)
        mesh_data_obj.preprocess_drawing(bb)
        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        mesh_gl = MeshGL(mesh_data_obj)

        # window.render_mesh(mesh_data_obj)

        assert mesh and mesh_data_obj and mesh_gl

    def test_point_cloud(self):
        pc = pointcloud.load("data/models/cube_pc.csv")
        data = pc.points[:, 2]
        bb = BoundingBox(pc.points)
        pc_data_obj = PointCloudData("name", pc, data)
        pc_data_obj.preprocess_drawing(bb)
        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        pc_gl = PointCloudGL(pc_data_obj)

        # window.render_point_cloud(pc_data_obj)

        assert pc_data_obj


if __name__ == "__main__":
    os.system("clear")

    test = TestOpenGLViewer()
    test.setup_method()

    # test.test_mesh_2()
    test.test_mesh_2()
    # test.test_mesh_4()
    # test.test_point_cloud()
