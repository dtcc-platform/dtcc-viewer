import numpy as np
import glfw
from dtcc_viewer.opengl.utils import invert_color
from dtcc_viewer.opengl.utils import Shading, RasterType, CameraProjection, CameraView
from dtcc_viewer.logging import info, warning
from abc import ABC, abstractmethod


class GuiParametersGlobal:
    """Class representing global GUI parameters for the viewer.

    Attributes
    ----------
    color : list
        Background color.
    text_color : list
        Text color derived from the background color.
    gui_width : int
        Width of the GUI.
    gui_height : int
        Height of the GUI.
    single_date : bool
        Flag to indicate single date mode.
    period : bool
        Flag to indicate period mode.
    clip_bool : list
        Clipping boolean values.
    clip_dir : list
        Clipping directions.
    clip_dist : list
        Clipping distances.
    show_grid : bool
        Flag to show the grid.
    show_axes : bool
        Flag to show the axes.
    grid_sf : float
        Grid scale factor.
    grid_adapt : bool
        Flag to adapt grid.
    axes_sf : float
        Axes scale factor.
    time : float
        Current time.
    time_acum : float
        Accumulated time.
    fps_counter : int
        Frame per second counter.
    camera_projection : CameraProjection
        Camera projection type.
    camera_view : CameraView
        Camera view type.
    update_camera : bool
        Flag to update the camera.
    """

    color: list
    text_color: list
    gui_width: int
    gui_height: int
    single_date: bool
    period: bool
    clip_bool: list
    clip_dir: list
    clip_dist: list
    show_grid: bool
    show_axes: bool
    grid_sf: float
    grid_adapt: bool
    axes_sf: float
    time: float
    time_acum: float
    fps_counter: int
    camera_projection: CameraProjection
    camera_view: CameraView
    update_camera: bool

    def __init__(self):
        """Initialize the GuiParameters object."""
        self.color = [0.17, 0.25, 0.42, 1.0]  # [0.05, 0.1, 0.25, 1]
        self.text_color = invert_color(self.color)
        self.gui_width = 320
        self.gui_height = 200
        self.single_date = True
        self.period = False
        self.clip_bool = [True, True, True]
        self.clip_dir = [1, 1, 1]
        self.clip_dist = [1, 1, 1]  # x,y has range [-1, 1], z has range [0, 1]
        self.fps_counter = 0
        self.time = 0.0
        self.time_acum = 0.0
        self.fps_counter = 0
        self.fps = 0
        self.camera_projection = CameraProjection.PERSPECTIVE
        self.camera_view = CameraView.PERSPECTIVE
        self.update_camera = False
        self.show_grid = True
        self.show_axes = False
        self.grid_sf = 1.0
        self.axes_sf = 1.0
        self.grid_adapt = True

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
    """Class representing GUI parameters for the model.

    Attributes
    ----------
    name : str
        Name of the model.
    show : bool
        Flag to show the model.
    shading : Shading
        Shading type for the model.
    animate_light : bool
        Flag to animate light.
    picked_id : int
        ID of the picked element.
    picked_uuid : str
        UUID of the picked element.
    picked_mesh_face_count : int
        Face count of the picked mesh.
    picked_mesh_vertex_count : int
        Vertex count of the picked mesh.
    picked_attributes : str
        Attributes of the picked element.
    picked_cp : np.ndarray
        Picked control points.
    picked_size : float
        Size of the picked element.
    """

    name: str
    show: bool
    shading: Shading
    animate_light: bool
    picked_id: int
    picked_uuid: str
    picked_mesh_face_count: int
    picked_mesh_vertex_count: int
    picked_attributes: str
    picked_cp: np.ndarray
    picked_size: float

    def __init__(self, name: str, shading: Shading) -> None:
        """Initialize the GuiParametersModel object.

        Parameters
        ----------
        name : str
            Name of the model.
        shading : Shading
            Shading type for the model.
        """
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
    """Common parameters for object representation in the GUI.

    Attributes
    ----------
    name : str
        Name of the object.
    show : bool
        Flag to show the object.
    color : bool
        Flag to enable color.
    invert_cmap : bool
        Flag to invert the color map.
    update_caps : bool
        Flag to update capabilities.
    update_data_tex : bool
        Flag to update data texture.
    cmap_idx : int
        Color map index.
    data_idx : int
        Data index.
    data_min : float
        Minimum data value.
    data_max : float
        Maximum data value.
    data_keys : list
        List of data keys.
    dict_slider_caps : dict
        Dictionary of slider capabilities.
    dict_min_max : dict
        Dictionary of minimum and maximum values.
    dict_sldr_val : dict
        Dictionary of slider values.
    """

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
    dict_min_max: dict
    dict_sldr_val: dict

    def set_default_values(self, name: str, dict_mat_data: dict, dict_min_max: dict):
        """Set default values for the object.

        Parameters
        ----------
        name : str
            Name of the object.
        dict_mat_data : dict
            Dictionary of material data.
        dict_min_max : dict
            Dictionary of minimum and maximum values.
        """
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
        self.dict_slider_caps = dict.fromkeys(self.data_keys, [0.0, 1.0])  # [0,1]
        self.dict_min_max = dict_min_max  # [min, max]

        self.dict_sldr_val = {}
        for key, min_max in dict_min_max.items():
            self.dict_sldr_val[key] = [min_max[0], min_max[1]]

    def get_current_data_name(self):
        """Get the name of the current data.

        Returns
        -------
        str
            The name of the current data.
        """
        return self.data_keys[self.data_idx]

    def calc_min_max(self):
        """Calculate minimum and maximum values for the current data."""
        key = self.get_current_data_name()
        self.data_min = self.dict_sldr_val[key][0]
        self.data_max = self.dict_sldr_val[key][1]


class GuiParametersMesh(GuiParametersObj):
    """Class representing GUI parameters for meshes.

    Attributes
    ----------
    show_fnormals : bool
        Flag to show face normals.
    show_vnormals : bool
        Flag to show vertex normals.
    """

    show_fnormals: bool
    show_vnormals: bool

    def __init__(self, name: str, dict_mat_data: dict, dict_min_max: dict) -> None:
        """Initialize the GuiParametersMesh object.

        Parameters
        ----------
        name : str
            Name of the mesh.
        dict_mat_data : dict
            Dictionary of material data.
        dict_min_max : dict
            Dictionary of minimum and maximum values.
        """
        self.set_default_values(name, dict_mat_data, dict_min_max)
        self.calc_min_max()
        self.show_fnormals = False
        self.show_vnormals = False


class GuiParametersPC(GuiParametersObj):
    """Class representing GUI parameters for point clouds.

    Attributes
    ----------
    point_scale : float
        Scale factor for points.
    """

    def __init__(self, name: str, dict_mat_data: dict, dict_min_max: dict) -> None:
        """Initialize the GuiParametersPC object.

        Parameters
        ----------
        name : str
            Name of the point cloud.
        dict_mat_data : dict
            Dictionary of material data.
        dict_min_max : dict
            Dictionary of minimum and maximum values.
        """

        self.set_default_values(name, dict_mat_data, dict_min_max)
        self.calc_min_max()
        self.point_scale = 1.0


class GuiParametersLines(GuiParametersObj):
    """Class representing GUI parameters for road networks.

    Attributes
    ----------
    line_scale : float
        Scale factor for lines.
    """

    def __init__(self, name: str, dict_mat_data: dict, dict_min_max: dict) -> None:
        """Initialize the GuiParametersLines object.

        Parameters
        ----------
        name : str
            Name of the road network.
        dict_mat_data : dict
            Dictionary of material data.
        dict_min_max : dict
            Dictionary of minimum and maximum values.
        """
        self.set_default_values(name, dict_mat_data, dict_min_max)
        self.calc_min_max()
        self.line_scale = 1.0


class GuiParametersRaster:
    """Class representing GUI parameters for raster data.

    Attributes
    ----------
    name : str
        Name of the raster.
    show : bool
        Flag to show the raster.
    color : bool
        Flag to enable color.
    invert_cmap : bool
        Flag to invert the color map.
    update_caps : bool
        Flag to update capabilities.
    type : RasterType
        Type of raster.
    update_data_tex : bool
        Flag to update data texture.
    channels : list
        List of channels to draw.
    cmap_idx : int
        Color map index.
    """

    def __init__(self, name, type: RasterType) -> None:
        """Initialize the GuiParametersRaster object.

        Parameters
        ----------
        name : str
            Name of the raster.
        type : RasterType
            Type of raster.
        """
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
