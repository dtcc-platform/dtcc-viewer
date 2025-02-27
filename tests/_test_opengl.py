import os
import numpy as np
import pytest
from pprint import pp

from dtcc_viewer import *
from dtcc_viewer.opengl.gl_mesh import GlMesh
from dtcc_viewer.opengl.gl_points import GlPoints
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.utils import *
from dtcc_core.model import Mesh
from dtcc_core.io import pointcloud, meshes
from dtcc_viewer.opengl.window import Window

@pytest.fixture
def viewer_setup():
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
    edges = np.array([[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [0, 2]])

    # Vertices in the format for OpenGL functions
    vertices_gl = np.array(
        [
            [0, 0, 0, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026, 0],
            [0, 1, 1, 0, 0, 1, 0.57735026, 0.57735026, -0.57735026, 0],
            [1, 1, 2, 1, 0, 0, 0.57735026, 0.57735026, -0.57735026, 0],
            [1, 1, 2, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135, 1],
            [1, 0, 3, 1, 0, 0, 0.90453404, -0.30151135, -0.30151135, 1],
            [0, 0, 0, 0, 0, 1, 0.90453404, -0.30151135, -0.30151135, 1],
        ]
    )
    faces_gl = np.array(faces, dtype="uint32").flatten()
    edges_gl = np.array(edges, dtype="uint32").flatten()

    return {
        "vertices": vertices,
        "faces": faces,
        "edges": edges,
        "vertices_gl": vertices_gl,
        "faces_gl": faces_gl,
        "edges_gl": edges_gl,
    }

def test_mesh_2(viewer_setup):
    # Creating a dtcc_model mesh
    mesh = Mesh(vertices=viewer_setup["vertices"], faces=viewer_setup["faces"])
    bb = BoundingBox(mesh.vertices.flatten())
    data = mesh.vertices[:, 0]
    mesh_wrapper = MeshWrapper("name", mesh=mesh, data=data)
    mesh_wrapper.preprocess_drawing(bb)
    # Assert that the flattened OpenGL vertices length matches
    assert len(viewer_setup["vertices_gl"].flatten()) == len(mesh_wrapper.vertices)

def test_mesh_3():
    # Testing conversion from an OBJ file to a MeshGL object.
    # This test assumes that "data/cube.obj" exists.
    mesh = meshes.load_mesh("data/cube.obj")
    bb = BoundingBox(mesh.vertices.flatten())
    data = mesh.vertices[:, 0]
    mesh_wrapper = MeshWrapper("name", mesh=mesh, data=data)
    mesh_wrapper.preprocess_drawing(bb)
    # Create an OpenGL context by creating a window.
    window = Window(1200, 800)
    mesh_gl = GlMesh(mesh_wrapper)
    # Optionally, window.render_mesh(mesh_gl) could be called here.
    assert mesh is not None
    assert mesh_wrapper is not None
    assert mesh_gl is not None

def test_point_cloud():
    # Testing point cloud loading and conversion.
    # This test assumes that "data/cube_pc.csv" exists.
    pc = pointcloud.load("data/cube_pc.csv")
    data = pc.points[:, 2]
    bb = BoundingBox(pc.points)
    pc_wrapper = PointCloudWrapper("name", pc, 0.2, data)
    pc_wrapper.preprocess_drawing(bb)
    # Create an OpenGL context by creating a window.
    window = Window(1200, 800)
    pc_gl = GlPoints(pc_wrapper)
    # Optionally, window.render_point_cloud(pc_gl) could be called here.
    assert pc_wrapper is not None
