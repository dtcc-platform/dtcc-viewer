import numpy as np
from dtcc_core.model import PointCloud
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.logging import warning, info


def view(sc, field_name=None, size=5.0, sphere_radius=None, screenshot=None):
    """View a SensorCollection in 3D.

    By default, renders stations as clickable spheres (clicking shows station
    attributes in the sidebar). Falls back to a plain PointCloud when
    ``sphere_radius`` is explicitly set to 0.

    Parameters
    ----------
    sc : SensorCollection
        Sensor collection to be viewed (self).
    field_name : str, optional
        Name of the field to color by (e.g. "air_temperature", "NO2").
        If None, uses the first available field. Only used in PointCloud mode.
    size : float
        Point size in meters (PointCloud mode only). Default 5.0.
    sphere_radius : float, optional
        Radius of the clickable station spheres. Default 2.0.
        Set to 0 to fall back to plain PointCloud rendering.
    screenshot : str, optional
        If provided, saves an offscreen PNG to this path instead of
        opening an interactive window.
    """
    window_w, window_h = 1200, 800

    if screenshot:
        window = Window(window_w, window_h, visible=False)
    else:
        window = Window(window_w, window_h)

    scene = Scene()

    if sphere_radius == 0:
        # PointCloud fallback (no click metadata)
        points, values = sc.to_arrays(field_name)
        if len(points) == 0:
            warning("SensorCollection has no stations with geometry/data. View aborted!")
            return
        pc = PointCloud(points=points)
        info(f"Viewing {len(points)} sensor stations as point cloud.")
        scene.add_pointcloud("Sensors", pc, size, data=values)
    else:
        radius = sphere_radius if sphere_radius is not None else 2.0
        info(f"Viewing sensor stations as clickable spheres (r={radius}).")
        scene.add_sensor_collection("Sensors", sc, sphere_radius=radius)

    if screenshot:
        window.screenshot(scene, screenshot, window_w, window_h)
    else:
        window.render(scene)
