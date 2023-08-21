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
from dtcc_viewer import pointcloud_opengl
from dtcc_viewer import mesh_opengl
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.utils import *


def window_gui_example():
    window = Window(1200, 800)
    window.render_empty()


def pointcloud_example_1():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    pc.view()


def pointcloud_example_2():
    filename_las = "../../../data/models/PointCloud2.las"
    pc = pointcloud.load(filename_las)
    color_data = pc.points[:, 0]
    pc.view(pc_data=color_data)


def mesh_example_1():
    filename_obj = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(filename_obj)
    mesh.view()


def mesh_example_2():
    filename_obj = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(filename_obj)
    face_mid_pts = utils.calc_face_mid_points(mesh)
    color_data = face_mid_pts[:, 2]
    mesh.view(mesh_data=color_data)


def mesh_example_3():
    filename_obj = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(filename_obj)
    color_data = mesh.vertices[:, 2]
    # color_data = color_data * color_data
    mesh.view(mesh_data=color_data)


def mesh_point_cloud_example_1():
    filename_obj = "../../../data/models/CitySurface.obj"
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    mesh = meshes.load_mesh(filename_obj)
    mesh.view(pc=pc)


def mesh_point_cloud_example_2():
    filename_obj = "../../../data/models/CitySurface.obj"
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    mesh = meshes.load_mesh(filename_obj)
    pc.view(mesh=mesh)


def mesh_point_cloud_example_3():
    filename_obj = "../../../data/models/CitySurface.obj"
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    pc_data = pc.points[:, 0]
    mesh = meshes.load_mesh(filename_obj)
    mesh_data = mesh.vertices[:, 1]
    pc.view(mesh=mesh, pc_data=pc_data, mesh_data=mesh_data)


def multi_geometry_example_1():
    window = Window(1200, 800)

    # Import meshes to be viewed
    mesh_a = meshes.load_mesh("../../../data/models/CitySurfaceA.obj")
    mesh_b = meshes.load_mesh("../../../data/models/CitySurfaceB.obj")
    mesh_data_a = mesh_a.vertices[:, 1]
    mesh_data_b = mesh_b.vertices[:, 0]
    meshes_imported = [mesh_a, mesh_b]

    # Import point clodus to be viewed
    pc_a = pointcloud.load("../../../data/models/PointCloud_HQ_A.csv")
    pc_b = pointcloud.load("../../../data/models/PointCloud_HQ_B.csv")
    pc_data_a = pc_a.points[:, 0]
    pc_data_b = pc_b.points[:, 1]
    pcs_imported = [pc_a, pc_b]

    # Calculate common recentering vector base of the bounding box of all combined vertices.
    recenter_vec = calc_multi_geom_recenter_vector(meshes_imported, pcs_imported)

    # Create mesh data classes that are structured for openggl calls
    mesh_data_obj_a = MeshData("mesh A", mesh_a, mesh_data_a, recenter_vec)
    mesh_data_obj_b = MeshData("mesh B", mesh_b, mesh_data_b, recenter_vec)
    mesh_data_list = [mesh_data_obj_a, mesh_data_obj_b]

    # Create point clode data classes that are structured for opengl calls
    pc_data_obj_a = PointCloudData("point cloud A", pc_a, pc_data_a, recenter_vec)
    pc_data_obj_b = PointCloudData("point cloud B", pc_b, pc_data_b, recenter_vec)
    pc_data_list = [pc_data_obj_a, pc_data_obj_b]

    window.render_multi(mesh_data_list, pc_data_list)


def multi_geometry_example_2():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    all_pcs = split_pc_in_stripes(10, pc, Direction.x)

    all_meshes = []

    # Calculate common recentering vector base of the bounding box of all combined vertices.
    recenter_vec = calc_multi_geom_recenter_vector(all_meshes, all_pcs)

    pc_data_list = []
    for i, pc_i in enumerate(all_pcs):
        pc_data = pc_i.points[:, Direction.x]
        pc_data_list.append(
            PointCloudData("point cloud " + str(i), pc_i, pc_data, recenter_vec)
        )

    window = Window(1200, 800)
    window.render_multi(all_meshes, pc_data_list)


def multi_geometry_example_3():
    filename_obj = "../../../data/models/CitySurface.obj"
    mesh_tri = trimesh.load_mesh(filename_obj)
    face_mid_pts = utils.calc_face_mid_points(mesh_tri)
    meshes = utils.split_mesh_in_stripes(4, mesh_tri, face_mid_pts, Direction.x)

    all_meshes = []
    all_pcs = []

    for i, mesh in enumerate(meshes):
        data = mesh.vertices[:, Direction.x]
        mesh_data_obj = MeshData("Mesh " + str(i), mesh, data)
        all_meshes.append(mesh_data_obj)

    window = Window(1200, 800)
    window.render_multi(all_meshes, all_pcs)


def multi_geometry_example_4():
    pc = pointcloud.load("../../../data/models/PointCloud_HQ.csv")
    all_pcs = split_pc_in_stripes(8, pc, Direction.x)

    mesh_tri = trimesh.load_mesh("../../../data/models/CitySurface.obj")
    all_meshes = utils.split_mesh_in_stripes(
        8, mesh_tri, utils.calc_face_mid_points(mesh_tri), Direction.y
    )

    recenter_vec = calc_multi_geom_recenter_vector(all_meshes, all_pcs)

    pc_data_list = []
    for i, pc_i in enumerate(all_pcs):
        pc_data = pc_i.points[:, Direction.x]
        pc_data_list.append(
            PointCloudData("point cloud " + str(i), pc_i, pc_data, recenter_vec)
        )

    mesh_data_list = []
    for i, mesh in enumerate(all_meshes):
        data = mesh.vertices[:, Direction.y]
        mesh_data_list.append(MeshData("Mesh " + str(i), mesh, data, recenter_vec))

    window = Window(1200, 800)
    window.render_multi(mesh_data_list, pc_data_list)


if __name__ == "__main__":
    os.system("clear")
    print("-------- View test started from main function -------")
    # window_gui_example()
    # pointcloud_example_1()
    # pointcloud_example_2()
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
