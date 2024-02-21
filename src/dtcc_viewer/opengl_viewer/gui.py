import imgui
from dtcc_viewer.opengl_viewer.utils import Shading
from imgui.integrations.glfw import GlfwRenderer
from dtcc_viewer.opengl_viewer.utils import shader_cmaps
from dtcc_viewer.opengl_viewer.model_gl import ModelGL
from dtcc_viewer.opengl_viewer.parameters import (
    GuiParameters,
    GuiParametersMesh,
    GuiParametersPC,
    GuiParametersLS,
    GuiParametersDates,
)


class Gui:
    """Graphical user interface (GUI) calss built on imgui and GLFW.

    This class has settings and methods for creating a GUI window and components
    for interacting with Mesh and PointCloud objects.

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

    def render_gui(self, model: ModelGL, impl: GlfwRenderer, gguip: GuiParameters):
        self._init_draw(impl)
        self._draw_apperance_gui(gguip)
        self._draw_model_gui(model)
        self._end_draw(impl)

    def _init_draw(self, impl: GlfwRenderer) -> None:
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

    def _draw_apperance_gui(self, guip: GuiParameters) -> None:
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

        self.draw_separator()

    def _draw_model_gui(self, model: ModelGL) -> None:
        """Draw GUI for model."""
        [expanded, visible] = imgui.collapsing_header(model.guip.name)
        if expanded:
            guip = model.guip

            imgui.push_id("Model show")
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()

            if guip.shading == Shading.shadows:
                imgui.same_line()
                imgui.push_id("Animate light")
                [changed, guip.animate_light] = imgui.checkbox(
                    "Animate light", guip.animate_light
                )
                imgui.pop_id()

            # Drawing mode combo box
            imgui.push_id("Combo")
            items = [
                "wireframe",
                "ambient",
                "diffuse",
                "wireshaded",
                "shadows",
                "picking",
            ]
            with imgui.begin_combo("Shading", items[guip.shading]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.shading
                        if imgui.selectable(item, is_selected)[0]:
                            guip.shading = i
                            print(guip.shading)
                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

            # Add individual ui for each mesh, pc, rn
            for i, mesh in enumerate(model.meshes):
                self._draw_mesh_gui(mesh.guip, i)

            for i, pc in enumerate(model.pointclouds):
                self._draw_pc_gui(pc.guip, i)

            for i, ls in enumerate(model.linestrings):
                self._draw_ls_gui(ls.guip, i)

    def _end_draw(self, impl: GlfwRenderer) -> None:
        """Finalize the GUI drawing and rendering."""
        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        imgui.end_frame()

    def _draw_mesh_gui(self, guip: GuiParametersMesh, index: int) -> None:
        """Draw GUI for mesh."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("ShowMesh " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("ColorMesh " + str(index))
            [changed, guip.color_mesh] = imgui.checkbox("Color", guip.color_mesh)
            imgui.pop_id()

            imgui.push_id("InvertColors " + str(index))
            imgui.same_line()
            [changed, guip.invert_cmap] = imgui.checkbox(
                "Invert cmap", guip.invert_cmap
            )
            if changed:
                guip.update_caps = True
            imgui.pop_id()

            key = guip.get_current_data_name()
            # Color maps combo box
            if guip.dict_has_data[key]:
                imgui.push_id("CmapCombo " + str(index))
                items = list(shader_cmaps.keys())
                with imgui.begin_combo("Color map", items[guip.cmap_idx]) as combo:
                    if combo.opened:
                        for i, item in enumerate(items):
                            is_selected = guip.cmap_idx
                            if imgui.selectable(item, is_selected)[0]:
                                guip.update_caps = True
                                guip.cmap_idx = i
                                guip.cmap_key = item
                                print(guip.cmap_idx)

                            # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                            if is_selected:
                                imgui.set_item_default_focus()
                imgui.pop_id()

            # Add combobox for selecting data to color by
            if len(guip.data_keys) > 1:
                # Drawing colors
                key = guip.get_current_data_name()
                imgui.push_id("ColorsCombo " + str(index))
                items = guip.data_keys
                with imgui.begin_combo("Data", items[guip.data_idx]) as combo:
                    if combo.opened:
                        for i, item in enumerate(items):
                            is_selected = guip.data_idx
                            if imgui.selectable(item, is_selected)[0]:
                                guip.update_caps = True
                                guip.data_idx = i
                                guip.dict_slider_caps[key][0] = 0.0
                                guip.dict_slider_caps[key][1] = 1.0

                            # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                            if is_selected:
                                imgui.set_item_default_focus()
                imgui.pop_id()

            key = guip.get_current_data_name()
            # Range sliders are only relevant if the colors are generated by data.
            if guip.dict_has_data[key]:
                # Range sliders to cap data
                imgui.push_id("lower_cap" + str(index))
                value = guip.dict_slider_caps[key][0]
                [changed, value] = imgui.slider_float("Min", value, 0, 0.99)
                if changed:
                    guip.dict_slider_caps[key][0] = value
                    guip.update_caps = True
                    if guip.dict_slider_caps[key][0] >= guip.dict_slider_caps[key][1]:
                        guip.dict_slider_caps[key][1] = (
                            guip.dict_slider_caps[key][0] + 0.001
                        )

                imgui.pop_id()

                imgui.push_id("upper_cap" + str(index))
                value = guip.dict_slider_caps[key][1]
                [changed, value] = imgui.slider_float("Max", value, 0.01, 1.0)
                if changed:
                    guip.dict_slider_caps[key][1] = value
                    guip.update_caps = True
                    if guip.dict_slider_caps[key][1] <= guip.dict_slider_caps[key][0]:
                        guip.dict_slider_caps[key][0] = (
                            guip.dict_slider_caps[key][1] - 0.001
                        )

                imgui.pop_id()

        self.draw_separator()

    def _draw_pc_gui(self, guip: GuiParametersPC, index: int) -> None:
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

            imgui.push_id("InvertColors " + str(index))
            imgui.same_line()
            [c, guip.invert_cmap] = imgui.checkbox("Invert cmap", guip.invert_cmap)
            imgui.pop_id()

            imgui.push_id("Color pc " + str(index))
            [changed, guip.pc_scale] = imgui.slider_float(
                "Scale factor", guip.pc_scale, 0, 10
            )
            imgui.pop_id()

            # Colormap selection combo box
            imgui.push_id("CmapSelectionCombo " + str(index))
            items = list(shader_cmaps.keys())
            with imgui.begin_combo("Color map", items[guip.cmap_index]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.cmap_index
                        if imgui.selectable(item, is_selected)[0]:
                            guip.update_caps = True
                            guip.cmap_index = i
                            guip.cmap_key = item

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

            key = guip.get_current_data_name()

            # Add combobox for selecting data for color calcs

            # Data selection combobox
            imgui.push_id("DataSelectionCombo " + str(index))
            items = guip.data_keys
            with imgui.begin_combo("Data", items[guip.data_index]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.data_index
                        if imgui.selectable(item, is_selected)[0]:
                            guip.update_caps = True
                            guip.data_index = i
                            # For selection of new data, reset the slider caps
                            guip.dict_slider_caps[key][0] = 0.0
                            guip.dict_slider_caps[key][1] = 1.0

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

            # Range sliders to cap data
            imgui.push_id("lower_cap" + str(index))
            value = guip.dict_slider_caps[key][0]
            [changed, value] = imgui.slider_float("Min", value, 0, 0.99)
            if changed:
                guip.dict_slider_caps[key][0] = value
                guip.update_caps = True
                if guip.dict_slider_caps[key][0] >= guip.dict_slider_caps[key][1]:
                    guip.dict_slider_caps[key][1] = (
                        guip.dict_slider_caps[key][0] + 0.001
                    )

            imgui.pop_id()

            imgui.push_id("upper_cap" + str(index))
            value = guip.dict_slider_caps[key][1]
            [changed, value] = imgui.slider_float("Max", value, 0.01, 1.0)
            if changed:
                guip.dict_slider_caps[key][1] = value
                guip.update_caps = True
                if guip.dict_slider_caps[key][1] <= guip.dict_slider_caps[key][0]:
                    guip.dict_slider_caps[key][0] = (
                        guip.dict_slider_caps[key][1] - 0.001
                    )

            imgui.pop_id()

        self.draw_separator()

    def _draw_ls_gui(self, guip: GuiParametersLS, index: int) -> None:
        """Draw GUI for road networks."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("Show rn " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("Color rn " + str(index))
            [changed, guip.color] = imgui.checkbox("Color", guip.color)
            imgui.pop_id()
            imgui.push_id("Color rn " + str(index))
            [changed, guip.scale] = imgui.slider_float(
                "Scale factor", guip.scale, 0, 10
            )
            imgui.pop_id()

            # Colormap selection combo box
            imgui.push_id("CmapSelectionCombo " + str(index))
            items = list(shader_cmaps.keys())
            with imgui.begin_combo("Color map", items[guip.cmap_idx]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.cmap_idx
                        if imgui.selectable(item, is_selected)[0]:
                            guip.update_caps = True
                            guip.cmap_idx = i
                            guip.cmap_key = item

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

            key = guip.get_current_data_name()

            # Data selection combobox
            imgui.push_id("DataSelectionCombo " + str(index))
            items = guip.data_keys
            with imgui.begin_combo("Data", items[guip.data_idx]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.data_idx
                        if imgui.selectable(item, is_selected)[0]:
                            guip.update_caps = True
                            guip.data_idx = i
                            # For selection of new data, reset the slider caps
                            guip.dict_slider_caps[key][0] = 0.0
                            guip.dict_slider_caps[key][1] = 1.0

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

            # Range sliders to cap data
            imgui.push_id("lower_cap" + str(index))
            value = guip.dict_slider_caps[key][0]
            [changed, value] = imgui.slider_float("Min", value, 0, 0.99)
            if changed:
                guip.dict_slider_caps[key][0] = value
                guip.update_caps = True
                if guip.dict_slider_caps[key][0] >= guip.dict_slider_caps[key][1]:
                    guip.dict_slider_caps[key][1] = (
                        guip.dict_slider_caps[key][0] + 0.001
                    )

            imgui.pop_id()

            imgui.push_id("upper_cap" + str(index))
            value = guip.dict_slider_caps[key][1]
            [changed, value] = imgui.slider_float("Max", value, 0.01, 1.0)
            if changed:
                guip.dict_slider_caps[key][1] = value
                guip.update_caps = True
                if guip.dict_slider_caps[key][1] <= guip.dict_slider_caps[key][0]:
                    guip.dict_slider_caps[key][0] = (
                        guip.dict_slider_caps[key][1] - 0.001
                    )

            imgui.pop_id()

        self.draw_separator()

    def draw_separator(self) -> None:
        """Draw a separator between GUI elements."""
        imgui.spacing()
        imgui.separator()
        imgui.spacing()

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
