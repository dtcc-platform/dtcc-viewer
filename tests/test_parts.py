import numpy as np

from dtcc_core.model import Mesh
from dtcc_viewer.opengl.parts import Parts


def test_parts_offset_ids_remaps_attributes_and_uuids():
    mesh_a = Mesh(
        vertices=np.array([(0, 0, 0), (1, 0, 0), (0, 1, 0)], dtype=float),
        faces=np.array([(0, 1, 2)], dtype=np.int64),
    )
    mesh_b = Mesh(
        vertices=np.array([(1, 0, 0), (2, 0, 0), (1, 1, 0)], dtype=float),
        faces=np.array([(0, 1, 2)], dtype=np.int64),
    )
    parts = Parts(
        [mesh_a, mesh_b],
        uuids=["a", "b"],
        attributes=[{"name": "A", "speed": 30}, {"name": "B", "speed": 50}],
    )

    parts.offset_ids(10)

    assert parts.ids.tolist() == [10, 11]
    assert parts.id_exists(10)
    assert parts.get_attributes(10) == {"name": "A", "speed": 30}
    assert parts.get_attributes(11) == {"name": "B", "speed": 50}
    assert parts.ids_2_uuids == {10: "a", 11: "b"}
    assert parts.get_numeric_attribute_keys() == ["speed"]
