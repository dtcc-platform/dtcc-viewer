from dtcc_viewer.opengl.gl_model import GlModel
from dtcc_viewer.opengl.parameters import GuiParametersModel
from dtcc_viewer.opengl.utils import Shading


def test_picked_attributes_are_initialized_and_cleared():
    guip = GuiParametersModel("Model", Shading.WIRESHADED)
    assert guip.picked_attributes is None

    model = object.__new__(GlModel)
    model.gl_objects = []
    model.guip = guip
    model.guip.picked_attributes = {"name": "old"}

    model._find_object_from_id(42)

    assert model.guip.picked_attributes is None
