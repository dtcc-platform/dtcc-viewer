import numpy as np
from dtcc_core.model import Mesh
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.data_wrapper import LinesDataWrapper
from dtcc_viewer.opengl.wrp_linestring import MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.parts import Parts
from dtcc_core.model import LineString, MultiLineString, RoadNetwork
from typing import Any


class RoadNetworkWrapper(Wrapper):
    """Road network wrapper for rendering and picking in an OpenGL window."""

    vertices: np.ndarray
    indices: np.ndarray
    name: str
    bb_local: BoundingBox
    bb_global: BoundingBox = None
    data_wrapper: LinesDataWrapper = None

    def __init__(
        self,
        name: str,
        roadnetwork: RoadNetwork,
        mts: int,
        data: Any = None,  # Dict, np.ndarray
        road_width: float = 6.0,
        z_offset: float = 0.05,
    ) -> None:
        """Initialize the RoadNetworkWrapper object.

        Parameters
        ----------
        name : str
            The name of the mesh wrapper.
        roadnetwork : RoadNetwork
            RoadNetwork object for visualisation.
        mts: int
            Max texture size for the data.
        data : Any, optional
            Additional mesh data (dict or array) for color calculation (default is None).
        road_width : float, default 6.0
            Rendered road ribbon width in model units.
        z_offset : float, default 0.05
            Small vertical offset for road ribbons to avoid z-fighting.
        """
        self.name = name
        self.data_wrapper = None
        mls = self._as_multilinestring(roadnetwork)
        self.mls_wrp = MultiLineStringWrapper(name, mls, mts, data)
        self.mesh_wrp = None

        mesh, parts = self._to_road_surface_mesh(
            roadnetwork, mls, road_width=road_width, z_offset=z_offset
        )
        if mesh is not None:
            face_data = {
                "Road color": np.full(len(mesh.faces), 0.62, dtype=float),
            }
            self.mesh_wrp = MeshWrapper(name, mesh, mts, data=face_data, parts=parts)
            self._prioritize_default_road_color(self.mesh_wrp)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp is not None:
            self.mesh_wrp.preprocess_drawing(bb_global)
        if self.mls_wrp is not None:
            self.mls_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        if self.mesh_wrp is not None:
            return self.mesh_wrp.get_vertex_positions()
        if self.mls_wrp is not None:
            return self.mls_wrp.get_vertex_positions()
        return None

    def _to_road_surface_mesh(
        self,
        roadnetwork: RoadNetwork,
        mls: MultiLineString,
        road_width: float,
        z_offset: float,
    ) -> tuple[Mesh | None, Parts | None]:
        if mls is None or len(mls.linestrings) == 0 or road_width <= 0:
            return None, None

        part_meshes = []
        part_attributes = []
        uuids = []
        half_width = road_width / 2.0
        segment_count = len(mls.linestrings)

        for index, line in enumerate(mls.linestrings):
            mesh = self._line_to_road_surface(line, half_width, z_offset)
            if mesh is None:
                continue
            part_meshes.append(mesh)
            uuids.append(self._road_uuid(roadnetwork, index, segment_count))
            part_attributes.append(
                self._road_attributes(roadnetwork, line, index, segment_count)
            )

        if not part_meshes:
            return None, None

        mesh = self._concatenate_meshes(part_meshes)
        parts = Parts(part_meshes, uuids, part_attributes)
        return mesh, parts

    def _line_to_road_surface(
        self, line: LineString, half_width: float, z_offset: float
    ) -> Mesh | None:
        points = self._zero_z_vertices(line.vertices)
        if len(points) < 2:
            return None

        vertices = []
        faces = []
        for start, end in zip(points[:-1], points[1:]):
            direction = end[:2] - start[:2]
            length = np.linalg.norm(direction)
            if length == 0:
                continue

            normal = np.array([-direction[1], direction[0]], dtype=float) / length
            offset = normal * half_width
            base = len(vertices)
            vertices.extend(
                [
                    [start[0] + offset[0], start[1] + offset[1], z_offset],
                    [start[0] - offset[0], start[1] - offset[1], z_offset],
                    [end[0] + offset[0], end[1] + offset[1], z_offset],
                    [end[0] - offset[0], end[1] - offset[1], z_offset],
                ]
            )
            faces.extend([[base, base + 1, base + 2], [base + 1, base + 3, base + 2]])

        if not faces:
            return None

        return Mesh(
            vertices=np.asarray(vertices, dtype=float),
            faces=np.asarray(faces, dtype=np.int64),
        )

    def _road_attributes(
        self,
        roadnetwork: RoadNetwork,
        line: LineString,
        index: int,
        segment_count: int,
    ) -> dict:
        attrs = {
            "road_segment_index": index,
            "length": float(line.length),
        }

        if len(roadnetwork.length) == segment_count:
            attrs["length"] = self._to_python_scalar(roadnetwork.length[index])

        edges = np.asarray(roadnetwork.edges)
        if edges.ndim == 2 and len(edges) == segment_count:
            attrs["start_vertex"] = int(edges[index, 0])
            attrs["end_vertex"] = int(edges[index, 1])

        for key, values in roadnetwork.attributes.items():
            value = self._attribute_at(values, index, segment_count)
            if value is not None:
                attrs[key] = value

        return attrs

    def _attribute_at(self, values: Any, index: int, segment_count: int):
        try:
            if len(values) != segment_count:
                return None
        except TypeError:
            return None

        return self._to_python_scalar(values[index])

    @staticmethod
    def _to_python_scalar(value: Any):
        if hasattr(value, "item"):
            return value.item()
        return value

    def _road_uuid(
        self, roadnetwork: RoadNetwork, index: int, segment_count: int
    ) -> str:
        way_id = self._attribute_at(
            roadnetwork.attributes.get("osm_way_id", []),
            index,
            segment_count,
        )
        segment_index = self._attribute_at(
            roadnetwork.attributes.get("segment_index", []),
            index,
            segment_count,
        )
        if way_id is not None and segment_index is not None:
            return f"osm_way_{way_id}_segment_{segment_index}"
        return f"road_segment_{index}"

    def _concatenate_meshes(self, meshes: list[Mesh]) -> Mesh:
        vertex_count = sum(len(mesh.vertices) for mesh in meshes)
        face_count = sum(len(mesh.faces) for mesh in meshes)
        vertices = np.zeros((vertex_count, 3), dtype=float)
        faces = np.zeros((face_count, 3), dtype=np.int64)

        vertex_offset = 0
        face_offset = 0
        for mesh in meshes:
            v_count = len(mesh.vertices)
            f_count = len(mesh.faces)
            vertices[vertex_offset : vertex_offset + v_count] = mesh.vertices
            faces[face_offset : face_offset + f_count] = mesh.faces + vertex_offset
            vertex_offset += v_count
            face_offset += f_count

        return Mesh(vertices=vertices, faces=faces)

    def _prioritize_default_road_color(self, mesh_wrp: MeshWrapper):
        key = "Road color"
        data_wrapper = mesh_wrp.data_wrapper
        if key not in data_wrapper.data_mat_dict:
            return

        color_data = data_wrapper.data_mat_dict.pop(key)
        data_wrapper.data_mat_dict = {
            key: color_data,
            **data_wrapper.data_mat_dict,
        }
        data_wrapper.data_min_max[key] = (0.0, 1.0)

    def _as_multilinestring(self, roadnetwork: RoadNetwork) -> MultiLineString:
        mls = roadnetwork.multilinestrings
        if mls is not None and len(mls.linestrings) > 0:
            return self._copy_multilinestring_zero_z(mls)
        return self._graph_to_multilinestring(roadnetwork)

    def _copy_multilinestring_zero_z(self, mls: MultiLineString) -> MultiLineString:
        copied = MultiLineString()
        for source_line in mls.linestrings:
            vertices = self._zero_z_vertices(source_line.vertices)
            if len(vertices) < 2:
                continue
            line = LineString()
            line.vertices = vertices
            copied.linestrings.append(line)
        return copied

    def _graph_to_multilinestring(self, roadnetwork: RoadNetwork) -> MultiLineString:
        mls = MultiLineString()
        vertices = np.asarray(roadnetwork.vertices)
        edges = np.asarray(roadnetwork.edges, dtype=np.int64)
        if vertices.ndim != 2 or vertices.shape[1] < 2 or edges.size == 0:
            return mls

        for start, end in edges.reshape((-1, 2)):
            if start >= len(vertices) or end >= len(vertices):
                continue
            line = LineString()
            line.vertices = self._zero_z_vertices(vertices[[start, end]])
            mls.linestrings.append(line)
        return mls

    @staticmethod
    def _zero_z_vertices(vertices: np.ndarray) -> np.ndarray:
        vertices = np.asarray(vertices, dtype=float)
        if vertices.ndim != 2 or vertices.shape[1] < 2:
            return np.empty((0, 3), dtype=float)
        if vertices.shape[1] == 2:
            z = np.zeros((len(vertices), 1), dtype=float)
            return np.hstack((vertices[:, :2].copy(), z))
        result = vertices[:, :3].copy()
        result[:, 2] = 0.0
        return result
