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

def pointcloud_example_1():
    filename_las = '../../../data/models/PointCloud2.las'
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    pc = pointcloud.load(filename_las)
    pc.view()

def pointcloud_example_2():
    filename_csv = '../../../data/models/PointCloud_LQ.csv'
    pc = pointcloud.load(filename_csv)
    pc.view()    

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
    color_data = mesh.vertices[:,0]
    color_data = color_data * color_data
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
 

if __name__ == '__main__':

    os.system('clear')
    print("-------- View test started from main function -------")
    pointcloud_example_1()
    #pointcloud_example_2()
    #mesh_example_1()
    #mesh_example_2()
    #mesh_example_3()
    #mesh_point_cloud_example_1()
    #mesh_point_cloud_example_2()
    