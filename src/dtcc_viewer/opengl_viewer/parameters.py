import numpy as np
from dtcc_viewer.opengl_viewer.utils import invert_color
from dtcc_viewer.opengl_viewer.utils import Shading
from dtcc_viewer.opengl_viewer.utils import shader_cmaps


class GuiParameters:
    """Class representing GUI parameters for the viewer."""

    def __init__(self):
        """Initialize the GuiParameters object."""
        self.color = [0.1, 0.2, 0.5, 1]
        self.text_color = invert_color(self.color)
        self.gui_width = 320
        self.gui_height = 200
        self.single_date = True
        self.period = False

        self.clip_bool = [False, False, False]
        self.clip_dir = [1, 1, 1]
        self.clip_dist = [1, 1, 1]  # each variable has range [-1, 1]


class GuiParametersObj:
    cmap_idx: int
    cmap_key: str

    data_idx: int
    data_min: float
    data_max: float
    data_keys: list
    dict_slider_caps: dict
    dict_value_caps: dict

    def __init__(self) -> None:
        pass


class GuiParametersMesh:
    """Class representing GUI parameters for meshes."""

    def __init__(self, name: str, shading: Shading, dict_data: dict) -> None:
        """Initialize the GuiParametersMesh object."""
        self.name = name
        self.show = True
        self.invert_cmap = False
        self.color_mesh = True
        self.animate_light = False
        self.lower_cap = 0.0
        self.upper_cap = 1.0
        self.update_caps = False

        self.cmap_idx = 0
        self.cmap_key = list(shader_cmaps.keys())[0]

        self.data_idx = 0
        self.data_min = 0  # Min value for color clamp
        self.data_max = 0  # Max value for color clamp
        self.data_keys = list(dict_data.keys())
        self.dict_slider_caps = dict.fromkeys(self.data_keys, [0.0, 1.0])
        self.dict_value_caps = dict.fromkeys(self.data_keys, [])
        self.dict_has_data = dict.fromkeys(self.data_keys, False)
        self.set_dict_has_data(dict_data)
        self.calc_dict_value_caps(dict_data)
        self.calc_data_min_max()

    def get_current_data_name(self):
        return self.data_keys[self.data_idx]

    def set_dict_has_data(self, dict_data: dict):
        for key in dict_data.keys():
            if dict_data[key] is not None:
                self.dict_has_data[key] = True

    def calc_dict_value_caps(self, dict_data: dict):
        for key in dict_data.keys():
            if dict_data[key] is not None:
                min = np.min(dict_data[key])
                max = np.max(dict_data[key])
                self.dict_value_caps[key] = [min, max]
            else:
                self.dict_value_caps[key] = None

    def set_dict_value_caps(self, key: str, min: float, max: float):
        if key in self.dict_value_caps:
            self.dict_value_caps[key] = [min, max]

    def calc_data_min_max(self):
        key = self.get_current_data_name()
        min = self.dict_value_caps[key][0]
        max = self.dict_value_caps[key][1]
        dom = max - min

        lower_cap = self.dict_slider_caps[key][0]
        upper_cap = self.dict_slider_caps[key][1]
        self.data_min = min + dom * lower_cap
        self.data_max = min + dom * upper_cap


class GuiParametersModel:
    name: str
    show: bool
    shading: Shading
    animate_light: bool

    def __init__(self, name: str, shading: Shading) -> None:
        self.name = name
        self.show = True
        self.shading = shading
        self.animate_light = False


class GuiParametersPC:
    """Class representing GUI parameters for point clouds."""

    def __init__(self, name: str, dict_data: dict) -> None:
        """Initialize the GuiParametersPC object."""
        self.name = name
        self.show = True
        self.color_pc = True
        self.invert_cmap = False
        self.pc_scale = 1.0
        self.update_caps = False

        self.cmap_index = 0
        self.cmap_key = list(shader_cmaps.keys())[0]

        self.data_index = 0
        self.data_min = 0  # Min value for color clamp
        self.data_max = 0  # Max value for color clamp
        self.data_keys = list(dict_data.keys())
        self.dict_slider_caps = dict.fromkeys(self.data_keys, [0.0, 1.0])
        self.dict_value_caps = dict.fromkeys(self.data_keys, [])
        self.calc_dict_value_caps(dict_data)
        self.calc_data_min_max()

    def get_current_data_name(self):
        """Get the current color name."""
        return self.data_keys[self.data_index]

    def calc_dict_value_caps(self, dict_data: dict):
        for key in dict_data.keys():
            if dict_data[key] is not None:
                min = np.min(dict_data[key])
                max = np.max(dict_data[key])
                self.dict_value_caps[key] = [min, max]
            else:
                self.dict_value_caps[key] = None

    def calc_data_min_max(self):
        key = self.get_current_data_name()
        min = self.dict_value_caps[key][0]
        max = self.dict_value_caps[key][1]
        dom = max - min

        lower_cap = self.dict_slider_caps[key][0]
        upper_cap = self.dict_slider_caps[key][1]
        self.data_min = min + dom * lower_cap
        self.data_max = min + dom * upper_cap


class GuiParametersLS:
    """Class representing GUI parameters for road networks."""

    def __init__(self, name: str, dict_data: dict) -> None:
        """Initialize the GuiParametersRN object."""
        self.name = name
        self.show = True
        self.color = True
        self.scale = 1.0

        self.invert_cmap = False
        self.update_caps = False

        self.cmap_idx = 0
        self.cmap_key = list(shader_cmaps.keys())[0]

        self.data_idx = 0
        self.data_min = 0  # Min value for color clamp
        self.data_max = 0  # Max value for color clamp
        self.data_keys = list(dict_data.keys())
        self.dict_slider_caps = dict.fromkeys(self.data_keys, [0.0, 1.0])
        self.dict_value_caps = dict.fromkeys(self.data_keys, [])
        self.calc_dict_value_caps(dict_data)
        self.calc_data_min_max()

    def get_current_data_name(self):
        """Get the current color name."""
        return self.data_keys[self.data_idx]

    def calc_dict_value_caps(self, dict_data: dict):
        for key in dict_data.keys():
            if dict_data[key] is not None:
                min = np.min(dict_data[key])
                max = np.max(dict_data[key])
                self.dict_value_caps[key] = [min, max]
            else:
                self.dict_value_caps[key] = None

    def calc_data_min_max(self):
        key = self.get_current_data_name()
        min = self.dict_value_caps[key][0]
        max = self.dict_value_caps[key][1]
        dom = max - min

        lower_cap = self.dict_slider_caps[key][0]
        upper_cap = self.dict_slider_caps[key][1]
        self.data_min = min + dom * lower_cap
        self.data_max = min + dom * upper_cap


class GuiParametersDates:
    """Class representing an example of GUI parameters."""

    def __init__(self) -> None:
        """Initialize the GuiParametersExample object."""
        self.year_start = 2023
        self.month_start = 3
        self.day_start = 3
        self.hour_start = 15

        self.year_end = 2023
        self.month_end = 3
        self.day_end = 4
        self.hour_end = 15

        self.color = [0.1, 0.2, 0.5, 1]
        self.text_color = invert_color(self.color)
        self.gui_width = 310
        self.gui_height = 200
        self.single_date = True
        self.period = False

        self.checkbox1 = False
        self.checkbox2 = False

        self.combo_selected_index = 2

    def match(self) -> None:
        """Set the end date to match the start date."""
        self.year_end = self.year_start
        self.month_end = self.month_start
        self.day_end = self.day_start
        self.hour_end = self.hour_start
