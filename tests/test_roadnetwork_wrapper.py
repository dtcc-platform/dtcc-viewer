import numpy as np
import pytest

from dtcc_core.model import GeometryType, LineString, MultiLineString, RoadNetwork
from dtcc_viewer.opengl.wrp_roadnetwork import RoadNetworkWrapper


def test_roadnetwork_wrapper_uses_graph_when_geometry_missing():
    roadnetwork = RoadNetwork()
    roadnetwork.vertices = np.array([(0, 0), (1, 0), (1, 1)], dtype=float)
    roadnetwork.edges = np.array([(0, 1), (1, 2)], dtype=np.int64)
    roadnetwork.length = np.array([1.0, 1.0])
    roadnetwork.attributes = {
        "highway": ["residential", "primary"],
        "maxspeed_kmh": [30.0, 50.0],
    }

    wrapper = RoadNetworkWrapper("Roads", roadnetwork, mts=1024, road_width=0.2)
    positions = wrapper.get_vertex_positions().reshape((-1, 3))

    assert wrapper.mesh_wrp is not None
    assert wrapper.mesh_wrp.parts.count == 2
    assert wrapper.mesh_wrp.data_wrapper.get_keys()[0] == "Road color"
    assert wrapper.mesh_wrp.data_wrapper.data_min_max["Road color"] == (0.0, 1.0)
    assert positions.shape == (12, 3)
    assert np.allclose(positions[:, 2], 0.05)
    assert len(wrapper.mls_wrp.indices) == 4

    attrs = wrapper.mesh_wrp.parts.get_attributes(0)
    assert attrs["road_segment_index"] == 0
    assert attrs["start_vertex"] == 0
    assert attrs["end_vertex"] == 1
    assert attrs["length"] == 1.0
    assert attrs["highway"] == "residential"
    assert attrs["maxspeed_kmh"] == 30.0


def test_roadnetwork_wrapper_does_not_mutate_geometry_z():
    roadnetwork = RoadNetwork()
    roadnetwork.vertices = np.array([(0, 0, 5), (1, 0, 8)], dtype=float)
    roadnetwork.edges = np.array([(0, 1)], dtype=np.int64)

    line = LineString()
    line.vertices = np.array([(0, 0, 5), (1, 0, 8)], dtype=float)
    multilinestring = MultiLineString()
    multilinestring.linestrings.append(line)
    roadnetwork.geometry[GeometryType.MULTILINESTRING] = multilinestring

    wrapper = RoadNetworkWrapper("Roads", roadnetwork, mts=1024, road_width=0.2)
    positions = wrapper.get_vertex_positions().reshape((-1, 3))

    assert np.allclose(line.vertices[:, 2], [5, 8])
    assert np.allclose(positions[:, 2], 0.05)


def test_roadnetwork_wrapper_road_width_controls_surface_width():
    roadnetwork = RoadNetwork()
    roadnetwork.vertices = np.array([(0, 0), (1, 0)], dtype=float)
    roadnetwork.edges = np.array([(0, 1)], dtype=np.int64)

    wrapper = RoadNetworkWrapper("Roads", roadnetwork, mts=1024, road_width=0.4)
    positions = wrapper.get_vertex_positions().reshape((-1, 3))

    assert np.max(positions[:, 1]) - np.min(positions[:, 1]) == pytest.approx(0.4)
