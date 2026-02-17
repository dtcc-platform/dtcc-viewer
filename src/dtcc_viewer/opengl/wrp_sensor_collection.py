import numpy as np
from shapely.geometry import Point

from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.utils import BoundingBox, create_sphere_mesh, concatenate_meshes
from dtcc_viewer.logging import info, warning


class SensorCollectionWrapper(Wrapper):
    """Wrapper for SensorCollection objects.

    Each station is rendered as a clickable 3D sphere. Clicking a station
    shows its attributes (name, location, field values) in the GUI sidebar.
    """

    name: str
    mesh_wrp: MeshWrapper | None

    def __init__(self, name, sensor_collection, mts, sphere_radius=2.0, sphere_segments=12):
        self.name = name
        self.mesh_wrp = None

        mesh, parts = self._generate_station_meshes(
            sensor_collection, sphere_radius, sphere_segments
        )
        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts, data=None, parts=parts)

    def _generate_station_meshes(self, sensor_collection, radius, segments):
        sphere_meshes = []
        uuids = []
        attributes_list = []

        for i, station in enumerate(sensor_collection.stations()):
            geom = self._get_point_geometry(station)
            if geom is None:
                continue

            center = Point(geom.x, geom.y, geom.z)
            sphere = create_sphere_mesh(center, radius, segments, segments)
            sphere_meshes.append(sphere)

            uuid = station.id or f"station_{i}"
            uuids.append(uuid)

            attrs = self._build_attributes(station, geom, i)
            attributes_list.append(attrs)

        if not sphere_meshes:
            warning(f"SensorCollection '{self.name}' has no stations with geometry")
            return None, None

        parts = Parts(sphere_meshes, uuids, attributes_list)
        combined = concatenate_meshes(sphere_meshes)

        info(f"SensorCollection '{self.name}': {len(sphere_meshes)} stations")
        return combined, parts

    def _get_point_geometry(self, station):
        for geom in station.geometry.values():
            if hasattr(geom, "x") and hasattr(geom, "y"):
                return geom
        return None

    def _build_attributes(self, station, geom, index):
        attrs = {
            "station_name": station.attributes.get("station_name", f"station_{index}"),
            "x": round(float(geom.x), 2),
            "y": round(float(geom.y), 2),
            "z": round(float(getattr(geom, "z", 0.0)), 2),
        }
        for field in getattr(geom, "fields", []):
            if len(field.values) > 0:
                attrs[field.name] = f"{field.values[0]:.2f} {field.unit}"
            else:
                attrs[field.name] = f"— {field.unit}"
        return attrs

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp is not None:
            self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        if self.mesh_wrp is not None:
            return self.mesh_wrp.get_vertex_positions()
        return np.array([])
