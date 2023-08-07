# Usage

## Getting started
Once DTCC Viewer, DTCC Model and DTCC IO have been successfully installed, getting started with DTCC Viewer is rather simple.  

To visualise a point cloud colored by the x-position of the points: 

```python
from dtcc_io import pointcloud
filename_pc = '../../../data/models/pointcloud.las'
pc = pointcloud.load(filename_pc)
color_data = pc.points[:,0]
pc.view(pc_data = color_data)
```

To visualise a mesh without data (default coloring schema will be vertex z-value):

```python
from dtcc_io import meshes
filename_mesh = '../../../data/models/mesh.obj'
mesh = meshes.load_mesh(filename_mesh)
mesh.view()
```

To visualise a point cloud and a mesh in the same window:

```python
from dtcc_io import meshes
from dtcc_io import pointcloud
filename_mesh = '../../../data/models/mesh.obj'
filename_pc = '../../../data/models/pointcloud.csv'
pc = pointcloud.load(filename_pc)
mesh = meshes.load_mesh(filename_mesh)
pc.view(mesh=mesh)
```

The same principle works the other way around, where the pointclode is added as an argument to the mesh viewing function call:

```python
from dtcc_io import meshes
from dtcc_io import pointcloud
filename_mesh = '../../../data/models/mesh.obj'
filename_pc = '../../../data/models/pointcloud.csv'
pc = pointcloud.load(filename_pc)
mesh = meshes.load_mesh(filename_mesh)
mesh.view(pc=pc)
```

## Viewer Controls

Once the DTCC Viewer is running and a graphics window is open, the following mouse and key commands are used to control the viewer:

Viewport navigation:
* Left mouse button - Rotate the view around the camera target
* Right mouse button - Panning the view, thus moving the camera target
* Scroll - Zoom in and out at the current camera target

Mesh viewing options:
* Q - Toggle visualisation of mesh **On** and **Off**
* W - Toggle color options between **Monochrome** and **Colored by data**
* E - Swich viewing mode between: **Wireframe**, **Diffuse Shaded**, **Fancy Shaded** (default), **Shadow Shaded**
* R - Toggle animation of light source position that cast shadows (only impacts "Fancy Shaded" and "Shadow Shaded" viewing mode)

Point cloud viewing options:
* A - Toggle visualisation of point cloud **On** and **Off**
* S - Toggle colors options between **Monochrome** and **Colored by data**
* D - Reduce particle size by 20%
* F - Increase particle size by 20%

That's it - happy hacking!
