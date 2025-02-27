import imgui
import glfw
import copy
import os
from OpenGL.GL import *
from dtcc_viewer.opengl.utils import Shading
from imgui.integrations.glfw import GlfwRenderer
from dtcc_viewer.opengl import GuiParametersDates, GuiParametersGlobal


class Gui:
    gui_width: int
    gui_min_width: int
    gui_max_width: int
    gui_height: int
    gui_min_height: int
    gui_max_height: int
    margin: int

    def __init__(self) -> None:
        pass

    def init_draw(self, impl: GlfwRenderer) -> None:
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
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        imgui.end_frame()

    def draw_example_gui(self, guip: GuiParametersDates) -> None:
        self.styles(guip)
        self.buttons_example(guip)
        self.checkbox_example(guip)
        self.combo_example(guip)
        self.add_example_dates(guip)
        self.draw_apperance_example(guip)

    def styles(self, guip: GuiParametersDates) -> None:
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

    def buttons_example(self, guip: GuiParametersDates) -> None:
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

    def combo_example(self, guip: GuiParametersDates):
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

    def checkbox_example(self, guip: GuiParametersDates) -> None:
        [expanded, visible] = imgui.collapsing_header("Checkboxes")
        if expanded:
            # Check box to change settings
            [changed, guip.checkbox1] = imgui.checkbox("cbx1!", guip.checkbox1)
            imgui.same_line()
            [changed, guip.checkbox2] = imgui.checkbox("cbx2!", guip.checkbox2)

        imgui.spacing()

    def add_example_dates(self, guip: GuiParametersDates) -> None:
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

    def draw_apperance_example(self, guip: GuiParametersDates) -> None:
        [expanded, visible] = imgui.collapsing_header("Appearance")
        if expanded:
            [changed, guip.color] = imgui.color_edit4(
                "color", guip.color[0], guip.color[1], guip.color[2], guip.color[3]
            )

    def draw_bar(self, guip: GuiParametersDates) -> None:
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
        new_day = current_day
        days_per_month = Gui.get_days_per_month(year, month)

        if current_day > days_per_month:
            print(days_per_month)
            new_day = days_per_month

        return new_day

    @staticmethod
    def get_days_per_month(year: int, month: int) -> None:
        days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (year % 4) == 0:
            days_per_month[1] = 29

        month_index = month - 1
        return days_per_month[month_index]

    @staticmethod
    def invert_color(color):
        """Invert the color."""
        inv_color = [1 - color[0], 1 - color[1], 1 - color[2], 1]
        return inv_color


if __name__ == "__main__":
    os.system("clear")

    imgui.create_context()
    io = imgui.get_io()

    if not glfw.init():
        raise Exception("glfw can not be initialised!")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(1200, 800, "OpenGL Window", None, None)

    if not window:
        glfw.terminate()
        raise Exception("glfw window can not be created!")

    glfw.set_window_pos(window, 400, 200)

    # Calls can be made after the contex is made current
    glfw.make_context_current(window)

    impl = GlfwRenderer(window)

    gui = Gui()
    guid = GuiParametersDates()
    guip = GuiParametersGlobal()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(
            guip.color[0],
            guip.color[1],
            guip.color[2],
            guip.color[3],
        )

        gui.init_draw(impl)
        gui.draw_apperance_example(guid)
        gui.add_example_dates(guid)
        gui.end_draw(impl)

        glfw.poll_events()
        glfw.swap_buffers(window)

    glfw.terminate()
