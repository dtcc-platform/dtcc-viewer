import numpy as np
import pytest
from shapely.geometry import Polygon

from dtcc_core.model import GeometryType, MultiSurface, Object, Surface
from dtcc_viewer.opengl.wrp_deso import DeSOWrapper

try:
    from dtcc_core.model import DeSO
except ImportError:
    DeSO = None

pytestmark = pytest.mark.skipif(DeSO is None, reason="dtcc-core has no DeSO model")


def _area(code: str, origin_x: float) -> Object:
    polygon = Polygon(
        [
            (origin_x, 0),
            (origin_x + 1, 0),
            (origin_x + 1, 1),
            (origin_x, 1),
        ]
    )
    surface = Surface().from_polygon(polygon, 0.0)
    area = Object(id=code, attributes={"desokod": code, "population": 100})
    area.add_geometry(MultiSurface(surfaces=[surface]), GeometryType.LOD0)
    return area


def _deso() -> DeSO:
    deso = DeSO()
    deso.add_child(_area("1480C1000", 0.0))
    deso.add_child(_area("1480C2000", 2.0))
    return deso


def test_deso_wrapper_colors_areas_by_default():
    wrapper = DeSOWrapper("DeSO", _deso(), mts=1024)

    assert wrapper.mesh_wrp is not None
    assert wrapper.mesh_wrp.parts.count == 2
    assert wrapper.mesh_wrp.data_wrapper.get_keys()[0] == "DeSO color"
    assert wrapper.mesh_wrp.data_wrapper.data_min_max["DeSO color"] == (0.0, 1.0)

    texture_data = wrapper.mesh_wrp.data_wrapper.data_mat_dict["DeSO color"].flatten()
    texture_data = texture_data[: len(wrapper.mesh_wrp.faces)]
    assert len(np.unique(texture_data)) == 2


def test_deso_wrapper_makes_areas_pickable_with_attributes():
    wrapper = DeSOWrapper("DeSO", _deso(), mts=1024)

    first = wrapper.mesh_wrp.parts.get_attributes(0)
    second = wrapper.mesh_wrp.parts.get_attributes(1)

    assert first["desokod"] == "1480C1000"
    assert first["population"] == 100
    assert first["deso_area_index"] == 0
    assert second["desokod"] == "1480C2000"
    assert wrapper.mesh_wrp.parts.ids_2_uuids == {
        0: "1480C1000",
        1: "1480C2000",
    }
