# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import os
import numpy as np

from pprint import pp
from dtcc_viewer import * 
from dtcc_viewer.colors import color_maps
from typing import List, Iterable
from dtcc_viewer import utils
from dtcc_io import pointcloud as pc
from dtcc_io import meshes as ms
from dtcc_viewer import pointcloud_opengl
from dtcc_viewer import mesh_opengl


def pointcloud_example():
    filename_las = '../../../data/models/PointCloud2.las'
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    loaded_pc = pc.load(filename_las)
    pointcloud_opengl.view(loaded_pc)

def mesh_example():
    filename_obj = '../../../data/models/CitySurface.obj'
    loaded_mesh = ms.load_mesh(filename_obj)
    mesh_opengl.view(loaded_mesh)

def mesh_point_cloud_example():
    filename_obj = '../../../data/models/CitySurface.obj'
    filename_csv = '../../../data/models/PointCloud_HQ.csv'
    loaded_pc = pc.load(filename_csv)
    loaded_mesh = ms.load_mesh(filename_obj)
    mesh_opengl.view(loaded_mesh, loaded_pc)

 
if __name__ == '__main__':

    os.system('clear')
    print("-------- View test started from main function -------")

    #pointcloud_example()
    #mesh_example()
    mesh_point_cloud_example()
    