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
from dtcc_viewer import pointcloud_opengl, mesh_opengl, mesh_fancy_opengl, mesh_fancy_shadow_opengl


def pointcloud_example():

    filename_las = '../../../data/models/PointCloud2.las'
    loaded_pc = pc.load(filename_las)
    pointcloud_opengl.view(loaded_pc)


def mesh_example():

    filename_obj = '../../../data/models/CitySurface.obj'
    loaded_mesh = ms.load_mesh(filename_obj)
    mesh_opengl.view(loaded_mesh)


def mesh_fancy_example():

    filename_obj = '../../../data/models/CitySurface.obj'
    loaded_mesh = ms.load_mesh(filename_obj)
    mesh_fancy_opengl.view(loaded_mesh)


def mesh_fancy_shadows_example():

    filename_obj = '../../../data/models/CitySurface.obj'
    loaded_mesh = ms.load_mesh(filename_obj)
    mesh_fancy_shadow_opengl.view(loaded_mesh)




if __name__ == '__main__':

    os.system('clear')
    print("-------- View test started from main function -------")

    #pointcloud_example()
    #mesh_example()
    #mesh_fancy_example()
    mesh_fancy_shadows_example()

    