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
        pass

    def test_mesh_2(self):
        # Creating a quad with 2 triangles where 2 vertices are shared
        vertices = np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 1.0, 1.0],
                [1.0, 1.0, 2.0],
                [1.0, 0.0, 3.0],
            ]
        )

        faces = np.array([[0, 1, 2], [2, 3, 0]])

        # Creating a dtcc_model mesh
        mesh = Mesh(vertices=vertices, faces=faces)
        data = mesh.vertices[:, 0]
        mesh_data_obj = MeshData("name", mesh=mesh, mesh_data=data)

        # 9 floats per vertex and 2 duplicated vertices (to enable individual normals at those vertices)
        # resulting in ((4+2) * 9) floats for this mesh.

        assert len(mesh_data_obj.vertices) == ((4 + 2) * 9)

    def test_mesh_3(self):
        # Vertices in the format of opengl functions (should be flattened first thou).
        # [x, y, z, r, g, b, nx, ny, n z]
        vertices = np.array(
            [
                [0, 0, 0, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026],
                [0, 1, 1, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026],
                [1, 1, 2, 1, 0, 0, 0.57735026, 0.57735026, -0.57735026],
                [1, 1, 2, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135],
                [1, 0, 3, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135],
                [0, 0, 0, 0, 0, 1, 0.90453404, -0.30151135, -0.30151135],
            ]
        )

        vertices = np.array(vertices, dtype="float32").flatten()
        faces = np.array([[0, 1, 2], [2, 3, 0]], dtype="uint32").flatten()
        edges = np.array(
            [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [0, 2]], dtype="uint32"
        ).flatten()

        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        mesh_gl = MeshGL("name", vertices=vertices, faces=faces, edges=edges)

        assert mesh_gl

    def test_mesh_4(self):
        # Testing conversion from obj to MeshGL object
        mesh = meshes.load_mesh("data/models/cube.obj")
        data = mesh.vertices[:, 0]
        print(mesh)
        recenter_vec = np.array([0, 0, 0])
        mesh_data_obj = MeshData(
            "name", mesh=mesh, mesh_data=data, recenter_vec=recenter_vec
        )

        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        mesh_gl = MeshGL(
            mesh_data_obj.name,
            mesh_data_obj.vertices,
            mesh_data_obj.face_indices,
            mesh_data_obj.edge_indices,
        )

        # window.render_mesh(mesh_data_obj)

        assert mesh and mesh_data_obj and mesh_gl

    def test_point_cloud(self):
        pc = pointcloud.load("data/models/cube_pc.csv")
        data = pc.points[:, 2]
        recenter_vec = np.array([0, 0, 0])
        pc_data_obj = PointCloudData("name", pc, data, recenter_vec)

        # Need to create a context for other OpenGL calls to be possible.
        window = Window(1200, 800)

        pc_gl = PointCloudGL(
            pc_data_obj.name, 0.1, pc_data_obj.points, pc_data_obj.colors
        )

        # window.render_point_cloud(pc_data_obj)

        assert pc_data_obj


if __name__ == "__main__":
    os.system("clear")

    test = TestOpenGLViewer()
    test.setup_method()

    # test.test_mesh_2()
    # test.test_mesh_3()
    # test.test_mesh_4()
    test.test_point_cloud()
