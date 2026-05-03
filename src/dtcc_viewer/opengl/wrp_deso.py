import numpy as np

from dtcc_core.model import GeometryType, Mesh, MultiSurface, Object

try:
    from dtcc_core.model import DeSO
except ImportError:  # pragma: no cover - compatibility with older dtcc-core
    DeSO = None

from dtcc_viewer.logging import warning
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.utils import BoundingBox, concatenate_meshes
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper


class DeSOWrapper(Wrapper):
    """DeSO wrapper for rendering statistical areas as pickable polygons."""

    name: str
    bb_global: BoundingBox = None
    mesh_wrp: MeshWrapper = None

    def __init__(self, name: str, deso: DeSO, mts: int) -> None:
        self.name = name
        self.mesh_wrp = None

        mesh, parts, area_color = self._to_area_mesh(deso)
        if mesh is not None:
            data = {"DeSO color": area_color}
            self.mesh_wrp = MeshWrapper(name, mesh, mts, data=data, parts=parts)
            self._prioritize_area_color(self.mesh_wrp)

    def preprocess_drawing(self, bb_global: BoundingBox):
        if self.mesh_wrp is not None:
            self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        if self.mesh_wrp is not None:
            return self.mesh_wrp.get_vertex_positions()
        return np.array([])

    def _to_area_mesh(
        self, deso: DeSO
    ) -> tuple[Mesh | None, Parts | None, np.ndarray]:
        area_meshes: list[Mesh] = []
        area_attributes: list[dict] = []
        area_uuids: list[str] = []
        area_values: list[float] = []

        area_colors = self._area_color_values(deso.areas)

        for index, area in enumerate(deso.areas):
            geometry = area.geometry.get(GeometryType.LOD0)
            if not isinstance(geometry, MultiSurface) or len(geometry.surfaces) == 0:
                continue

            mesh = self._mesh_multisurface(geometry)
            if mesh is None or len(mesh.faces) == 0:
                continue

            code = area.attributes.get("desokod", area.id)
            area_meshes.append(mesh)
            area_uuids.append(str(code))
            area_attributes.append(self._area_attributes(area, index))
            area_values.append(area_colors.get(str(code), 0.62))

        if not area_meshes:
            return None, None, np.array([])

        mesh = concatenate_meshes(area_meshes)
        parts = Parts(area_meshes, area_uuids, area_attributes)
        face_data = self._part_values_to_face_data(area_values, parts)
        return mesh, parts, face_data

    def _mesh_multisurface(self, multisurface: MultiSurface) -> Mesh | None:
        try:
            return multisurface.mesh()
        except Exception as exc:
            warning(f"Unable to mesh DeSO area for viewing: {exc}")
            return None

    def _area_attributes(self, area: Object, index: int) -> dict:
        attributes = dict(area.attributes)
        attributes.setdefault("deso_area_index", index)
        attributes.setdefault("id", area.id)
        return attributes

    def _area_color_values(self, areas: list[Object]) -> dict[str, float]:
        codes = sorted(
            {
                str(area.attributes.get("desokod", area.id))
                for area in areas
            }
        )
        golden_ratio_conjugate = 0.6180339887498949
        return {
            code: 0.1 + 0.8 * (((index + 1) * golden_ratio_conjugate) % 1.0)
            for index, code in enumerate(codes)
        }

    def _part_values_to_face_data(
        self, values: list[float], parts: Parts
    ) -> np.ndarray:
        face_data = []
        for value, face_count in zip(values, parts.face_count_per_part):
            face_data.extend(np.repeat(value, face_count))
        return np.asarray(face_data, dtype=float)

    def _prioritize_area_color(self, mesh_wrp: MeshWrapper):
        key = "DeSO color"
        data_wrapper = mesh_wrp.data_wrapper
        if key not in data_wrapper.data_mat_dict:
            return

        color_data = data_wrapper.data_mat_dict.pop(key)
        data_wrapper.data_mat_dict = {
            key: color_data,
            **data_wrapper.data_mat_dict,
        }
        data_wrapper.data_min_max[key] = (0.0, 1.0)
