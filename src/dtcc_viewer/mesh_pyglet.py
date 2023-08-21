import pyglet
import trimesh
import numpy as np
from typing import List, Any, Iterable

# import dtcc_model as model
from dtcc_viewer.colors import color_maps
from pprint import pp


class Viewer:
    """
    Viewer is a simple tool for visualising mesh geometry.

    User instructions:

    Press W to toggle between wireframe mode and shaded mode.

    """

    scene: trimesh.Scene

    def __init__(self):
        """
        Initialising a trimesh scene which wrapps the pyglet viewer
        in a conveniant way.
        """
        self.scene = trimesh.Scene()
        self.scene.camera._fov = [35, 35]  # Field of view [x, y]
        self.scene.camera.z_far = 10000  # Distance to the far clipping plane

    def recalibrate_camera(self):
        """
        Setting the camera "look_at" to include all the geometry in
        the scene. This is achieved by finding the corners for each
        geometry bounding box and calling the look_at function
        with the list of corner points as an argument.
        """
        bb_corners = []
        for key in self.scene.geometry:
            obj = self.scene.geometry[key]
            bb = trimesh.bounds.corners(obj.bounding_box.bounds)
            for pt in bb:
                bb_corners.append(pt)

        self.scene.camera_transform = self.scene.camera.look_at(bb_corners)

    def add_meshes(self, meshes):
        """
        Adding geometry to the scene and recalibrating the camera
        so that all the new geometry is visible.
        """
        self.scene.add_geometry(meshes)
        self.recalibrate_camera()

    def show(self):
        """
        Opening the window and showing the geometry which has been
        added to the scene.
        """
        self.scene.show()

    def add_light(self):
        pass


def view(
    viewer: Viewer,
    mesh: trimesh,
    values: Iterable[float] = None,
    color_map_key: str = "arctic",
    min_val=None,
    max_val=None,
):
    color_map_function = color_maps[color_map_key]

    if values is None:
        values = np.ones(len(mesh.faces))
        colors = color_map_function(values, min_val, max_val)
    else:
        colors = color_map_function(values, min_val, max_val)

    if len(mesh.faces) == len(colors):
        mesh.visual.face_colors = colors
    elif len(mesh.vertices) == len(colors):
        mesh.visual.vertice_colors = colors

    viewer.add_meshes(mesh)

    return True
