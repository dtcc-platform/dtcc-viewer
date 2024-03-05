# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
import trimesh
import time
import dtcc_io

from affine import Affine

from pprint import pp

# from dtcc_viewer import *
from dtcc_viewer import utils
from dtcc_io import pointcloud, meshes
from dtcc_io import load_roadnetwork
from dtcc_model import City, Mesh, PointCloud, Object, Raster
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.utils import *
from dtcc_viewer.logging import set_log_level
from shapely.geometry import LineString, Point
from dtcc_viewer.opengl.bundle import Bundle


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
    data_array = face_mid_pts[:, 2]
    mesh.view(data=data_array, shading=Shading.ambient)


def mesh_example_3():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    mesh = utils.get_sub_mesh([0.45, 0.55], [0.45, 0.55], mesh)
    face_mid_pts = calc_face_mid_points(mesh)
    data_dict = {}
    data_dict["vertex_x"] = mesh.vertices[:, 0]
    data_dict["face_x"] = face_mid_pts[:, 0]
    data_dict["vertex_y"] = mesh.vertices[:, 1]
    data_dict["face_y"] = face_mid_pts[:, 1]
    data_dict["vertex_z"] = mesh.vertices[:, 2]
    data_dict["face_z"] = face_mid_pts[:, 2]
    mesh.view(data=data_dict)


def multi_geometry_example_1():
    pc = pointcloud.load("../../../data/models/PointCloud_HQ.csv")
    all_pcs = split_pc_in_stripes(4, pc, Direction.x)

    mesh_tri = trimesh.load_mesh("../../../data/models/CitySurface.obj")
    face_mid_pts = utils.calc_face_mid_points(mesh_tri)
    all_meshes = utils.split_mesh_in_stripes(4, mesh_tri, face_mid_pts, Direction.y)

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
    rn = load_roadnetwork(filename, type_field="Gcm_typ", name_field="id")
    data_dict = {}
    data_dict["vertex_x"] = rn.vertices[:, 0]
    data_dict["vertex_y"] = rn.vertices[:, 1]
    rn.view()


def roadnetwork_example_2():
    window = Window(1200, 800)
    scene = Scene()

    file_1 = "../../../data/models/helsingborg_vagslag.shp"
    file_3 = "../../../data/models/helsingborg_cykel.shp"

    rn_1 = load_roadnetwork(file_1, type_field="Typ", name_field="id")
    rn_3 = load_roadnetwork(file_3, type_field="ELEMENT_ID", name_field="id")

    scene.add_roadnetwork("Road Network", rn_1)
    scene.add_roadnetwork("Road Network", rn_3)
    window.render(scene)


def linestring_example_1():
    linestring_1 = LineString([[0, 0, 0], [1, 1, 0], [2, 2, 0], [1, 2, 0], [3, 1, 0]])
    linestring_2 = LineString([[1, 2, 5], [1, 3, 0], [4, 6, 0], [8, 2, 0], [5, 6, 1]])
    linestring_3 = LineString([[5, 2, 1], [0, 2, 1], [4, 2, 0], [7, 3, 0]])

    linestrings = [linestring_1, linestring_2, linestring_3]

    scene = Scene()
    scene.add_linestrings("Linestrings", linestrings)

    window = Window(1200, 800)
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


def building_example_1():
    city_dhg = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")
    building = city_dhg.buildings[5]
    building.view()


def building_example_2():
    window = Window(1200, 800)
    scene = Scene()

    city_dhg = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")
    for i, building in enumerate(city_dhg.buildings):
        if i < 10:
            scene.add_building(f"building {i}", building)

    window.render(scene)


def object_example_1():
    sphere_mesh = create_sphere_mesh(Point(20, 0, 0), 3, 50, 50)
    circle_ls = create_linestring_circle(Point(0, 0, 0), 20, 200)
    cylinder_ms = create_cylinder(Point(0, 0, 0), 10, 10, 100)
    obj = Object()

    obj.geometry[GeometryType.MESH] = sphere_mesh
    obj.geometry[GeometryType.LINESTRING] = circle_ls
    obj.geometry[GeometryType.LOD2] = cylinder_ms
    obj.view()


def object_example_2():
    r, n = 20, 10
    z1, z2, z3 = 0, 5, 10
    a = 2 * math.pi / n
    meshes, mss, lss, pts = [], [], [], []
    for i in range(n):
        x = r * math.cos(i * a)
        y = r * math.sin(i * a)
        mesh = create_sphere_mesh(Point(x, y, z1), 3, 30, 30)
        ls = create_linestring_circle(Point(x, y, z2), 20, 200)
        ms = create_cylinder(Point(x, y, z3), 3, 10, 100)
        meshes.append(mesh)
        lss.append(ls)
        mss.append(ms)
        pts.append([x, y, z1])

    pts = np.array(pts)
    pointcloud = PointCloud(pts)
    obj = Object()
    obj.geometry[GeometryType.MESH] = meshes
    obj.geometry[GeometryType.LINESTRING] = lss
    obj.geometry[GeometryType.LOD2] = mss
    obj.geometry[GeometryType.POINT_CLOUD] = pointcloud
    obj.view()


def raster_example_1():
    # Define the coordinate reference system (CRS)
    crs = "EPSG:4326"  # For example, WGS84

    # Create some sample data
    data = np.random.rand(10000, 10000)
    georef = Affine.identity()
    raster = Raster(data=data, georef=georef, crs=crs)

    # Print information about the raster
    print(raster)
    print("Shape:", raster.shape)
    print("Height:", raster.height)
    print("Width:", raster.width)
    print("Channels:", raster.channels)
    print("Bounds:", raster.bounds)
    print("Cell Size:", raster.cell_size)

    # Access a value at a specific coordinate
    value = raster.get_value(x=10.0, y=20.0)
    print("Value at (10.0, 20.0):", value)

    raster.view()


if __name__ == "__main__":
    os.system("clear")
    print("-------- View test started from main function -------")
    set_log_level("INFO")
    # pointcloud_example_1()
    # pointcloud_example_2()
    # mesh_example_2()
    # mesh_example_3()
    # multi_geometry_example_1()
    # roadnetwork_example_1()
    # roadnetwork_example_2()
    # building_example_2()
    # linestring_example_1()
    # mesh_example_1()
    # city_example_1()
    # building_example_1()
    # object_example_1()
    # object_example_2()
    raster_example_1()
