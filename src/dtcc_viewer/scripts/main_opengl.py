# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np

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

def window_gui_example():
    window = Window(1200, 800)
    window.render_empty()

def pointcloud_example_1():
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    pc = pointcloud.load(filename_csv)
    pc.view()    

def pointcloud_example_2():
    filename_las = '../../../data/models/PointCloud2.las'
    pc = pointcloud.load(filename_las)
    color_data = pc.points[:,0]
    pc.view(pc_data = color_data)

def mesh_example_1():
    filename_obj = '../../../data/models/CitySurface.obj'
    mesh = meshes.load_mesh(filename_obj)
    mesh.view()

def mesh_example_2():
    filename_obj = '../../../data/models/CitySurface.obj'
    mesh = meshes.load_mesh(filename_obj)
    face_mid_pts = utils.calc_face_mid_points(mesh)
    color_data = face_mid_pts[:,2]
    mesh.view(mesh_data=color_data)

def mesh_example_3():
    filename_obj = '../../../data/models/CitySurface.obj'
    mesh = meshes.load_mesh(filename_obj)
    color_data = mesh.vertices[:,2]
    #color_data = color_data * color_data
    mesh.view(mesh_data=color_data)

def mesh_point_cloud_example_1():
    filename_obj = '../../../data/models/CitySurface.obj'
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    pc = pointcloud.load(filename_csv)
    mesh = meshes.load_mesh(filename_obj)
    mesh.view(pc=pc)

def mesh_point_cloud_example_2():
    filename_obj = '../../../data/models/CitySurface.obj'
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    pc = pointcloud.load(filename_csv)
    mesh = meshes.load_mesh(filename_obj)
    pc.view(mesh=mesh)
 
def mesh_point_cloud_example_3():
    filename_obj = '../../../data/models/CitySurface.obj'
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    pc = pointcloud.load(filename_csv)
    pc_data = pc.points[:,0]
    mesh = meshes.load_mesh(filename_obj)
    mesh_data = mesh.vertices[:,1]
    pc.view(mesh=mesh, pc_data = pc_data, mesh_data = mesh_data)


if __name__ == '__main__':

    os.system('clear')
    print("-------- View test started from main function -------")
    #window_gui_example()
    #pointcloud_example_1()
    #pointcloud_example_2()
    #mesh_example_1()
    #mesh_example_2()
    #mesh_example_3()
    #mesh_point_cloud_example_1()
    #mesh_point_cloud_example_2()
    mesh_point_cloud_example_3()
    