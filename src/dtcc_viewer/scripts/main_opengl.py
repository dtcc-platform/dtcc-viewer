# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
import trimesh

from pprint import pp

from dtcc_viewer import *
from dtcc_viewer.colors import color_maps
from typing import List, Iterable
from dtcc_viewer import utils
from dtcc_io import pointcloud
from dtcc_io import meshes
from dtcc_io import city
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.scene import Scene
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.utils import *


def pointcloud_example_1():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    pc.view()


def pointcloud_example_2():
    file = "../../../../dtcc-demo-data/helsingborg-residential-2022/pointcloud.las"
    pc = pointcloud.load(file)

    color_data = pc.points[:, 2]
    color_data = abs(pc.points[:, 2]) / pc.points[:, 2].max()
    colors = np.zeros((len(pc.points), 3))
    colors[:, 0] = color_data
    colors[:, 2] = color_data
    pc.view(pc_colors=colors)


def pointcloud_example_3():
    file = "../../../../dtcc-demo-data/helsingborg-harbour-2022/pointcloud.las"
    pc = pointcloud.load(file)
    color_data = pc.points[:, 2]
    color_data = abs(pc.points[:, 2]) / pc.points[:, 2].max()
    colors = np.zeros((len(pc.points), 3))
    colors[:, 0] = color_data
    colors[:, 2] = color_data
    pc.view(pc_colors=colors)


def mesh_example_1():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    mesh.view()


def mesh_example_2():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    face_mid_pts = utils.calc_face_mid_points(mesh)
    color_data = face_mid_pts[:, 2]
    mesh.view(mesh_data=color_data)


def mesh_example_3():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    color_data = abs(mesh.vertices[:, 2] / mesh.vertices[:, 2].max())
    colors = np.zeros((len(mesh.vertices), 3))
    colors[:, 0] = color_data
    mesh.view(mesh_colors=colors)


def mesh_point_cloud_example_1():
    file_1 = "../../../data/models/CitySurface.obj"
    file_2 = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(file_2)
    mesh = meshes.load_mesh(file_1)
    mesh.view(pc=pc)


def mesh_point_cloud_example_2():
    file_1 = "../../../data/models/CitySurface.obj"
    file_2 = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(file_2)
    mesh = meshes.load_mesh(file_1)
    pc.view(mesh=mesh)


def mesh_point_cloud_example_3():
    file_1 = "../../../data/models/CitySurface.obj"
    file_2 = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(file_2)
    pc_data = pc.points[:, 0]
    mesh = meshes.load_mesh(file_1)
    mesh_data = mesh.vertices[:, 1]
    pc.view(mesh=mesh, pc_data=pc_data, mesh_data=mesh_data)


def multi_geometry_example_1():
    window = Window(1200, 800)
    scene = Scene()

    # Import meshes to be viewed
    mesh_a = meshes.load_mesh("../../../data/models/CitySurfaceA.obj")
    mesh_b = meshes.load_mesh("../../../data/models/CitySurfaceB.obj")
    data_a = mesh_a.vertices[:, 1]
    data_b = mesh_b.vertices[:, 0]

    # Combine mesh and coloring data in a MeshData object and add to scene
    md_a = MeshData("mesh A", mesh_a, data_a)
    md_b = MeshData("mesh B", mesh_b, data_b)
    scene.add_mesh_data_list([md_a, md_b])

    # Import point clodus to be viewed
    pc_a = pointcloud.load("../../../data/models/PointCloud_HQ_A.csv")
    pc_b = pointcloud.load("../../../data/models/PointCloud_HQ_B.csv")
    pc_data_a = pc_a.points[:, 0]
    pc_data_b = pc_b.points[:, 1]

    # Combine pc and coloring data in a PointCloudData object and add to scene
    pcd_a = PointCloudData("pc A", pc_a, pc_data_a)
    pcd_b = PointCloudData("pc B", pc_b, pc_data_b)
    scene.add_pointcloud_data_list([pcd_a, pcd_b])

    window.render(scene)


def multi_geometry_example_2():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    all_pcs = split_pc_in_stripes(10, pc, Direction.x)

    scene = Scene()
    for i, pc in enumerate(all_pcs):
        data = pc.points[:, Direction.x]
        pcd = PointCloudData("pc" + str(i), pc, data)
        scene.add_pointcloud_data(pcd)

    window = Window(1200, 800)
    window.render(scene)


def multi_geometry_example_3():
    filename_obj = "../../../data/models/CitySurface.obj"
    mesh_tri = trimesh.load_mesh(filename_obj)
    face_mid_pts = utils.calc_face_mid_points(mesh_tri)
    split_meshes = utils.split_mesh_in_stripes(4, mesh_tri, face_mid_pts, Direction.x)

    scene = Scene()
    for i, mesh in enumerate(split_meshes):
        data = mesh.vertices[:, Direction.x]
        md = MeshData("Mesh " + str(i), mesh, data)
        scene.add_mesh_data(md)

    window = Window(1200, 800)
    window.render(scene)


def multi_geometry_example_4():
    pc = pointcloud.load("../../../data/models/PointCloud_HQ.csv")
    all_pcs = split_pc_in_stripes(8, pc, Direction.x)

    mesh_tri = trimesh.load_mesh("../../../data/models/CitySurface.obj")
    face_mid_pts = utils.calc_face_mid_points(mesh_tri)
    all_meshes = utils.split_mesh_in_stripes(8, mesh_tri, face_mid_pts, Direction.y)

    scene = Scene()

    for i, pc in enumerate(all_pcs):
        data = pc.points[:, Direction.x]
        pcd = PointCloudData("pc " + str(i), pc, data)
        scene.add_pointcloud_data(pcd)

    for i, mesh in enumerate(all_meshes):
        data = mesh.vertices[:, Direction.y]
        md = MeshData("Mesh " + str(i), mesh, data)
        scene.add_mesh_data(md)

    window = Window(1200, 800)
    window.render(scene)


if __name__ == "__main__":
    os.system("clear")
    print("-------- View test started from main function -------")
    # pointcloud_example_1()
    # pointcloud_example_2()
    # pointcloud_example_3()
    # mesh_example_1()
    # mesh_example_2()
    # mesh_example_3()
    # mesh_point_cloud_example_1()
    # mesh_point_cloud_example_2()
    # mesh_point_cloud_example_3()
    # multi_geometry_example_1()
    # multi_geometry_example_2()
    # multi_geometry_example_3()
    multi_geometry_example_4()
