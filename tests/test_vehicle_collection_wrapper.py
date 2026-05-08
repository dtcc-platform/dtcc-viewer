from dtcc_core.model import Object, Point, VehicleCollection
from dtcc_viewer.opengl.wrp_vehicle_collection import VehicleCollectionWrapper


def test_vehicle_collection_wrapper_creates_clickable_parts():
    collection = VehicleCollection()
    vehicle = Object()
    vehicle.attributes = {
        "vehicle_id": "bus-1",
        "mode": "bus",
        "line": "16",
        "provider": "test",
        "speed": 8.0,
    }
    vehicle.geometry["location"] = Point(x=1.0, y=2.0, z=0.0)
    collection.add_vehicle(vehicle)

    wrapper = VehicleCollectionWrapper("Vehicles", collection, mts=1024)

    assert wrapper.mesh_wrp is not None
    assert wrapper.mesh_wrp.parts.count == 1
    attrs = wrapper.mesh_wrp.parts.get_attributes(0)
    assert attrs["vehicle"] == "bus-1"
    assert attrs["mode"] == "bus"
    assert attrs["line"] == "16"
