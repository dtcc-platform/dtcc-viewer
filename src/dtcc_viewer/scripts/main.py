# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
import trimesh
import dtcc_io

from affine import Affine
from pprint import pp
from dtcc_viewer import utils
from dtcc_io import pointcloud, meshes
from dtcc_io import load_raster
from dtcc_model import City, Mesh, PointCloud, Object, Raster, Grid, VolumeGrid
from dtcc_model import VolumeMesh
from dtcc_model.object.object import GeometryType
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.utils import *
from dtcc_viewer.logging import set_log_level
from shapely.geometry import LineString, Point, MultiLineString


def pointcloud_example_1():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    data = pc.points[:, 0]
    pc.view(data=data)


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
    mesh.view(data=data_array)


def mesh_example_3():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    # mesh = utils.get_sub_mesh([0.45, 0.55], [0.45, 0.55], mesh)
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
    all_pcs = split_pc_in_stripes(3, pc, Direction.x)

    mesh_tri = trimesh.load_mesh("../../../data/models/CitySurface.obj")
    face_mid_pts = utils.calc_face_mid_points(mesh_tri)
    all_meshes = utils.split_mesh_in_stripes(3, mesh_tri, face_mid_pts, Direction.y)

    window = Window(1200, 800)
    scene = Scene()

    for i, pc in enumerate(all_pcs):
        data = pc.points[:, Direction.x]
        scene.add_pointcloud("pc " + str(i), pc, 0.2, data)

    for i, mesh in enumerate(all_meshes):
        data = mesh.vertices[:, Direction.y]
        scene.add_mesh("Mesh " + str(i), mesh, data)

    window.render(scene)


def linestring_example_2():
    lss = []

    for i in range(100):
        ls = create_ls_circle(Point(0, 0, 0), 1 + i, 100)
        lss.append(ls)

    mls = MultiLineString(lss)

    x_vals = np.array([pt[0] for ls in lss for pt in ls.coords])
    y_vals = np.array([pt[1] for ls in lss for pt in ls.coords])
    z_vals = np.array([pt[2] for ls in lss for pt in ls.coords])

    data_dict = {}
    data_dict["vertex_x"] = x_vals
    data_dict["vertex_y"] = y_vals
    data_dict["vertex_z"] = z_vals
    data_dict["vertex_x2"] = x_vals * x_vals
    data_dict["vertex_y2"] = y_vals * y_vals
    data_dict["vertex_z2"] = z_vals * z_vals

    window = Window(1200, 800)
    scene = Scene()
    scene.add_multilinestring("Multi line strings", mls, data=data_dict)

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
    circle_ls = create_ls_circle(Point(0, 0, 0), 20, 200)
    cylinder_ms = create_cylinder(Point(0, 0, 0), 10, 10, 100)
    obj = Object()
    obj.geometry[GeometryType.MESH] = sphere_mesh
    obj.geometry[GeometryType.LINESTRING] = circle_ls
    obj.geometry[GeometryType.LOD2] = cylinder_ms
    obj.view()


def object_example_2():
    r, n = 20, 10
    z1, z2, z3, z4 = 0, 5, 10, 25
    a = 2 * math.pi / n
    meshes, mss, lss, pcs = [], [], [], []
    for i in range(n):
        x = r * math.cos(i * a)
        y = r * math.sin(i * a)
        mesh = create_sphere_mesh(Point(x, y, z1), 3, 30, 30)
        ls = create_ls_circle(Point(x, y, z2), 20, 200)
        ms = create_cylinder(Point(x, y, z3), 3, 10, 100)
        meshes.append(mesh)
        lss.append(ls)
        mss.append(ms)
        pts = mesh.vertices + np.array([0, 0, z4])
        pc = PointCloud(points=pts)
        pcs.append(pc)

    pts = np.array(pts)
    obj = Object()
    obj.geometry[GeometryType.MESH] = meshes
    obj.geometry[GeometryType.LINESTRING] = lss
    obj.geometry[GeometryType.LOD2] = mss
    obj.geometry[GeometryType.POINT_CLOUD] = pcs
    obj.view()


def raster_example_1():
    # Define the coordinate reference system (CRS)
    crs = "EPSG:4326"

    # Create some sample data
    data = np.arange(0, 15000 * 15000, 1).reshape(15000, 15000)
    # data = np.random.rand(150, 300)
    georef = Affine.identity()
    raster = Raster(data=data, georef=georef, crs=crs)

    raster.view()


def raster_example_2():
    x_range = (-2 * np.pi, 3 * np.pi)
    y_range = (-2 * np.pi, 3 * np.pi)
    (x, y, z) = double_sine_wave_surface(x_range, y_range, 200, 200, 1, 1)
    raster = Raster(data=z)

    raster.view()


def raster_example_3():
    raster = load_raster("../../../data/models/672_61_7550_2017.tif")
    raster.view()


def raster_example_4():
    raster = load_raster("../../../data/models/652_59_7550_2019.tif")
    raster.view()


def geometries_example():
    origo = Point(0, 0, 0)
    mesh = create_sphere_mesh(Point(20, 0, 0), 3, 50, 50)
    linestring_1 = create_ls_circle(origo, 20, 200)
    multi_surface = create_cylinder(origo, 5, 10, 100)
    bounds = Bounds(-10, -10, 10, 10, 0, 0)
    surface = create_surface_disc(Point(10, 0, 0), 5, 100)

    linestring_2 = create_ls_circle(origo, 10, 200)
    linestring_3 = create_ls_circle(origo, 15, 200)
    multi_ls = MultiLineString([linestring_2, linestring_3])

    geometries = [mesh, linestring_1, multi_surface, bounds, multi_ls, surface]
    print(type(geometries))
    window = Window(1200, 800)
    scene = Scene()
    scene.add_geometries("geometries", geometries)
    window.render(scene)


def bounds_example():
    bounds = Bounds(-10, -10, 10, 10, 0, 0)
    bounds.view()


def multilinestring_example():
    lss = []
    for i in range(5):
        lss.append(create_ls_circle(Point(0, 0, 0), 10 + i, 100))

    mls = MultiLineString(lss)
    window = Window(1200, 800)
    scene = Scene()
    scene.add_multilinestring("MultiLineString", mls)
    window.render(scene)


def multisurface_example():
    cylinder_ms = create_cylinder(Point(0, 0, 0), 10, 10, 100)
    cylinder_ms.view()


def surface_example():
    surface = create_surface_disc(Point(0, 0, 0), 10, 100)
    surface.view()


def grid_example():
    bounds = Bounds(-12, -12, 12, 12, 0, 0)
    grid = Grid(width=30, height=50, bounds=bounds)
    grid.view()


def volume_grid_example():
    bounds = Bounds(-2, -3, 2, 3, -4, 4)
    volume_grid = VolumeGrid(width=26, height=31, depth=43, bounds=bounds)
    volume_grid.view()


def volume_mesh_example():
    vertices = 10.0 * np.array(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0.5, 0.5, 1]]
    )
    cells = np.array([[0, 1, 2, 4], [0, 2, 3, 4]])
    vmesh = VolumeMesh(vertices=vertices, cells=cells)
    vmesh.view()


def crasch_test():

    window = Window(1200, 800)
    scene = Scene()

    vertices = np.array([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [5.0, 2.0, 3.0]])
    faces = np.array([[0, 1, 2]])

    mesh = Mesh(vertices=vertices, faces=faces)

    wrong_input = np.zeros(5)
    wrong_list = [7, 4.5, "text", None]

    scene.add_mesh("crasch mesh", mesh, None)
    scene.add_mesh("crasch mesh", None, None)
    scene.add_mesh("crasch mesh", wrong_input, None)
    scene.add_multisurface("crasch ms", None)
    scene.add_multisurface("crasch ms", wrong_input)
    scene.add_surface("crasch srf", None)
    scene.add_surface("crasch srf", wrong_input)
    scene.add_city("crasch city", None)
    scene.add_city("crasch city", wrong_input)
    scene.add_object("crasch obj", None)
    scene.add_object("crasch obj", wrong_input)
    scene.add_pointcloud("crasch pc", None)
    scene.add_pointcloud("crasch pc", wrong_input)
    scene.add_linestring("crasch ls", None)
    scene.add_linestring("crasch ls", wrong_input)
    scene.add_multilinestring("crasch mls", None)
    scene.add_multilinestring("crasch mls", wrong_input)
    scene.add_geometries("crasch geo", None)
    scene.add_geometries("crasch geo", wrong_input)
    scene.add_geometries("crasch geo", wrong_list)
    scene.add_bounds("crasch bounds", None)
    scene.add_bounds("crasch bounds", wrong_input)

    window.render(scene)


if __name__ == "__main__":
    os.system("clear")
    print("-------- View test started from main function -------")
    set_log_level("INFO")
    # pointcloud_example_1()
    # pointcloud_example_2()
    # mesh_example_1()
    # mesh_example_2()
    # mesh_example_3()
    # multi_geometry_example_1()
    # building_example_2()
    # linestring_example_2()
    # city_example_1()
    # building_example_1()
    # object_example_1()
    # object_example_2()
    # raster_example_1()
    # raster_example_2()
    # raster_example_3()
    # raster_example_4()
    geometries_example()
    # bounds_example()
    # multilinestring_example()
    # multisurface_example()
    # surface_example()
    # crasch_test()
    # grid_example()
    # volume_grid_example()
    # volume_mesh_example()
