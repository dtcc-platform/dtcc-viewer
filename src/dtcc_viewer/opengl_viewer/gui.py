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
    """Class representing GUI parameters for meshes.

    Attributes
    ----------
    name : str
        The name of the mesh.
    show : bool
        Flag indicating whether the mesh is visible.
    color_mesh : bool
        Flag indicating whether mesh coloring is enabled.
    animate_light : bool
        Flag indicating whether light animation is enabled.
    mesh_shading : MeshShading
        The shading mode for the mesh.
    """

    def __init__(self, name: str) -> None:
        """Initialize the GuiParametersMesh object.

        Parameters
        ----------
        name : str
            The name of the mesh.
        """
        self.name = name
        self.show = True
        self.color_mesh = True
        self.animate_light = False
        self.mesh_shading = MeshShading.shaded_diffuse


class GuiParametersPC:
    """Class representing GUI parameters for point clouds.

    Attributes
    ----------
    name : str
        The name of the point cloud.
    show : bool
        Flag indicating whether the point cloud is visible.
    color_pc : bool
        Flag indicating whether point cloud coloring is enabled.
    pc_scale : float
        The scaling factor for the point cloud.
    """

    def __init__(self, name: str) -> None:
        """Initialize the GuiParametersPC object.

        Parameters
        ----------
        name : str
            The name of the point cloud.
        """
        self.name = name
        self.show = True
        self.color_pc = True
        self.pc_scale = 1.0


class GuiParametersExample:
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

    This class has settings and methods for creating a GUI window and components for
    interacting with Mesh and PointCloud objects.

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
        """
        Initialize the GUI drawing environment.

        Parameters
        ----------
        impl : GlfwRenderer
            The GlfwRenderer instance used for rendering.

        Returns
        -------
        None
        """
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
        """
        Finalize the GUI drawing and rendering.

        Parameters
        ----------
        impl : GlfwRenderer
            The GlfwRenderer instance used for rendering.

        Returns
        -------
        None
        """
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        imgui.end_frame()

    def draw_pc_gui(self, guip: GuiParametersPC, index: int) -> None:
        """
        Draw GUI elements for point clouds.

        Parameters
        ----------
        guip : GuiParametersPC
            The GuiParametersPC instance containing point cloud parameters.
        index : int
            The index of the point cloud.

        Returns
        -------
        None
        """
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

    def draw_mesh_gui(self, guip: GuiParametersMesh, index: int) -> None:
        """
        Draw GUI elements for meshes.

        Parameters
        ----------
        guip : GuiParametersMesh
            The GuiParametersMesh instance containing mesh parameters.
        index : int
            The index of the mesh.

        Returns
        -------
        None
        """
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("Show mesh " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("Color mesh " + str(index))
            [changed, guip.color_mesh] = imgui.checkbox("Color", guip.color_mesh)
            imgui.pop_id()

            if guip.mesh_shading == MeshShading.shaded_shadows:
                imgui.same_line()
                imgui.push_id("Animate light " + str(index))
                [changed, guip.animate_light] = imgui.checkbox(
                    "Animate light", guip.animate_light
                )
                imgui.pop_id()

            # Drawing mode
            imgui.push_id("Combo " + str(index))
            items = ["Wireframe", "Shaded ambient", "Shaded diffuse", "Shaded shadow"]
            with imgui.begin_combo("combo", items[guip.mesh_shading]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = i == guip.mesh_shading
                        if imgui.selectable(item, is_selected)[0]:
                            guip.mesh_shading = i

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

    def draw_separator(self) -> None:
        """
        Draw a separator between GUI elements.

        Returns
        -------
        None
        """
        imgui.spacing()
        imgui.separator()
        imgui.spacing()

    def draw_apperance_gui(self, guip: GuiParameters) -> None:
        """
        Draw GUI elements for adjusting appearance settings like background color.

        Parameters
        ----------
        guip : GuiParameters
            The GuiParameters instance containing appearance parameters.

        Returns
        -------
        None
        """
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

    def draw_example_gui(self, guip: GuiParametersExample) -> None:
        """
        Draw an example GUI using provided parameters.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing example GUI parameters.

        Returns
        -------
        None
        """
        self.styles(guip)
        self.buttons_example(guip)
        self.checkbox_example(guip)
        self.combo_example(guip)
        self.add_example_dates(guip)
        self.draw_apperance_example(guip)

    def styles(self, guip: GuiParametersExample) -> None:
        """
        Apply custom GUI styling based on provided parameters.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing style parameters.

        Returns
        -------
        None
        """
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

    def buttons_example(self, guip: GuiParametersExample) -> None:
        """
        Draw example buttons with associated actions.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing button parameters.

        Returns
        -------
        None
        """
        [expanded, visible] = imgui.collapsing_header("Buttons")
        if expanded:
            # Buttons to trigger action of some sort
            if imgui.button("btn1!"):
                print("Pressed first btn")

            imgui.same_line()
            if imgui.button("btn2!"):
                print("Pressed second btn")

            imgui.same_line()
            if imgui.button("btn3!"):
                print("Pressed third btn")

        imgui.spacing()

    def combo_example(self, guip: GuiParametersExample):
        """
        Draw an example combo box for selecting items.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing combo box parameters.

        Returns
        -------
        None
        """
        [expanded, visible] = imgui.collapsing_header("Combo")
        if expanded:
            items = ["AAAA", "BBBB", "CCCC", "DDDD"]
            with imgui.begin_combo("combo", items[guip.combo_selected_index]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = i == guip.combo_selected_index
                        if imgui.selectable(item, is_selected)[0]:
                            guip.combo_selected_index = i

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
        imgui.spacing()

    def checkbox_example(self, guip: GuiParametersExample) -> None:
        """
        Draw example checkboxes for changing settings.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing checkbox parameters.

        Returns
        -------
        None
        """
        [expanded, visible] = imgui.collapsing_header("Checkboxes")
        if expanded:
            # Check box to change settings
            [changed, guip.checkbox1] = imgui.checkbox("cbx1!", guip.checkbox1)
            imgui.same_line()
            [changed, guip.checkbox2] = imgui.checkbox("cbx2!", guip.checkbox2)

        imgui.spacing()

    def add_example_dates(self, guip: GuiParametersExample) -> None:
        """
        Draw example date and period selection controls.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing date and period parameters.

        Returns
        -------
        None
        """
        [expanded, visible] = imgui.collapsing_header("Date")

        if expanded:
            if imgui.radio_button("date", guip.single_date):
                guip.period = guip.single_date
                guip.single_date = not guip.single_date

            imgui.same_line()
            if imgui.radio_button("period", guip.period):
                guip.single_date = guip.period
                guip.period = not guip.period

            if guip.period:
                imgui.same_line()
                if imgui.button("match"):
                    guip.match()

            self.draw_bar(guip)

            # Sliders to change values
            [changed_year, guip.year_start] = imgui.slider_int(
                "year_start", guip.year_start, 1990, 2023
            )
            [changed_month, guip.month_start] = imgui.slider_int(
                "month_start", guip.month_start, 1, 12
            )
            [changed_day, guip.day_start] = imgui.slider_int(
                "day_start",
                guip.day_start,
                1,
                Gui.get_days_per_month(guip.year_start, guip.month_start),
            )
            [changed_hour, guip.hour_start] = imgui.slider_int(
                "hour_start", guip.hour_start, 0, 24
            )

            if (changed_month, changed_year):
                new_day = Gui.update_day(
                    guip.year_start, guip.month_start, guip.day_start
                )
                guip.day_start = new_day

            # Add an other
            if guip.period:
                self.draw_bar(guip)
                [changed_year, guip.year_end] = imgui.slider_int(
                    "year_end", guip.year_end, 1990, 2023
                )
                [changed_month, guip.month_end] = imgui.slider_int(
                    "month_end", guip.month_end, 1, 12
                )
                [changed_day, guip.day_end] = imgui.slider_int(
                    "day_end",
                    guip.day_end,
                    1,
                    Gui.get_days_per_month(guip.year_end, guip.month_end),
                )
                [changed_hour, guip.hour_end] = imgui.slider_int(
                    "hour_end", guip.hour_end, 0, 24
                )

                if (changed_month, changed_year):
                    new_day = Gui.update_day(
                        guip.year_end, guip.month_end, guip.day_end
                    )
                    guip.day_end = new_day
            self.draw_bar(guip)

        imgui.spacing()

    def draw_apperance_example(self, guip: GuiParametersExample) -> None:
        """
        Draw example GUI elements for adjusting appearance settings.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing appearance parameters.

        Returns
        -------
        None
        """
        [expanded, visible] = imgui.collapsing_header("Appearance")
        if expanded:
            [changed, guip.color] = imgui.color_edit4(
                "color", guip.color[0], guip.color[1], guip.color[2], guip.color[3]
            )

    def draw_bar(self, guip: GuiParametersExample) -> None:
        """
        Draw a visual bar separator.

        Parameters
        ----------
        guip : GuiParametersExample
            The GuiParametersExample instance containing bar parameters.

        Returns
        -------
        None
        """
        imgui.push_style_color(
            imgui.COLOR_TEXT,
            guip.text_color[0],
            guip.text_color[1],
            guip.text_color[2],
            0.5,
        )
        imgui.text("//////////////////////////////////////////")
        imgui.pop_style_color()

    @staticmethod
    def update_day(year: int, month: int, current_day: int) -> None:
        """
        Update the day value to be within the valid range for the given year and month.

        Parameters
        ----------
        year : int
            The year.
        month : int
            The month.
        current_day : int
            The current day value.

        Returns
        -------
        int
            The updated day value.
        """
        new_day = current_day
        days_per_month = Gui.get_days_per_month(year, month)

        if current_day > days_per_month:
            print(days_per_month)
            new_day = days_per_month

        return new_day

    @staticmethod
    def get_days_per_month(year: int, month: int) -> None:
        """
        Get the number of days in a month for a given year.

        Parameters
        ----------
        year : int
            The year.
        month : int
            The month.

        Returns
        -------
        int
            The number of days in the month.
        """
        days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (year % 4) == 0:
            days_per_month[1] = 29

        month_index = month - 1
        return days_per_month[month_index]

    @staticmethod
    def invert_color(color):
        """
        Invert the color.

        Parameters
        ----------
        color
            The color value to be inverted.

        Returns
        -------
        list
            The inverted color value.
        """
        inv_color = [1 - color[0], 1 - color[1], 1 - color[2], 1]
        return inv_color
