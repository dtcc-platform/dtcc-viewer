import glfw
import imgui
import math
import numpy as np
from OpenGL.GL import *
from imgui.integrations.glfw import GlfwRenderer
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.parameters import GuiParametersGlobal
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.gl_pointcloud import GlPointCloud
from dtcc_viewer.opengl.gl_linestring import GlLineString
from dtcc_viewer.opengl.gl_raster import GlRaster
from dtcc_viewer.opengl.gl_object import GlObject
from dtcc_viewer.opengl.gl_grid import GlGrid
from dtcc_viewer.opengl.gl_model import GlModel
from dtcc_viewer.opengl.gl_mesh import GlMesh
from dtcc_viewer.opengl.gl_quad import GlQuad
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.gui import Gui


class Window:
    """OpenGL Rendering Window.

    This class represents an OpenGL rendering window with interactive controls
    for visualizing meshes and point clouds. The window provides methods for
    rendering various types of data and handling user interactions.

    Parameters
    ----------
    width : int
        The width of the window in pixels.
    height : int
        The height of the window in pixels.

    Attributes
    ----------
    gl_objects : list[GlObject]
        List of GlObject instances to be rendered in the window.
    gui : Gui
        An instance of the GUI for interacting with the rendering.
    guip : GuiParameters
        GUI parameters common for the entire window.
    width : int
        The width of the window in pixels.
    height : int
        The height of the window in pixels.
    interaction : Interaction
        An Interaction object managing user input interactions.
    impl : GlfwRenderer
        GlfwRenderer instance for rendering ImGui GUI.
    fps : int
        Frames per second for the rendering loop.
    time : float
        Current time in seconds.
    time_acum : float
        Accumulated time for FPS calculation.
    """

    gl_objects: list[GlObject]
    model: GlModel
    gl_grid: GlGrid
    gl_quad: GlQuad
    gui: Gui
    guip: GuiParametersGlobal  # Gui parameters common for the whole window
    win_width: int
    win_height: int
    action: Action
    impl: GlfwRenderer
    fps: int
    time: float
    time_acum: float

    def __init__(self, width: int, height: int):
        """Initialize the OpenGL rendering window and setting up default parameters.

        Parameters
        ----------
        width : int
            The width of the window in pixels.
        height : int
            The height of the window in pixels.
        """
        self.win_width = width
        self.win_height = height
        self.action = Action(width, height)

        imgui.create_context()
        self.gui = Gui()
        self.guip = GuiParametersGlobal()
        self.io = imgui.get_io()

        if not glfw.init():
            raise Exception("glfw can not be initialised!")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(
            self.win_width, self.win_height, "DTCC Viewer", None, None
        )  # Create window

        if not self.window:
            glfw.terminate()
            raise Exception("glfw window can not be created!")

        # Calculate screen position for window
        primary_monitor = glfw.get_primary_monitor()
        mode = glfw.get_video_mode(primary_monitor)

        x_pos = (mode.size.width - self.win_width) // 2
        y_pos = (mode.size.height - self.win_height) // 2

        glfw.set_window_pos(self.window, x_pos, y_pos)

        # Calls can be made after the contex is made current
        glfw.make_context_current(self.window)

        # Callback should be called after the impl has been registered
        self.impl = GlfwRenderer(self.window)

        # Register callback functions to enable mouse and keyboard interaction
        glfw.set_window_size_callback(self.window, self._window_resize_callback)
        glfw.set_cursor_pos_callback(self.window, self.action.mouse_look_callback)
        glfw.set_key_callback(self.window, self.action.key_input_callback)
        glfw.set_mouse_button_callback(self.window, self.action.mouse_input_callback)
        glfw.set_scroll_callback(self.window, self.action.scroll_input_callback)

        self._update_window_framebuffer_size()

    def _preprocess_model(self, scene: Scene):
        self.gl_objects = []

        for obj in scene.obj_wrappers:
            if obj.mesh_wrp_1 is not None:
                mesh_gl = GlMesh(obj.mesh_wrp_1)
                self.gl_objects.append(mesh_gl)
            if obj.mesh_wrp_2 is not None:
                mesh_gl = GlMesh(obj.mesh_wrp_2)
                self.gl_objects.append(mesh_gl)
            if obj.ls_wrapper is not None:
                lss_gl = GlLineString(obj.ls_wrapper)
                self.gl_objects.append(lss_gl)

        for city in scene.city_wrappers:
            if city.building_mw is not None:
                mesh_gl_bld = GlMesh(city.building_mw)
                self.gl_objects.append(mesh_gl_bld)
            if city.terrain_mw is not None:
                mesh_gl_ter = GlMesh(city.terrain_mw)
                self.gl_objects.append(mesh_gl_ter)

        for building in scene.bld_wrappers:
            mesh_gl = GlMesh(building.building_mw)
            self.gl_objects.append(mesh_gl)

        for mesh in scene.mesh_wrappers:
            mesh_gl = GlMesh(mesh)
            self.gl_objects.append(mesh_gl)

        for pc in scene.pcs_wrappers:
            pc_gl = GlPointCloud(pc)
            self.gl_objects.append(pc_gl)

        for rn in scene.rnd_wrappers:
            rn_gl = GlLineString(rn)
            self.gl_objects.append(rn_gl)

        for lss in scene.lss_wrappers:
            lss_gl = GlLineString(lss)
            self.gl_objects.append(lss_gl)

        for rst in scene.rst_wrappers:
            txq_gl = GlRaster(rst)
            self.gl_objects.append(txq_gl)

        for mrsr in scene.mrst_wrappers:
            for rst in mrsr.raster_wrappers:
                txq_gl = GlRaster(rst)
                self.gl_objects.append(txq_gl)

        if len(self.gl_objects) == 0:
            warning("No meshes or point clouds or line strings found in the scene!")
            return False

        # Create model from meshes
        self.model = GlModel(self.gl_objects, scene.bb)

        size_scene = math.sqrt(pow(scene.bb.xdom, 2) + pow(scene.bb.ydom, 2))
        self.action.set_camera_distance_to_target(1.5 * size_scene)
        self.action.save_init_camera()

        if not self.model.preprocess():
            warning("GLModel preprocessing failed!")

        self.model.create_picking_fbo(self.action)

        # Create grid
        self.gl_grid = GlGrid(scene.bb, self.guip)

        self.gl_quad = GlQuad(500)

        return True

    def render(self, scene: Scene):
        """Render single or multiple MeshData and/or PointCloudData objects.

        This method renders multiple meshes and point clouds in the window.
        It updates the rendering loop, handles user interactions, and displays
        the GUI elements for each rendered object.

        Parameters
        ----------
            scene: Scene
                The scene with objects to be rendered.
        """

        if not scene.preprocess_drawing():
            warning("Scene preprocessing failed. Viewer aborted!")
            glfw.terminate()
            return False

        if not self._preprocess_model(scene):
            warning("Model preprocessing failed. Viewer aborted!")
            glfw.terminate()
            return False

        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glDepthFunc(GL_LESS)

        info(f"Rendering scene...")

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            color = self.guip.color
            glClearColor(color[0], color[1], color[2], color[3])

            # Enable clipping planes
            self._clipping_planes()

            # Check if the mouse is on the GUI or on the model
            self.action.set_mouse_on_gui(self.io.want_capture_mouse)

            # Update camera for selected objects
            if self.action.zoom_selected:
                self.model.zoom_selected(self.action, self.guip)

            # Update camera for selected view
            if self.guip.update_camera:
                self.action.update_view(self.guip)

            # True if the user has clicked on the GUI
            if self.action.picking:
                self.model.evaluate_picking(self.action, self.guip)

            # Render the model
            if self.model.guip.show:
                self.model.render(self.action, self.guip)

            # Draw grid
            self.gl_grid.render(self.action, self.guip)

            # Render the GUI
            self.gui.render(self.model, self.impl, self.guip)

            self.guip.calc_fps()

            glfw.swap_buffers(self.window)

        glfw.terminate()

    def _render_point_clouds(self):
        """Render all the point clouds in the window.

        This method renders all the point cloud objects in the window using OpenGL.
        """
        for pc in self.pcs:
            if pc.guip.show:
                pc.render(self.action, self.guip)

    def _render_road_networks(self):
        """Render all the road networks in the window."""
        for rn in self.lss:
            mguip = rn.guip
            if mguip.show:
                rn.render(self.action, self.guip)

    def _window_resize_callback(self, window, width, height):
        """Callback for window resize events.

        This method is a callback function that gets called when the window is resized.
        It updates the viewport size and interaction parameters.
        """

        self._update_window_framebuffer_size()
        self.model.create_picking_fbo(self.action)

    def _update_window_framebuffer_size(self):
        fbuf_size = glfw.get_framebuffer_size(self.window)
        win_size = glfw.get_window_size(self.window)
        fb_width = fbuf_size[0]
        fb_height = fbuf_size[1]
        win_width = win_size[0]
        win_height = win_size[1]
        glViewport(0, 0, fb_width, fb_height)
        self.action.update_window_size(fb_width, fb_height, win_width, win_height)

    def _clipping_planes(self):
        if self.guip.clip_bool[0]:
            glEnable(GL_CLIP_DISTANCE0)
        else:
            glDisable(GL_CLIP_DISTANCE0)

        if self.guip.clip_bool[1]:
            glEnable(GL_CLIP_DISTANCE1)
        else:
            glDisable(GL_CLIP_DISTANCE1)

        if self.guip.clip_bool[2]:
            glEnable(GL_CLIP_DISTANCE2)
        else:
            glDisable(GL_CLIP_DISTANCE2)

        # Grid clipping planes
        if self.guip.show_grid:
            glEnable(GL_CLIP_DISTANCE3)
            glEnable(GL_CLIP_DISTANCE4)
            glEnable(GL_CLIP_DISTANCE5)
            glEnable(GL_CLIP_DISTANCE6)
        else:
            glDisable(GL_CLIP_DISTANCE3)
            glDisable(GL_CLIP_DISTANCE4)
            glDisable(GL_CLIP_DISTANCE5)
            glDisable(GL_CLIP_DISTANCE6)
