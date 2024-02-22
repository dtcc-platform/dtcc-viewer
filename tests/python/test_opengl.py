# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
from pprint import pp
from dtcc_viewer import *
from dtcc_viewer.opengl_viewer.gl_mesh import GlMesh
from dtcc_viewer.opengl_viewer.gl_pointcloud import GlPointCloud
from dtcc_viewer.opengl_viewer.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl_viewer.wrp_pointcloud import PointCloudWrapper
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
        # [x, y, z, r, g, b, nx, ny, n z, id]
        self.vertices_gl = np.array(
            [
                [0, 0, 0, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026, 0],
                [0, 1, 1, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026, 0],
                [1, 1, 2, 1, 0, 0, 0.57735026, 0.57735026, -0.57735026, 0],
                [1, 1, 2, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135, 1],
                [1, 0, 3, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135, 1],
                [0, 0, 0, 0, 0, 1, 0.90453404, -0.30151135, -0.30151135, 1],
            ]
        )

        self.faces_gl = np.array(self.faces, dtype="uint32").flatten()
        self.edges_gl = np.array(self.edges, dtype="uint32").flatten()

    def test_mesh_2(self):
        # Creating a dtcc_model mesh
        mesh = Mesh(vertices=self.vertices, faces=self.faces)
        bb = BoundingBox(mesh.vertices.flatten())
        data = mesh.vertices[:, 0]
        mesh_wrapper = MeshWrapper("name", mesh=mesh, data=data)
        mesh_wrapper.preprocess_drawing(bb)
        assert len(self.vertices_gl.flatten()) == len(mesh_wrapper.vertices)

    def test_mesh_3(self):
        # Testing conversion from obj to MeshGL object
        mesh = meshes.load_mesh("data/models/cube.obj")
        bb = BoundingBox(mesh.vertices.flatten())
        data = mesh.vertices[:, 0]
        mesh_wrapper = MeshWrapper("name", mesh=mesh, data=data)
        mesh_wrapper.preprocess_drawing(bb)
        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        mesh_gl = GlMesh(mesh_wrapper)

        # window.render_mesh(mesh_data_obj)

        assert mesh and mesh_wrapper and mesh_gl

    def test_point_cloud(self):
        pc = pointcloud.load("data/models/cube_pc.csv")
        data = pc.points[:, 2]
        bb = BoundingBox(pc.points)
        pc_wrapper = PointCloudWrapper("name", pc, 0.2, data)
        pc_wrapper.preprocess_drawing(bb)
        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        pc_gl = GlPointCloud(pc_wrapper)

        # window.render_point_cloud(pc_data_obj)

        assert pc_wrapper


if __name__ == "__main__":
    os.system("clear")

    test = TestOpenGLViewer()
    test.setup_method()

    test.test_mesh_2()
    test.test_mesh_3()
    # test.test_point_cloud()
