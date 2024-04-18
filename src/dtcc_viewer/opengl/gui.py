import imgui
import numpy as np
from dtcc_viewer.opengl.utils import (
    Shading,
    ColorMaps,
    RasterType,
    CameraProjection,
    CameraView,
)
from imgui.integrations.glfw import GlfwRenderer
from dtcc_viewer.opengl.gl_model import GlModel
from dtcc_viewer.opengl.gl_mesh import GlMesh
from dtcc_viewer.opengl.gl_pointcloud import GlPointCloud
from dtcc_viewer.opengl.gl_raster import GlRaster
from dtcc_viewer.opengl.gl_linestring import GlLineString
from dtcc_viewer.opengl.parameters import (
    GuiParametersGlobal,
    GuiParametersObj,
    GuiParametersMesh,
    GuiParametersPC,
    GuiParametersLS,
    GuiParametersRaster,
    GuiParametersDates,
    GuiParametersModel,
)


class Gui:
    """Graphical user interface (GUI) calss built on imgui and GLFW.

    This class has settings and methods for creating a GUI window and components
    for interacting with Mesh and PointCloud objects.

    """

    min_width: int
    min_width: int
    max_width: int
    gui_height: int
    min_height: int
    max_height: int
    margin: int
    id: int

    shading_names: list[str]
    cmaps_names: list[str]
    camera_view_names: list[str]

    selected: int

    def __init__(self) -> None:
        """
        Initialize an instance of the Gui class.
        """
        np.set_printoptions(precision=1)
        self.shading_names = [style.name.lower() for style in Shading]
        self.cmaps_names = [cmap.name.lower() for cmap in ColorMaps]
        self.camera_view_names = [view.name.lower() for view in CameraView]
        self.selected = 0

    def render(self, model: GlModel, impl: GlfwRenderer, gguip: GuiParametersGlobal):
        self._init_gui(impl)

        # Draw window with GUI controls
        self._init_win_1(impl)
        self._draw_apperance_gui(gguip)
        self._draw_model_gui(model)
        self._end_win_1(impl)

        # Draw window for data display
        self._init_win_2(impl)
        self._draw_help()
        self._draw_data(model)
        self._draw_fps(gguip)
        self._end_win_2()

        self._end_gui(impl)

    def _init_gui(self, impl: GlfwRenderer) -> None:
        self.min_width = 320
        self.max_width = 320
        self.min_height = 20
        self.max_height = 1200
        self.text_width = 40
        self.margin = 30
        impl.process_inputs()
        imgui.new_frame()

    def _init_win_1(self, impl: GlfwRenderer) -> None:
        """Initialize the GUI drawing environment."""
        imgui.set_next_window_size_constraints(
            (self.min_width, self.min_height), (self.max_width, self.max_height)
        )
        window_with = impl.io.display_size.x
        imgui.begin(
            "Controls",
            flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE
            | imgui.WINDOW_NO_SAVED_SETTINGS
            | imgui.WINDOW_NO_MOVE,
        )
        imgui.set_window_position_labeled(
            "Controls", window_with - (self.min_width + self.margin), self.margin
        )

    def _draw_apperance_gui(self, gguip: GuiParametersGlobal) -> None:
        """Draw GUI elements for adjusting appearance settings like background color."""
        [expanded, visible] = imgui.collapsing_header("Appearance")
        if expanded:

            # Visualisation settings box
            imgui.begin_child("Box1", 0, 57, border=True)
            # Testing radio buttons
            options = ["Perspective", "Ortho projection"]
            selected_index = gguip.camera_projection.value
            self._create_radiobuttons(options, selected_index, gguip, True)

            # Display mode combo box
            imgui.push_id("ComboView")
            items = self.camera_view_names
            with imgui.begin_combo("View", items[gguip.camera_view]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = gguip.camera_view
                        if imgui.selectable(item, is_selected)[0]:
                            gguip.camera_view = i
                            gguip.update_camera = True
                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()
            imgui.end_child()

            imgui.spacing()

            imgui.begin_child("Box2", 0, 37, border=True)
            [changed, gguip.color] = imgui.color_edit4(
                "Background",
                gguip.color[0],
                gguip.color[1],
                gguip.color[2],
                gguip.color[3],
            )
            imgui.end_child()

            imgui.spacing()

            imgui.begin_child("Box3", 0, 81, border=True)

            (gguip.clip_bool[0], gguip.clip_dist[0]) = self._create_clip_slider(
                "Clip X", gguip.clip_bool[0], gguip.clip_dist[0]
            )

            (gguip.clip_bool[1], gguip.clip_dist[1]) = self._create_clip_slider(
                "Clip Y", gguip.clip_bool[1], gguip.clip_dist[1]
            )

            (gguip.clip_bool[2], gguip.clip_dist[2]) = self._create_clip_slider(
                "Clip Z", gguip.clip_bool[2], gguip.clip_dist[2], min=0, max=1.0
            )

            imgui.end_child()

            # Grid settings
            imgui.begin_child("Box4", 0, 57, border=True)
            imgui.push_id("grid")
            [changed, gguip.show_grid] = imgui.checkbox("grid", gguip.show_grid)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("adaptive")
            [changed, gguip.grid_adapt] = imgui.checkbox("adaptive", gguip.grid_adapt)
            imgui.pop_id()
            imgui.same_line()
            imgui.text(f"spacing: {gguip.grid_sf} m")
            imgui.push_id("cs")
            [changed, gguip.show_axes] = imgui.checkbox(
                "coordinate axis", gguip.show_axes
            )
            imgui.pop_id()
            imgui.end_child()

        self._draw_separator()

    def _create_clip_slider(
        self, name: str, clip_bool: bool, clip_dist: float, min=-1.0, max=1.0
    ):
        imgui.push_id(name + "1")
        [changed, clip_bool] = imgui.checkbox(name, clip_bool)
        imgui.pop_id()
        imgui.same_line()
        imgui.push_id(name + "2")
        [changed, clip_dist] = imgui.slider_float("", clip_dist, min, max)
        imgui.pop_id()

        return clip_bool, clip_dist

    def _draw_model_gui(self, model: GlModel) -> None:
        """Draw GUI for model."""
        meshes = model.filter_gl_type(GlMesh)
        pointclouds = model.filter_gl_type(GlPointCloud)
        linestrings = model.filter_gl_type(GlLineString)
        rasters = model.filter_gl_type(GlRaster)

        [expanded, visible] = imgui.collapsing_header(model.guip.name)
        if expanded:
            guip = model.guip

            imgui.push_id("Model show")
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()

            if guip.shading == Shading.SHADOWS:
                imgui.same_line()
                imgui.push_id("Animate light")
                [changed, guip.animate_light] = imgui.checkbox(
                    "Animate light", guip.animate_light
                )
                imgui.pop_id()

            # Display mode combo box
            self._create_combo_display(meshes, guip)

            # The id ensures gui component has a unique identifyer while they may have
            # the same name
            self.id = 0

            # Add individual ui for each mesh, pc, rn
            for mesh in meshes:
                self._draw_mesh_gui(mesh.guip, self._get_id())

            for pc in pointclouds:
                self._draw_pc_gui(pc.guip, self._get_id())

            for ls in linestrings:
                self._draw_ls_gui(ls.guip, self._get_id())

            for rst in rasters:
                self._draw_rst_gui(rst.guip, self._get_id())

    def _get_id(self):
        self.id += 1
        return self.id

    def _end_win_1(self, impl: GlfwRenderer) -> None:
        imgui.end()

    def _end_gui(self, impl: GlfwRenderer) -> None:
        """Finalize the GUI drawing and rendering."""
        imgui.render()
        impl.render(imgui.get_draw_data())
        imgui.end_frame()

    def _draw_mesh_gui(self, guip: GuiParametersMesh, index: int) -> None:
        """Draw GUI for mesh."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.begin_child("BoxMesh" + str(index), 0, 150, border=True)
            self._create_cbxs(index, guip)
            self._create_normals_cbx(index, guip)
            self._create_combo_cmaps(index, guip)
            self._create_cobmo_data(index, guip)
            self._create_range_sliders(index, guip)
            imgui.end_child()

        self._draw_separator()

    def _draw_pc_gui(self, guip: GuiParametersPC, index: int) -> None:
        """Draw GUI for point clouds."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:

            self._create_cbxs(index, guip)

            imgui.push_id("Size" + str(index))
            [changed, guip.point_scale] = imgui.slider_float(
                "Scale factor", guip.point_scale, 0, 10
            )
            imgui.pop_id()

            self._create_combo_cmaps(index, guip)
            self._create_cobmo_data(index, guip)
            self._create_range_sliders(index, guip)

        self._draw_separator()

    def _draw_ls_gui(self, guip: GuiParametersLS, index: int) -> None:
        """Draw GUI for road networks."""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            self._create_cbxs(index, guip)
            self._create_combo_cmaps(index, guip)
            self._create_cobmo_data(index, guip)
            self._create_range_sliders(index, guip)

        self._draw_separator()

    def _draw_rst_gui(self, guip: GuiParametersRaster, index: int) -> None:
        """Draw GUI for raster"""
        [expanded, visible] = imgui.collapsing_header(str(index) + " " + guip.name)
        if expanded:
            imgui.push_id("Show raster " + str(index))
            [changed, guip.show] = imgui.checkbox("Show", guip.show)
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id("Color raster " + str(index))
            [changed, guip.color] = imgui.checkbox("Color", guip.color)
            imgui.pop_id()
            imgui.push_id("InvertRasterColors " + str(index))
            imgui.same_line()
            [c, guip.invert_cmap] = imgui.checkbox("Invert cmap", guip.invert_cmap)
            imgui.pop_id()

            if guip.type == RasterType.Data:
                # Colormap selection combo box
                imgui.push_id("CmapSelectionCombo " + str(index))
                items = self.cmaps_names
                with imgui.begin_combo("Color map", items[guip.cmap_idx]) as combo:
                    if combo.opened:
                        for i, item in enumerate(items):
                            is_selected = guip.cmap_idx
                            if imgui.selectable(item, is_selected)[0]:
                                guip.cmap_idx = i

                            # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                            if is_selected:
                                imgui.set_item_default_focus()
                imgui.pop_id()

            elif guip.type == RasterType.RGB or guip.type == RasterType.RGBA:
                imgui.text("Active channels: ")
                imgui.same_line()
                imgui.push_id("Draw r-channel " + str(index))
                [c, guip.channels[0]] = imgui.checkbox("R", guip.channels[0])
                imgui.pop_id()
                imgui.same_line()
                imgui.push_id("Draw g-channel " + str(index))
                [c, guip.channels[1]] = imgui.checkbox("G", guip.channels[1])
                imgui.pop_id()
                imgui.same_line()
                imgui.push_id("Draw b-channel " + str(index))
                [c, guip.channels[2]] = imgui.checkbox("B", guip.channels[2])
                imgui.pop_id()

            if guip.type == RasterType.RGBA:
                imgui.same_line()
                imgui.push_id("Draw a-channel " + str(index))
                [c, guip.channels[3]] = imgui.checkbox("A", guip.channels[3])
                imgui.pop_id()

    def _draw_separator(self) -> None:
        """Draw a separator between GUI elements."""
        imgui.spacing()
        imgui.separator()
        imgui.spacing()

    def _create_radiobuttons(
        self,
        options: list[str],
        selected: int,
        guip: GuiParametersGlobal,
        same_line: bool,
    ) -> int:
        """Create a set of radio buttons for selecting an option."""
        for i, option in enumerate(options):
            is_selected = selected == i
            imgui.radio_button(option, is_selected)
            if same_line and i < len(options) - 1:
                imgui.same_line()

            if imgui.is_item_clicked():
                selected = i
                guip.camera_projection = CameraProjection(i)

        return selected

    def _create_combo_display(self, meshes: list[GlMesh], guip: GuiParametersModel):
        if len(meshes) > 0:
            # Display mode combo box
            imgui.push_id("Combo")

            items = self.shading_names

            with imgui.begin_combo("Display mode", items[guip.shading]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.shading
                        if imgui.selectable(item, is_selected)[0]:
                            guip.shading = i
                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

    def _create_cbxs(self, index: int, guip: GuiParametersDates) -> None:
        """Create checkboxes for common visualisation options."""

        # Toggle visualisation on and off
        imgui.push_id("Show" + str(index))
        [changed, guip.show] = imgui.checkbox("show     ", guip.show)
        imgui.pop_id()

        # Toggle color on and off
        imgui.same_line()
        imgui.push_id("Color" + str(index))
        [changed, guip.color] = imgui.checkbox("color", guip.color)
        imgui.pop_id()

        # Toggle color map inversion
        imgui.same_line()
        imgui.push_id("Invert" + str(index))
        [c, guip.invert_cmap] = imgui.checkbox("invert cmap", guip.invert_cmap)
        imgui.pop_id()

    def _create_normals_cbx(self, index: int, guip: GuiParametersMesh) -> None:
        """Create a checkbox for displaying normals."""
        imgui.push_id("face normals" + str(index))
        [changed, guip.show_fnormals] = imgui.checkbox("f-normals", guip.show_fnormals)
        imgui.pop_id()
        imgui.same_line()
        imgui.push_id("vertex normals" + str(index))
        [changed, guip.show_vnormals] = imgui.checkbox("v-normals", guip.show_vnormals)
        imgui.pop_id()

    def _create_combo_cmaps(self, index: int, guip: GuiParametersObj) -> None:
        """Create a combo box for selecting color maps."""
        imgui.push_id("CmapCombo " + str(index))
        items = self.cmaps_names
        with imgui.begin_combo("cmap", items[guip.cmap_idx]) as combo:
            if combo.opened:
                for i, item in enumerate(items):
                    is_selected = guip.cmap_idx
                    if imgui.selectable(item, is_selected)[0]:
                        guip.update_caps = True
                        guip.cmap_idx = i

                    # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                    if is_selected:
                        imgui.set_item_default_focus()
        imgui.pop_id()

    def _create_cobmo_data(self, index: int, guip: GuiParametersObj) -> None:
        """Create a combo box for data selection."""

        if len(guip.data_keys) > 1:
            key = guip.get_current_data_name()
            imgui.push_id("ColorsCombo " + str(index))
            items = guip.data_keys
            with imgui.begin_combo("Data", items[guip.data_idx]) as combo:
                if combo.opened:
                    for i, item in enumerate(items):
                        is_selected = guip.data_idx
                        if imgui.selectable(item, is_selected)[0]:
                            guip.update_caps = True
                            guip.update_data_tex = True
                            guip.data_idx = i
                            guip.dict_slider_caps[key][0] = 0.0
                            guip.dict_slider_caps[key][1] = 1.0

                        # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                        if is_selected:
                            imgui.set_item_default_focus()
            imgui.pop_id()

    def _create_range_sliders(self, index: int, guip: GuiParametersObj) -> None:
        """Create range sliders for adjusting data range."""

        key = guip.get_current_data_name()

        # Range sliders to cap data
        imgui.push_id("lower_cap" + str(index))
        value = guip.dict_slider_caps[key][0]
        [changed, value] = imgui.slider_float("Min", value, 0, 0.99)
        if changed:
            guip.dict_slider_caps[key][0] = value
            guip.update_caps = True
            if guip.dict_slider_caps[key][0] >= guip.dict_slider_caps[key][1]:
                guip.dict_slider_caps[key][1] = guip.dict_slider_caps[key][0] + 0.001

        imgui.pop_id()

        imgui.push_id("upper_cap" + str(index))
        value = guip.dict_slider_caps[key][1]
        [changed, value] = imgui.slider_float("Max", value, 0.01, 1.0)
        if changed:
            guip.dict_slider_caps[key][1] = value
            guip.update_caps = True
            if guip.dict_slider_caps[key][1] <= guip.dict_slider_caps[key][0]:
                guip.dict_slider_caps[key][0] = guip.dict_slider_caps[key][1] - 0.001

        imgui.pop_id()

    def _styles(self, guip: GuiParametersDates) -> None:
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

    def _init_win_2(self, impl: GlfwRenderer) -> None:
        imgui.set_next_window_size_constraints(
            (self.min_width, self.min_height), (self.max_width, self.max_height)
        )

        imgui.begin(
            "Properties",
            flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE
            | imgui.WINDOW_NO_SAVED_SETTINGS
            | imgui.WINDOW_NO_MOVE,
        )

        imgui.set_window_position_labeled("Properties", self.margin, self.margin)

    def _end_win_2(self) -> None:
        imgui.end()

    def _draw_help(self) -> None:
        """Draw GUI elements for adjusting appearance settings like background color."""
        width = self.text_width
        [expanded, visible] = imgui.collapsing_header("Help")
        if expanded:
            imgui.begin_child(
                "Scrolling_help",
                0,
                250,
                border=True,
                flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE,
            )

            imgui.bullet_text("NAVIGATION:")
            text_0 = "- Use the mouse to navigate the scene."
            text_1 = "- Press left mouse button to rotate the view."
            text_2 = "- Press right mouse button to pan the view."
            text_3 = "- Scroll the mouse wheel to zoom in and out."
            imgui.text(self.wrap_text(text_0, width))
            imgui.text(self.wrap_text(text_1, width))
            imgui.text(self.wrap_text(text_2, width))
            imgui.text(self.wrap_text(text_3, width))

            imgui.bullet_text("OBJECT SELECTION:")
            text_0 = " - Left-click on an object to select an object."
            text_1 = " - Data attached to the selected object will be displayed under 'data'."
            imgui.text(self.wrap_text(text_0, width))
            imgui.text(self.wrap_text(text_1, width))

            imgui.bullet_text("VIEW OPTIONS:")
            text_0 = " - Use the gui under the 'Appearance' to set background color and clipping planes."
            text_1 = "- Use the checkboxes or dropdown menus for each object under 'Model' to customise the view."
            text_2 = "- Use the range sliders to set the range of data to be displayed."
            imgui.text(self.wrap_text(text_0, width))
            imgui.text(self.wrap_text(text_1, width))
            imgui.text(self.wrap_text(text_2, width))

            imgui.bullet_text("ADDITIONAL TIPS:")
            text_0 = "- If shadow display mode selected, the light source can be animated by checking the 'Animate light' checkbox."
            text_1 = "- If shadow display mode selected, the 'S-'key can be pressed to toggle display of the shadow map from the light source persepctive."
            imgui.text(self.wrap_text(text_0, width))
            imgui.text(self.wrap_text(text_1, width))

            imgui.bullet_text("HELP:")
            text_0 = "- If you need further assistance, reach out on github."
            imgui.text(self.wrap_text(text_0, width))

            imgui.end_child()

        self._draw_separator()

    def _draw_data(self, model: GlModel) -> None:
        """Draw GUI elements for adjusting appearance settings like background color."""
        width = self.text_width
        [expanded, visible] = imgui.collapsing_header("Data")
        mhs = model.filter_gl_type(GlMesh)
        pcs = model.filter_gl_type(GlPointCloud)
        lss = model.filter_gl_type(GlLineString)
        rst = model.filter_gl_type(GlRaster)

        if expanded:
            self._draw_model_stats(mhs, pcs, lss, width)
            self._draw_model_data(model, width)
        self._draw_separator()

    def _draw_model_stats(
        self,
        mhs: list[GlMesh],
        pcs: list[GlPointCloud],
        lss: list[GlLineString],
        text_width: int,
    ) -> None:
        """Draw GUI elements for adjusting appearance settings like background color."""
        imgui.begin_child("ModelStats", 0, 180, border=True)
        imgui.text("MODEL STATS:")
        v_count, f_count, p_count, l_count = 0, 0, 0, 0
        for mesh in mhs:
            text_0 = f"- Mesh called: '{mesh.name}' has {mesh.n_vertices} vertices and {mesh.n_faces} faces."
            imgui.text(self.wrap_text(text_0, text_width))
            v_count += mesh.n_vertices
            f_count += mesh.n_faces
            # print(v_count)
        for pc in pcs:
            n_particles = pc.n_points
            n_vertices = (pc.n_sides + 1) * n_particles
            n_faces = pc.n_sides * n_particles
            text_0 = f"- PointCloud called: '{pc.name}' has {pc.n_points} points, which are drawn with {n_vertices} vertices and {n_faces} faces."
            imgui.text(self.wrap_text(text_0, text_width))
            v_count += n_vertices
            f_count += n_faces
            p_count += n_particles
        for ls in lss:
            text_0 = f"- LineString called: '{ls.name}' has {len(ls.vertices)} points."
            imgui.text(self.wrap_text(text_0, text_width))
            v_count += ls.n_vertices
            l_count += ls.n_lines

        imgui.text(f"----------------------------------------")
        imgui.text("Visualisation stats:")
        if v_count > 0:
            imgui.text(f"Total vertex count: {v_count}")
        if f_count > 0:
            imgui.text(f"Total face count: {f_count}")
        if p_count > 0:
            imgui.text(f"Total particle count: {p_count}")
        if l_count > 0:
            imgui.text(f"Total line count: {l_count}")

        imgui.end_child()

    def _draw_model_data(self, model: GlModel, text_width: int) -> None:
        imgui.begin_child("ModelData", 0, 250, border=True)
        imgui.text("SELECTED OBJECT DATA:")
        if model.guip.picked_id != -1:
            text_0 = "- id: " + str(model.guip.picked_id)
            imgui.text(self.wrap_text(text_0, text_width))
            text_1 = "- uuid: " + str(model.guip.picked_uuid)
            imgui.text(self.wrap_text(text_1, text_width))
            text_2 = "- mesh: " + str(model.guip.picked_metadata)
            imgui.text(self.wrap_text(text_2, text_width))
            text_3 = "- center: " + str(model.guip.picked_cp)
            imgui.text(self.wrap_text(text_3, text_width))
            text_4 = "- size: " + str(model.guip.picked_size)
            imgui.text(self.wrap_text(text_4, text_width))

        imgui.end_child()

    def _draw_fps(self, guip: GuiParametersGlobal) -> None:
        """Draw GUI elements for adjusting appearance settings like background color."""
        imgui.text("FPS: " + str(guip.fps))

    def wrap_text(self, text, width):
        lines = []
        current_line = ""
        words = text.split()
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                if current_line:
                    current_line += " "
                current_line += word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return "\n".join(lines)
