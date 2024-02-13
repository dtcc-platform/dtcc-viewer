# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
import trimesh
import time

from pprint import pp

from dtcc_viewer import *
from dtcc_viewer.colors import color_maps
from typing import List, Iterable
from dtcc_viewer import utils
from dtcc_io import pointcloud, meshes
import dtcc_io
from dtcc_model import City, Mesh, PointCloud
from dtcc_viewer.opengl_viewer.window import Window
from dtcc_viewer.opengl_viewer.scene import Scene
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper
from dtcc_viewer.opengl_viewer.pointcloud_wrapper import PointCloudWrapper
from dtcc_viewer.opengl_viewer.utils import *
from dtcc_viewer.utils import *
from dtcc_io import load_roadnetwork
from dtcc_viewer.logging import set_log_level


def pointcloud_example_1():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    pc.view()


def pointcloud_example_2():
    file = "../../../../dtcc-demo-data/helsingborg-harbour-2022/pointcloud.las"
    pc = pointcloud.load(file)
    data_dict = {}
    data_dict["vertex_x"] = pc.points[:, 0]
    data_dict["vertex_y"] = pc.points[:, 1]
    data_dict["vertex_z"] = pc.points[:, 2]
    pc.view(data=data_dict)


def mesh_example_1():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    mesh.view()


def mesh_example_2():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    face_mid_pts = utils.calc_face_mid_points(mesh)
    color_data = face_mid_pts[:, 2]
    mesh.view(data=color_data, shading=MeshShading.ambient)


def mesh_example_3():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    # mesh = utils.get_sub_mesh([0.45, 0.55], [0.45, 0.55], mesh)
    print("Vertex count: " + str(len(mesh.vertices)))
    face_mid_pts = calc_face_mid_points(mesh)
    data_dict = {}
    data_dict["vertex_x"] = mesh.vertices[:, 0]
    data_dict["face_x"] = face_mid_pts[:, 0]
    data_dict["vertex_y"] = mesh.vertices[:, 1]
    data_dict["face_y"] = face_mid_pts[:, 1]
    data_dict["vertex_z"] = mesh.vertices[:, 2]
    data_dict["face_z"] = face_mid_pts[:, 2]
    print(len(data_dict["vertex_x"]))
    mesh.view(data=data_dict)


def mesh_point_cloud_example_1():
    file_1 = "../../../data/models/CitySurface.obj"
    file_2 = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(file_2)
    mesh = meshes.load_mesh(file_1)
    mesh.view(pc=pc, pc_size=1.0)


def mesh_point_cloud_example_2():
    file_1 = "../../../data/models/CitySurface.obj"
    file_2 = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(file_2)
    pc_data = pc.points[:, 0]
    mesh = meshes.load_mesh(file_1)
    mesh_data = mesh.vertices[:, 1]
    pc.view(mesh=mesh, data=pc_data, mesh_data=mesh_data)


def mesh_point_cloud_example_3():
    file_1 = "../../../data/models/CitySurface.obj"
    file_2 = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(file_2)
    pc_data_dict = {}
    pc_data_dict["point_x"] = pc.points[:, 0]
    pc_data_dict["point_y"] = pc.points[:, 1]
    pc_data_dict["point_z"] = pc.points[:, 2]

    mesh = meshes.load_mesh(file_1)
    mesh_data_dict = {}
    mesh_data_dict["vertex_x"] = mesh.vertices[:, 0]
    mesh_data_dict["vertex_y"] = mesh.vertices[:, 1]
    mesh_data_dict["vertex_z"] = mesh.vertices[:, 2]
    pc.view(data=pc_data_dict, mesh=mesh, mesh_data=mesh_data_dict)


def multi_geometry_example_1():
    window = Window(1200, 800)
    scene = Scene()

    # Import meshes to be viewed
    mesh_a = meshes.load_mesh("../../../data/models/CitySurfaceA.obj")
    mesh_b = meshes.load_mesh("../../../data/models/CitySurfaceB.obj")

    data_a = {}
    data_a["vertex_x"] = mesh_a.vertices[:, 0]
    data_a["vertex_y"] = mesh_a.vertices[:, 1]

    data_b = {}
    data_b["vertex_x"] = mesh_b.vertices[:, 0]
    data_b["vertex_y"] = mesh_b.vertices[:, 1]

    scene.add_mesh("mesh A", mesh_a, data_a)
    scene.add_mesh("mesh B", mesh_b, data_b)

    # Import point clodus to be viewed
    pc_a = pointcloud.load("../../../data/models/PointCloud_HQ_A.csv")
    pc_b = pointcloud.load("../../../data/models/PointCloud_HQ_B.csv")
    pc_data_a = pc_a.points[:, 0]
    pc_data_b = pc_b.points[:, 1]
    scene.add_pointcloud("pc A", pc_a, 0.2, pc_data_a)
    scene.add_pointcloud("pc B", pc_b, 0.2, pc_data_b)

    window.render(scene)


def multi_geometry_example_2():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    all_pcs = split_pc_in_stripes(10, pc, Direction.x)

    scene = Scene()
    for i, pc in enumerate(all_pcs):
        data = pc.points[:, Direction.x]
        print(len(pc.points))
        scene.add_pointcloud("pc" + str(i), pc, 0.1 + i * 0.1, data)

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
        scene.add_mesh("Mesh " + str(i), mesh, data)

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
        scene.add_pointcloud("pc " + str(i), pc, 0.2, data)

    for i, mesh in enumerate(all_meshes):
        data = mesh.vertices[:, Direction.y]
        scene.add_mesh("Mesh " + str(i), mesh, data)

    window = Window(1200, 800)
    window.render(scene)


def roadnetwork_example_1():
    filename = "../../../data/models/helsingborg_road_data.shp"
    roadnetwork = load_roadnetwork(filename, type_field="Gcm_typ", name_field="id")
    roadnetwork.view()


def roadnetwork_example_2():
    window = Window(1200, 800)
    scene = Scene()

    filename = "../../../data/models/helsingborg_road_data.shp"
    rn = load_roadnetwork(filename, type_field="Gcm_typ", name_field="id")
    scene.add_roadnetwork("Road Network", rn)
    window.render(scene)


def roadnetwork_example_3():
    window = Window(1200, 800)
    scene = Scene()

    file_1 = "../../../data/models/helsingborg_vagslag.shp"
    file_3 = "../../../data/models/helsingborg_cykel.shp"

    rn_1 = load_roadnetwork(file_1, type_field="Typ", name_field="id")
    rn_3 = load_roadnetwork(file_3, type_field="ELEMENT_ID", name_field="id")

    scene.add_roadnetwork("Road Network", rn_1)
    scene.add_roadnetwork("Road Network", rn_3)
    window.render(scene)


def city_example_1():
    # city_rot = dtcc_io.load_cityjson("../../../data/models/rotterdam.city.json")
    # city_mon = dtcc_io.load_cityjson("../../../data/models/montreal.city.json")
    # city_vie = dtcc_io.load_cityjson("../../../data/models/vienna.city.json")
    city_dhg = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")
    # city_rwy = dtcc_io.load_cityjson("../../../data/models/railway.city.json")
    # city_nyc = dtcc_io.load_cityjson("../../../data/models/newyork.city.json")

    # city_rot.view()
    # city_mon.view()
    # city_vie.view()
    city_dhg.view()
    # city_rwy.view()
    # city_nyc.view()


if __name__ == "__main__":
    os.system("clear")
    print("-------- View test started from main function -------")
    set_log_level("INFO")
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
    # multi_geometry_example_4()
    # roadnetwork_example_1()
    # roadnetwork_example_2()
    # roadnetwork_example_3()
    city_example_1()
