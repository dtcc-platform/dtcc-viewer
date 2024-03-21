import numpy as np
import glfw
from dtcc_viewer.opengl.utils import invert_color
from dtcc_viewer.opengl.utils import Shading, RasterType
from dtcc_viewer.opengl.utils import ColorMaps
from dtcc_viewer.logging import info, warning
from abc import ABC, abstractmethod


class GuiParametersGlobal:
    """Class representing GUI parameters for the viewer."""

    color: list
    text_color: list
    gui_width: int
    gui_height: int
    single_date: bool
    period: bool
    clip_bool: list
    clip_dir: list
    clip_dist: list

    time: float
    time_acum: float
    fps_counter: int

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
        self.fps_counter = 0
        self.time = 0.0
        self.time_acum = 0.0
        self.fps_counter = 0
        self.fps = 0

    def calc_fps(self):
        """Perform FPS calculations for the rendering loop."""

        new_time = glfw.get_time()
        time_passed = new_time - self.time
        self.time = new_time
        self.time_acum += time_passed
        self.fps_counter += 1

        if self.time_acum > 1:
            self.time_acum = 0
            self.fps = self.fps_counter
            self.fps_counter = 0


class GuiParametersModel:
    name: str
    show: bool
    shading: Shading
    animate_light: bool
    picked_id: int
    picked_uuid: str
    picked_metadata: str
    picked_cp: np.ndarray
    picked_size: float

    def __init__(self, name: str, shading: Shading) -> None:
        self.name = name
        self.show = True
        self.shading = shading
        self.animate_light = False
        self.picked_id = -1
        self.picked_uuid = ""
        self.picked_metadata = ""
        self.picked_cp = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.picked_size = 0.0


class GuiParametersObj(ABC):
    """Common parameters for object representation in the GUI."""

    name: str
    show: bool
    color: bool
    invert_cmap: bool
    update_caps: bool
    update_data_tex: bool
    cmap_idx: int
    data_idx: int
    data_min: float
    data_max: float
    data_keys: list
    dict_slider_caps: dict
    dict_value_caps: dict

    def set_default_values(self, name: str, dict_mat_data: dict, dict_val_caps: dict):
        self.name = name
        self.show = True
        self.color = True
        self.invert_cmap = False
        self.update_caps = False
        self.update_data_tex = False
        self.cmap_idx = 0
        self.data_idx = 0
        self.data_min = 0  # Min value for color clamp
        self.data_max = 0  # Max value for color clamp
        self.data_keys = list(dict_mat_data.keys())
        self.dict_slider_caps = dict.fromkeys(self.data_keys, [0.0, 1.0])
        self.dict_value_caps = dict_val_caps

    def get_current_data_name(self):
        return self.data_keys[self.data_idx]

    def calc_min_max(self):
        key = self.get_current_data_name()
        min = self.dict_value_caps[key][0]
        max = self.dict_value_caps[key][1]
        dom = max - min

        lower_cap = self.dict_slider_caps[key][0]
        upper_cap = self.dict_slider_caps[key][1]
        self.data_min = min + dom * lower_cap
        self.data_max = min + dom * upper_cap


class GuiParametersMesh(GuiParametersObj):
    """Class representing GUI parameters for meshes."""

    def __init__(self, name: str, dict_mat_data: dict, dict_val_caps: dict) -> None:
        self.set_default_values(name, dict_mat_data, dict_val_caps)
        self.calc_min_max()


class GuiParametersPC(GuiParametersObj):
    """Class representing GUI parameters for point clouds."""

    def __init__(self, name: str, dict_mat_data: dict, dict_val_caps: dict) -> None:
        """Initialize the GuiParametersPC object."""
        self.set_default_values(name, dict_mat_data, dict_val_caps)
        self.calc_min_max()
        self.point_scale = 1.0


class GuiParametersLS(GuiParametersObj):
    """Class representing GUI parameters for road networks."""

    def __init__(self, name: str, dict_mat_data: dict, dict_val_caps: dict) -> None:
        self.set_default_values(name, dict_mat_data, dict_val_caps)
        self.calc_min_max()
        self.line_scale = 1.0


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


class GuiParametersRaster:
    def __init__(self, name, type: RasterType) -> None:
        self.name = name
        self.show = True
        self.color = True
        self.invert_cmap = False
        self.update_caps = False
        self.type = type
        self.update_data_tex = False

        # 1 = draw, 0 = do not draw
        self.channels = [1, 1, 1, 1]
        self.cmap_idx = 0

    def calc_data_min_max(self):
        pass
