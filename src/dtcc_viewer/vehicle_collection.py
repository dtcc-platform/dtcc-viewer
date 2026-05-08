from dtcc_core.model import PointCloud
from dtcc_viewer.opengl.window import Window
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.logging import warning, info


def view(vc, field_name=None, size=5.0, sphere_radius=None, screenshot=None):
    """View a VehicleCollection in 3D."""
    window_w, window_h = 1200, 800

    if screenshot:
        window = Window(window_w, window_h, visible=False)
    else:
        window = Window(window_w, window_h)

    scene = Scene()

    if sphere_radius == 0:
        points, values = vc.to_arrays(field_name)
        if len(points) == 0:
            warning("VehicleCollection has no vehicles with geometry. View aborted!")
            return
        pc = PointCloud(points=points)
        info(f"Viewing {len(points)} vehicles as point cloud.")
        scene.add_pointcloud("Vehicles", pc, size, data=values)
    else:
        radius = sphere_radius if sphere_radius is not None else 2.5
        info(f"Viewing vehicles as clickable spheres (r={radius}).")
        scene.add_vehicle_collection("Vehicles", vc, sphere_radius=radius)

    if screenshot:
        window.screenshot(scene, screenshot, window_w, window_h)
    else:
        window.render(scene)
