import imgui
import copy
from dtcc_viewer.opengl_viewer.utils import MeshShading
from imgui.integrations.glfw import GlfwRenderer


class GuiParameters:
    """Class representing GUI parameters for the viewer.

    Attributes
    ----------
    color : list of float
        The color used for GUI elements.
    text_color : list of float
        The inverted color for text elements.
    gui_width : int
        The width of the GUI window.
    gui_height : int
        The height of the GUI window.
    single_date : bool
        Flag indicating whether a single date is selected.
    period : bool
        Flag indicating whether a date period is selected.
    """

    def __init__(self):
        """Initialize the GuiParameters object."""
        self.color = [0.1, 0.2, 0.5, 1]
        self.text_color = Gui.invert_color(self.color)
        self.gui_width = 320
        self.gui_height = 200
        self.single_date = True
        self.period = False

        self.clip_bool = [False, False, False]
        self.clip_dir = [1, 1, 1]
        self.clip_dist = [1, 1, 1]  # each variable has range [-1, 1]


class GuiParametersMesh:
    """Class representing GUI parameters for meshes."""

    def __init__(self, name: str, shading: MeshShading) -> None:
        """Initialize the GuiParametersMesh object."""
        self.name = name
        self.show = True
        self.color_mesh = True
        self.animate_light = False
        self.mesh_shading = shading


class GuiParametersPC:
    """Class representing GUI parameters for point clouds."""

    def __init__(self, name: str) -> None:
        """Initialize the GuiParametersPC object."""
        self.name = name
        self.show = True
        self.color_pc = True
        self.pc_scale = 1.0


class GuiParametersRN:
    """Class representing GUI parameters for road networks."""

    def __init__(self, name: str) -> None:
        """Initialize the GuiParametersRN object."""
        self.name = name
        self.show = True
        self.color_rn = True
        self.rn_scale = 1.0


class GuiParametersDates:
    """Class representing an example of GUI parameters.

    Attributes
    ----------
    year_start : int
        The starting year.
    month_start : int
        The starting month.
    day_start : int
        The starting day.
    hour_start : int
        The starting hour.
    year_end : int
        The ending year.
    month_end : int
        The ending month.
    day_end : int
        The ending day.
    hour_end : int
        The ending hour.
    color : list of float
        The color used for GUI elements.
    text_color : list of float
        The inverted color for text elements.
    gui_width : int
        The width of the GUI window.
    gui_height : int
        The height of the GUI window.
    single_date : bool
        Flag indicating whether a single date is selected.
    period : bool
        Flag indicating whether a date period is selected.
    checkbox1 : bool
        The state of the first checkbox.
    checkbox2 : bool
        The state of the second checkbox.
    combo_selected_index : int
        The selected index in the combo box.
    """

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
        self.text_color = Gui.invert_color(self.color)
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


class Gui:
    """Graphical user interface (GUI) calss built on imgui and GLFW.

    This class has settings and methods for creating a GUI window and components
    for interacting with Mesh and PointCloud objects.

    Attributes
    ----------
    gui_width : int
        The width of the GUI window.
    gui_min_width : int
        The minimum width of the GUI window.
    gui_max_width : int
        The maximum width of the GUI window.
    gui_height : int
        The height of the GUI window.
    gui_min_height : int
        The minimum height of the GUI window.
    gui_max_height : int
        The maximum height of the GUI window.
    margin : int
        The margin for GUI window positioning.
    """

    gui_width: int
    gui_min_width: int
    gui_max_width: int
    gui_height: int
    gui_min_height: int
    gui_max_height: int
    margin: int

    def __init__(self) -> None:
        """
        Initialize an instance of the Gui class.
        """
        pass

    def init_draw(self, impl: GlfwRenderer) -> None:
        """Initialize the GUI drawing environment."""
        window_with = impl.io.display_size.x
        self.gui_width = 320
        self.margin = 40
        impl.process_inputs()
        imgui.new_frame()
        imgui.set_next_window_size_constraints(
            (self.gui_width, 20), (self.gui_width, 1200)
        )
        imgui.begin(
            "DTCC Viewer",
            flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_SAVED_SETTINGS,
        )
        imgui.set_window_position_labeled(
            "DTCC Viewer", window_with - (self.gui_width + self.margin), self.margin
        )

    def end_draw(self, impl: GlfwRenderer) -> None:
        """Finalize the GUI drawing and rendering."""
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        imgui.end_frame()

    def draw_pc_gui(self, guip: GuiParametersPC, index: int) -> None:
        """Draw GUI for point clouds."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("Show pc " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("Color pc " + str(index))
            [changed, guip.color_pc] = imgui.checkbox("Color", guip.color_pc)
            imgui.pop_id()
            imgui.push_id("Color pc " + str(index))
            [changed, guip.pc_scale] = imgui.slider_float(
                "Scale factor", guip.pc_scale, 0, 10
            )
            imgui.pop_id()

    def draw_rn_gui(self, guip: GuiParametersRN, index: int) -> None:
        """Draw GUI for road networks."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("Show rn " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("Color rn " + str(index))
            [changed, guip.color_rn] = imgui.checkbox("Color", guip.color_rn)
            imgui.pop_id()
            imgui.push_id("Color rn " + str(index))
            [changed, guip.rn_scale] = imgui.slider_float(
                "Scale factor", guip.rn_scale, 0, 10
            )
            imgui.pop_id()

    def draw_mesh_gui(self, guip: GuiParametersMesh, index: int) -> None:
        """Draw GUI for mesh."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("Show mesh " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("Color mesh " + str(index))
            [changed, guip.color_mesh] = imgui.checkbox("Color", guip.color_mesh)
            imgui.pop_id()

            if guip.mesh_shading == MeshShading.shadows:
                imgui.same_line()
                imgui.push_id("Animate light " + str(index))
                [changed, guip.animate_light] = imgui.checkbox(
                    "Animate light", guip.animate_light
                )
                imgui.pop_id()

            # Drawing mode
            imgui.push_id("Combo " + str(index))
            items = ["wireframe", "ambient", "diffuse", "wireshaded", "shadows"]
            with imgui.begin_combo("combo", items[guip.mesh_shading]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.mesh_shading
                        if imgui.selectable(item, is_selected)[0]:
                            guip.mesh_shading = i

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

    def draw_separator(self) -> None:
        """Draw a separator between GUI elements."""
        imgui.spacing()
        imgui.separator()
        imgui.spacing()

    def draw_apperance_gui(self, guip: GuiParameters) -> None:
        """Draw GUI elements for adjusting appearance settings like background color."""
        [expanded, visible] = imgui.collapsing_header("Appearance")
        if expanded:
            imgui.spacing()
            [changed, guip.color] = imgui.color_edit4(
                "color", guip.color[0], guip.color[1], guip.color[2], guip.color[3]
            )
            imgui.spacing()

            imgui.push_id("CbxClipX")
            [changed, guip.clip_bool[0]] = imgui.checkbox("Clip X", guip.clip_bool[0])
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("ClipX")
            [changed, guip.clip_dist[0]] = imgui.slider_float(
                "", guip.clip_dist[0], -1.0, 1.0
            )
            imgui.pop_id()

            imgui.push_id("CbxClipY")
            [changed, guip.clip_bool[1]] = imgui.checkbox("Clip Y", guip.clip_bool[1])
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("ClipY")
            [changed, guip.clip_dist[1]] = imgui.slider_float(
                "", guip.clip_dist[1], -1.0, 1.0
            )
            imgui.pop_id()

            imgui.push_id("CbxClipZ")
            [changed, guip.clip_bool[2]] = imgui.checkbox("Clip Z", guip.clip_bool[2])
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("ClipZ")
            [changed, guip.clip_dist[2]] = imgui.slider_float(
                "", guip.clip_dist[2], -1.0, 1.0
            )
            imgui.pop_id()

    def draw_example_gui(self, guip: GuiParametersDates) -> None:
        """Draw an example GUI using provided parameters."""
        self.styles(guip)
        self.buttons_example(guip)
        self.checkbox_example(guip)
        self.combo_example(guip)
        self.add_date_controls(guip)
        self.draw_apperance_example(guip)

    def styles(self, guip: GuiParametersDates) -> None:
        """Apply custom GUI styling based on provided parameters."""
        style = imgui.get_style()
        style.colors[imgui.COLOR_BORDER] = (0, 0.5, 1, 1)
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = (0.5, 0.5, 0.5, 1)
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (1, 0.5, 1, 0.5)
        style.colors[imgui.COLOR_BUTTON] = (0.3, 0.5, 1, 1)
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.2, 0.2, 0.2, 0.3)
        style.colors[imgui.COLOR_TEXT] = (
            1 - guip.color[0],
            1 - guip.color[1],
            1 - guip.color[2],
            1,
        )

    @staticmethod
    def invert_color(color):
        """Invert the color."""
        inv_color = [1 - color[0], 1 - color[1], 1 - color[2], 1]
        return inv_color
