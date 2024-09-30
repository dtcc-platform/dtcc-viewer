# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np
import trimesh
import dtcc_core.io as io

from affine import Affine
from pprint import pp
from dtcc_viewer import utils
from dtcc_core.io import pointcloud, meshes, roadnetwork
from dtcc_core.io import load_raster, load_roadnetwork
from dtcc_core.model import City, Mesh, PointCloud, Object, Raster, Grid, VolumeGrid, Field
from dtcc_core.model import VolumeMesh, LineString, MultiLineString, Building, RoadNetwork
from dtcc_core.model.object.object import GeometryType
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.utils import *
from dtcc_viewer.utils import *
from dtcc_viewer.logging import set_log_level
from shapely.geometry import Point
from dtcc_core.builder import clean_building_surfaces


def pointcloud_example_1():
    filename_csv = "../../../data/models/PointCloud_HQ.csv"
    pc = pointcloud.load(filename_csv)
    data = pc.points[:, 0]
    pc.view(data=data)


def pointcloud_example_2():
    file = "../../../../dtcc-demo-data/helsingborg-harbour-2022/pointcloud.las"
    pc = pointcloud.load(file)

    field = Field(name="Field: z", values=pc.points[:, 2])
    pc.add_field(field)

    data_dict = {}
    data_dict["vertex_x2"] = pc.points[:, 0] * pc.points[:, 0]
    data_dict["vertex_y2"] = pc.points[:, 1] * pc.points[:, 1]
    data_dict["vertex_z2"] = pc.points[:, 2] * pc.points[:, 2]
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


def mesh_example_4():
    window = Window(1200, 800)
    scene = Scene()
    mesh = meshes.load_mesh("../../../data/models/CitySurface.obj")
    pc = PointCloud(points=mesh.vertices)
    scene.add_mesh("MESH", mesh)
    scene.add_pointcloud("PC", pc)
    window.render(scene)


def mesh_example_5():
    file = "../../../data/models/CitySurface.obj"
    mesh = meshes.load_mesh(file)
    face_mid_pts = calc_face_mid_points(mesh)
    field1 = Field(name="Field: face_z", values=face_mid_pts[:, 2], dim=1)
    field2 = Field(name="Field: vertex_z", values=mesh.vertices[:, 2], dim=1)
    mesh.add_field(field1)
    mesh.add_field(field2)
    mesh.view()


def multi_geometry_example_2():
    pc = pointcloud.load("../../../data/models/PointCloud_HQ.csv")
    mesh = meshes.load_mesh("../../../data/models/CitySurface.obj")

    lss = []
    for i in range(30):
        lss.append(create_ls_circle(Point(0, 0, 0), 50 + i * 5, 200))

    mls = MultiLineString(linestrings=lss)
    window = Window(1200, 800)
    scene = Scene()
    scene.add_pointcloud("Pointcloud", pc, 0.2)
    scene.add_mesh("Mesh", mesh)
    scene.add_multilinestring("MultiLineString", mls)

    window.render(scene)


def linestring_example_2():
    # Create instances of LineString
    linestring = LineString(vertices=np.array([[0, 5], [1, 1], [2, 1], [4, 3], [0, 4]]))
    linestring.view()


def multilinestring_example_1():
    line1 = LineString(vertices=np.array([[0, 0], [1, 1], [2, 2]]))
    line2 = LineString(vertices=np.array([[2, 2], [3, 3], [4, 4]]))
    line3 = LineString(vertices=np.array([[4, 4], [5, 5], [6, 6]]))

    line_strings = [line1, line2, line3]
    multilinestring = MultiLineString(linestrings=line_strings)
    multilinestring.view()


def multi_geometry_example_1():
    pc = pointcloud.load("../../../data/models/PointCloud_HQ.csv")
    all_pcs = split_pc_in_stripes(3, pc, Direction.x)

    mesh_tri = trimesh.load_mesh("../../../data/models/CitySurface.obj")
    face_mid_pts = utils.calc_face_mid_points(mesh_tri)
    all_meshes = utils.split_mesh_in_stripes(3, mesh_tri, face_mid_pts, Direction.y)

    window = Window(1200, 800)
    scene = Scene()

    data = pc.points[:, Direction.x]
    scene.add_pointcloud("pc", pc, 0.2, data)

    for i, mesh in enumerate(all_meshes):
        data = mesh.vertices[:, Direction.y]
        scene.add_mesh("Mesh " + str(i), mesh, data)

    window.render(scene)


def multilinestring_example_2():
    lss = []
    for i in range(15):
        lss.append(create_ls_circle(Point(0, 0, 0), 10 + i, 100))

    mls = MultiLineString(linestrings=lss)
    window = Window(1200, 800)
    scene = Scene()
    scene.add_multilinestring("MultiLineString", mls)
    window.render(scene)


def multilinestring_example_3():
    lss = []

    for i in range(100):
        ls = create_ls_circle(Point(0, 0, 0), 1 + i, 100)
        lss.append(ls)

    mls = MultiLineString(linestrings=lss)

    x_vals = np.array([pt[0] for ls in lss for pt in ls.vertices])
    y_vals = np.array([pt[1] for ls in lss for pt in ls.vertices])
    z_vals = np.array([pt[2] for ls in lss for pt in ls.vertices])

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
    city = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")
    city.view()


def city_example_2():
    city = dtcc_io.load_cityjson("../../../data/models/rotterdam.city.json")
    city = clean_building_surfaces(city, GeometryType.LOD2)
    city.view()


def city_example_3():
    city = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")
    building_year = [1900, 1920, 1930, 1945, 1960, 1980, 2000, 2010, 2020, 2030]
    residents = np.arange(10) + 5

    for i, building in enumerate(city.buildings):
        building.attributes["energy consumption"] = i
        building.attributes["no residents"] = residents[i % len(residents)]
        building.attributes["year"] = building_year[i % len(building_year)]
    city.view()


def city_example_4():
    file1 = "../../../data/models/citygml_loz_buildings_energy_20230819.json"
    file2 = "../../../data/models/lozenets_citygml2cityjson.json"
    file3 = "../../../data/models/lozenets_citygml2cityjson_lod1_replaced.json"
    file4 = "../../../data/models/lozenets_citygml2cityjson_with_facades_2.json"
    city = dtcc_io.load_cityjson(file1)
    city.view()


def city_example_5():
    city = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")

    # Add some geometries to the city
    n = 30
    bounds = city.bounds
    bounds.zmax = 100
    grid = Grid(width=n, height=n)
    grid.bounds = bounds
    field1 = Field(name="field1", values=np.random.rand(grid.num_vertices), dim=1)
    field2 = Field(name="field2", values=np.random.rand(grid.num_vertices), dim=1)
    grid.add_field(field1)
    grid.add_field(field2)

    city.add_geometry(grid, "grid")

    vgrid = VolumeGrid(width=n, height=n, depth=n)
    vgrid.bounds = bounds
    field3 = Field(name="field3", values=np.random.rand(vgrid.num_vertices), dim=1)
    field4 = Field(name="field4", values=np.random.rand(vgrid.num_vertices), dim=1)

    vgrid.add_field(field3)
    vgrid.add_field(field4)
    city.add_geometry(vgrid, "volume_grid")

    city.view()


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


def building_example_3():
    city_dhg = dtcc_io.load_cityjson("../../../data/models/denhaag.city.json")
    new_city = City()
    some_buildings = []
    for i, building in enumerate(city_dhg.buildings):
        if i < 1:
            some_buildings.append(building)

    new_city.attributes = city_dhg.attributes
    new_city.add_buildings(some_buildings)
    new_city.view()


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
    ms = create_cylinder(origo, 5, 10, 100)
    surface = create_surface_disc(Point(10, 0, 0), 5, 100)

    ls1 = create_ls_circle(origo, 20, 200)
    ls2 = create_ls_circle(origo, 10, 200)
    ls3 = create_ls_circle(origo, 15, 200)
    mls = MultiLineString(linestrings=[ls2, ls3])

    vmesh = create_tetrahedral_cube_mesh(10, 10, 10, 10)
    vmesh.vertices += np.array([20, -20, 0])

    bounds = Bounds(-20, -20, -10, -10, 0, 0)
    grid = Grid(width=30, height=50)
    grid.bounds = bounds

    bounds = Bounds(10, 10, 20, 20, 0, 10)
    vgrid = VolumeGrid(width=30, height=50, depth=20)
    vgrid.bounds = bounds

    bounds = Bounds(-30, -30, 30, 30, 0, 0)

    geometries = [mesh, ls1, ms, bounds, mls, surface, vmesh, grid, vgrid]
    print(type(geometries))
    window = Window(1200, 800)
    scene = Scene()
    scene.add_geometries("geometries", geometries)
    window.render(scene)


def bounds_example():
    bounds = Bounds(-10, -10, 10, 10, 0, 0)
    bounds.view()


def multisurface_example():
    cylinder_ms = create_cylinder(Point(0, 0, 0), 10, 10, 100)
    data1 = np.random.rand(len(cylinder_ms.surfaces))
    data2 = np.random.rand(len(cylinder_ms.surfaces))
    field1 = Field(name="field1", values=data1, dim=1)
    field2 = Field(name="field2", values=data2, dim=1)
    # cylinder_ms.add_field(field1)
    # cylinder_ms.add_field(field2)
    cylinder_ms.view()


def surface_example():
    surface = create_surface_disc(Point(0, 0, 0), 10, 100)
    surface.view()


def grid_example():
    bounds = Bounds(-12, -12, 12, 12, 0, 0)
    grid = Grid(width=30, height=40)
    grid.bounds = bounds
    field1 = Field(name="field", values=np.random.rand(grid.num_vertices))
    field2 = Field(name="field", values=np.random.rand(grid.num_vertices))
    grid.add_field(field1)
    grid.add_field(field2)
    grid.view()


def volume_grid_example():
    bounds = Bounds(5.0, -3.0, 10.0, 3.0, -4.0, 4.0)
    volume_grid = VolumeGrid(width=2, height=3, depth=4)
    volume_grid.bounds = bounds
    field1 = Field(name="field", values=np.random.rand(volume_grid.num_vertices))
    field2 = Field(name="field", values=np.random.rand(volume_grid.num_vertices))
    volume_grid.add_field(field1)
    volume_grid.add_field(field2)
    volume_grid.view()


def volume_mesh_example():
    vertices = 10.0 * np.array(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0.5, 0.5, 1]]
    )
    cells = np.array([[0, 1, 2, 4], [0, 2, 3, 4]])
    vmesh = VolumeMesh(vertices=vertices, cells=cells)
    vmesh.view()


def volume_mesh_example_2():
    vmesh = meshes.load_volume_mesh("../../../data/models/volume_mesh_step_34.vtu")
    vmesh.view()


def volume_mesh_example_3():
    window = Window(1200, 800)
    scene = Scene()
    vmesh = meshes.load_volume_mesh("../../../data/models/volume_mesh_step_34.vtu")
    pc = PointCloud(points=vmesh.vertices)
    scene.add_volume_mesh("volume mesh", vmesh)
    scene.add_pointcloud("point cloud", pc)
    window.render(scene)


def volume_mesh_example_4():

    np.set_printoptions(precision=3, suppress=True)

    window = Window(1200, 800)
    scene = Scene()
    vmesh = meshes.load_volume_mesh("../../../data/models/volume_mesh_step_34.vtu")
    cell_mask = np.zeros(len(vmesh.cells), dtype=bool)
    cell_mask[0::400] = True
    sub_vmesh = get_sub_volume_mesh_from_mask(cell_mask, vmesh)
    scene.add_volume_mesh("volume mesh", sub_vmesh)
    window.render(scene)


def volume_mesh_example_5():
    window = Window(1200, 800)
    scene = Scene()
    vmesh = create_tetrahedral_cube_mesh(10, 10, 10, 10)
    print(f"vmesh vertices count: {len(vmesh.vertices)}")
    print(f"vmesh cells count: {len(vmesh.cells)}")
    print(f"max cell index: {np.max(vmesh.cells)}")
    scene.add_volume_mesh("volume mesh", vmesh)
    window.render(scene)


def road_network_example():
    filename = "../../../data/models/helsingborg_road_data.shp"
    rn = load_roadnetwork(filename)
    rn.view()


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


def crasch_empty_geometry():

    window = Window(1200, 800)
    scene = Scene()
    vertices = np.array([])
    faces = np.array([])

    mesh = Mesh(vertices=vertices, faces=faces)
    ms = MultiSurface(surfaces=[])
    srf = Surface()
    mls = MultiLineString(linestrings=[])
    ls = LineString(vertices=np.array([]))
    pc = PointCloud(points=np.array([]))
    city = City()
    obj = Object()
    grid = Grid()
    vgrid = VolumeGrid()
    building = Building()
    roadnetwork = RoadNetwork()
    vmesh = VolumeMesh()
    bounds = Bounds()
    raster = Raster(data=np.array([]))

    scene.add_mesh("empty mesh", mesh)
    scene.add_multisurface("empty ms", ms)
    scene.add_surface("empty srf", srf)
    scene.add_city("empty city", city)
    scene.add_object("empty obj", obj)
    scene.add_pointcloud("empty pc", pc)
    scene.add_linestring("empty ls", ls)
    scene.add_multilinestring("empty mls", mls)
    scene.add_grid("empty grid", grid)
    scene.add_volume_grid("empty vgrid", vgrid)
    scene.add_building("empty building", building)
    scene.add_roadnetwork("empty roadnetwork", roadnetwork)
    scene.add_volume_mesh("empty vmesh", vmesh)
    scene.add_bounds("empty bounds", bounds)
    scene.add_raster("empty raster", raster)

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
    # mesh_example_4()
    # mesh_example_5()
    # linestring_example_2()
    # multilinestring_example_1()
    # multilinestring_example_2()
    # multilinestring_example_3()
    # multi_geometry_example_1()
    # multi_geometry_example_2()
    # geometries_example()
    # bounds_example()
    # multisurface_example()
    # surface_example()
    # grid_example()
    # volume_grid_example()
    # volume_mesh_example()
    # volume_mesh_example_2()
    # volume_mesh_example_3()
    # volume_mesh_example_4()
    # raster_example_1()
    # raster_example_2()
    # raster_example_3()
    # raster_example_4()
    # road_network_example()
    # building_example_2()
    # city_example_1()
    # city_example_2()
    # city_example_3()
    # city_example_4()
    # city_example_5()
    # building_example_1()
    # building_example_3()
    # object_example_1()
    # object_example_2()
    # crasch_test()
    # crasch_empty_geometry()
