import numpy as np
from shapely.geometry import Point

from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.utils import BoundingBox, create_sphere_mesh, concatenate_meshes
from dtcc_viewer.logging import info, warning


class VehicleCollectionWrapper(Wrapper):
    """Wrapper for VehicleCollection objects.

    Each vehicle is rendered as a clickable 3D sphere. Clicking a vehicle shows
    its route, mode, provider, timestamp, speed, and bearing in the GUI sidebar.
    """

    name: str
    mesh_wrp: MeshWrapper | None

    def __init__(self, name, vehicle_collection, mts, sphere_radius=2.5, sphere_segments=12):
        self.name = name
        self.mesh_wrp = None

        mesh, parts = self._generate_vehicle_meshes(
            vehicle_collection, sphere_radius, sphere_segments
        )
        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts, data=None, parts=parts)

    def _generate_vehicle_meshes(self, vehicle_collection, radius, segments):
        sphere_meshes = []
        uuids = []
        attributes_list = []

        for i, vehicle in enumerate(vehicle_collection.vehicles()):
            geom = self._get_point_geometry(vehicle)
            if geom is None:
                continue

            center = Point(geom.x, geom.y, geom.z)
            sphere = create_sphere_mesh(center, radius, segments, segments)
            sphere_meshes.append(sphere)

            uuid = vehicle.id or f"vehicle_{i}"
            uuids.append(uuid)
            attributes_list.append(self._build_attributes(vehicle, geom, i))

        if not sphere_meshes:
            warning(f"VehicleCollection '{self.name}' has no vehicles with geometry")
            return None, None

        parts = Parts(sphere_meshes, uuids, attributes_list)
        combined = concatenate_meshes(sphere_meshes)

        info(f"VehicleCollection '{self.name}': {len(sphere_meshes)} vehicles")
        return combined, parts

    def _get_point_geometry(self, vehicle):
        for geom in vehicle.geometry.values():
            if hasattr(geom, "x") and hasattr(geom, "y"):
                return geom
        return None

    def _build_attributes(self, vehicle, geom, index):
        attrs = {
            "vehicle": vehicle.attributes.get("vehicle_id", f"vehicle_{index}"),
            "mode": vehicle.attributes.get("mode", "unknown"),
            "line": vehicle.attributes.get("line", ""),
            "provider": vehicle.attributes.get("provider", ""),
            "timestamp": vehicle.attributes.get("timestamp", ""),
            "x": round(float(geom.x), 2),
            "y": round(float(geom.y), 2),
            "z": round(float(getattr(geom, "z", 0.0)), 2),
        }
        for key in ("route_id", "trip_id", "destination", "speed", "bearing"):
            if key in vehicle.attributes:
                attrs[key] = vehicle.attributes[key]
        return attrs

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp is not None:
            self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        if self.mesh_wrp is not None:
            return self.mesh_wrp.get_vertex_positions()
        return np.array([])
