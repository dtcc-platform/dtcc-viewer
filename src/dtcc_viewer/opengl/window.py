import glfw
import imgui
import math
import numpy as np
from OpenGL.GL import *
from imgui.integrations.glfw import GlfwRenderer
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.parameters import GuiParametersGlobal
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.gl_points import GlPoints
from dtcc_viewer.opengl.gl_lines import GlLines
from dtcc_viewer.opengl.gl_raster import GlRaster
from dtcc_viewer.opengl.gl_object import GlObject
from dtcc_viewer.opengl.gl_grid import GlGrid
from dtcc_viewer.opengl.gl_axes import GlAxes
from dtcc_viewer.opengl.gl_model import GlModel
from dtcc_viewer.opengl.gl_mesh import GlMesh
from dtcc_viewer.opengl.gl_quad import GlQuad
from dtcc_viewer.opengl.scene import Scene
from dtcc_viewer.opengl.gui import Gui

from dtcc_viewer.opengl.wrp_bounds import BoundsWrapper
from dtcc_viewer.opengl.wrp_lines import LinesWrapper
from dtcc_viewer.opengl.wrp_object import ObjectWrapper
from dtcc_viewer.opengl.wrp_geometries import GeometriesWrapper
from dtcc_viewer.opengl.wrp_city import CityWrapper
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.wrp_grid import GridWrapper, VolumeGridWrapper
from dtcc_viewer.opengl.wrp_linestring import LineStringWrapper, MultiLineStringWrapper
from dtcc_viewer.opengl.wrp_pointcloud import PointCloudWrapper
from dtcc_viewer.opengl.wrp_surface import SurfaceWrapper, MultiSurfaceWrapper
from dtcc_viewer.opengl.wrp_raster import RasterWrapper, MultiRasterWrapper
from dtcc_viewer.opengl.wrp_building import BuildingWrapper
from dtcc_viewer.opengl.wrp_volume_mesh import VolumeMeshWrapper
from dtcc_viewer.opengl.wrp_roadnetwork import RoadNetworkWrapper


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
    gl_axes: GlAxes
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
        """Preprocess the scene model.

        This method processes the scene objects and prepares them for rendering.
        It converts scene wrappers into OpenGL objects and sets up the rendering model.

        Parameters
        ----------
        scene : Scene
            The scene containing objects to be preprocessed.
        """
        self.gl_objects = []

        scene.offset_mesh_part_ids()

        info("Preprocessing scene objects...")
        info(f"Scene has {len(scene.wrappers)} objects.")

        for wrapper in scene.wrappers:
            if isinstance(wrapper, ObjectWrapper):
                if wrapper.mesh_wrp_1 is not None:
                    self.gl_objects.append(GlMesh(wrapper.mesh_wrp_1))
                if wrapper.mesh_wrp_2 is not None:
                    self.gl_objects.append(GlMesh(wrapper.mesh_wrp_2))
                if wrapper.lss_wrp is not None:
                    self.gl_objects.append(GlLines(wrapper.lss_wrp))
                if wrapper.pc_wrp is not None:
                    self.gl_objects.append(GlPoints(wrapper.pc_wrp))

            elif isinstance(wrapper, CityWrapper):
                if wrapper.mesh_bld is not None:
                    self.gl_objects.append(GlMesh(wrapper.mesh_bld))
                if wrapper.mesh_ter is not None:
                    self.gl_objects.append(GlMesh(wrapper.mesh_ter))
                for grid_wrp in wrapper.grid_wrps:
                    self.gl_objects.append(GlLines(grid_wrp.lines_wrp))
                for vgrid_wrp in wrapper.vgrid_wrps:
                    self.gl_objects.append(GlLines(vgrid_wrp.lines_wrp))
                for pc_wrp in wrapper.pc_wrps:
                    self.gl_objects.append(GlPoints(pc_wrp))

            elif isinstance(wrapper, GeometriesWrapper):
                for mesh_w in wrapper.mesh_wrps:
                    self.gl_objects.append(GlMesh(mesh_w))
                for srf in wrapper.srf_wrps:
                    self.gl_objects.append(GlMesh(srf.mesh_wrp))
                for ms in wrapper.ms_wrps:
                    self.gl_objects.append(GlMesh(ms.mesh_wrp))
                for mls_wrp in wrapper.mls_wrps:
                    self.gl_objects.append(GlLines(mls_wrp))
                for ls_wrp in wrapper.lss_wrps:
                    self.gl_objects.append(GlLines(ls_wrp))
                for bnds_wrp in wrapper.bnds_wrps:
                    self.gl_objects.append(GlLines(bnds_wrp.ls_wrp))
                for pc in wrapper.pc_wrps:
                    self.gl_objects.append(GlPoints(pc))
                for mesh_wrp in wrapper.vmesh_wrps:
                    self.gl_objects.append(GlMesh(mesh_wrp.mesh_vol_wrp))
                    self.gl_objects.append(GlMesh(mesh_wrp.mesh_env_wrp))
                for grd_wrp in wrapper.grd_wrps:
                    self.gl_objects.append(GlLines(grd_wrp.lines_wrp, False))
                for vgrd_wrp in wrapper.vgrd_wrps:
                    self.gl_objects.append(GlLines(vgrd_wrp.lines_wrp, False))

            elif isinstance(wrapper, MeshWrapper):
                self.gl_objects.append(GlMesh(wrapper))

            elif isinstance(wrapper, SurfaceWrapper):
                self.gl_objects.append(GlMesh(wrapper.mesh_wrp))

            elif isinstance(wrapper, MultiSurfaceWrapper):
                self.gl_objects.append(GlMesh(wrapper.mesh_wrp))

            elif isinstance(wrapper, BuildingWrapper):
                self.gl_objects.append(GlMesh(wrapper.mesh_wrp))

            elif isinstance(wrapper, MultiLineStringWrapper):
                self.gl_objects.append(GlLines(wrapper))

            elif isinstance(wrapper, LineStringWrapper):
                self.gl_objects.append(GlLines(wrapper))

            elif isinstance(wrapper, LinesWrapper):
                self.gl_objects.append(GlLines(wrapper))

            elif isinstance(wrapper, RoadNetworkWrapper):
                self.gl_objects.append(GlLines(wrapper.mls_wrp))

            elif isinstance(wrapper, BoundsWrapper):
                self.gl_objects.append(GlLines(wrapper.ls_wrp))

            elif isinstance(wrapper, PointCloudWrapper):
                self.gl_objects.append(GlPoints(wrapper))

            elif isinstance(wrapper, GridWrapper):
                if wrapper.lines_wrp is not None:
                    self.gl_objects.append(GlLines(wrapper.lines_wrp, False))

            elif isinstance(wrapper, VolumeGridWrapper):
                if wrapper.lines_wrp is not None:
                    self.gl_objects.append(GlLines(wrapper.lines_wrp, False))

            elif isinstance(wrapper, VolumeMeshWrapper):
                if wrapper.mesh_vol_wrp is not None:
                    self.gl_objects.append(GlMesh(wrapper.mesh_vol_wrp))
                if wrapper.mesh_env_wrp is not None:
                    self.gl_objects.append(GlMesh(wrapper.mesh_env_wrp))

            elif isinstance(wrapper, RasterWrapper):
                self.gl_objects.append(GlRaster(wrapper))

            elif isinstance(wrapper, MultiRasterWrapper):
                for raster_wrp in wrapper.raster_wrappers:
                    self.gl_objects.append(GlRaster(raster_wrp))
            else:
                warning(f"Wrapper type {type(wrapper)} not supported!")

        if len(self.gl_objects) == 0:
            warning("No meshes, points or lines added to scene!")
            return False

        # Create model from meshes
        self.model = GlModel(self.gl_objects, scene.bb)

        # Initialise camera base on bounding box size
        self.action.initialise_camera(scene.bb)

        # Create opengl data for all the objects
        if not self.model.preprocess():
            warning("GLModel preprocessing failed!")

        # Create picking frame buffer object
        self.model.create_picking_fbo(self.action)

        # Create grid and coordinate axes
        self.gl_grid = GlGrid(scene.bb)
        self.gl_axes = GlAxes(1.0, scene.bb.zmin)

        return True

    def render(self, scene: Scene):
        """Render single or multiple objects.

        This method renders multiple meshes, line collections and and point clouds in
        the window. It updates the rendering loop, handles user interactions, and
        displays the GUI elements for each rendered object.

        Parameters
        ----------
            scene: Scene
                The scene with objects to be rendered.
        """

        if scene.wrappers is None or len(scene.wrappers) == 0:
            warning("Scene has no objects to render. Viewer aborted!")
            return False

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

            color = self.action.gguip.color
            glClearColor(color[0], color[1], color[2], color[3])

            # Enable clipping planes
            self._clipping_planes()

            # Check if the mouse is on the GUI or on the model
            self.action.set_mouse_on_gui(self.io.want_capture_mouse)

            # Update camera for selected objects
            if self.action.update_zoom_selected:
                self.model.zoom_selected(self.action)

            # Update camera for selected view
            if self.action.gguip.update_camera:
                self.action.update_view()

            # True if the user has clicked on the model
            if self.action.picking:
                self.model.evaluate_picking(self.action)

            # Render the model
            if self.model.guip.show:
                self.model.render(self.action)

            # Draw grid
            self.gl_grid.render(self.action)

            # Draw axes
            self.gl_axes.render(self.action)

            # Render the GUI
            self.gui.render(self.model, self.impl, self.action.gguip)

            self.action.gguip.calc_fps()

            glfw.swap_buffers(self.window)

        glfw.terminate()

    def _window_resize_callback(self, window, width, height):
        """Callback for window resize events.

        This method is a callback function that gets called when the window is resized.
        It updates the viewport size and interaction parameters.
        """

        self._update_window_framebuffer_size()
        self.model.create_picking_fbo(self.action)

    def _update_window_framebuffer_size(self):
        """Update the window framebuffer size.

        This method updates the size of the framebuffer and the viewport, when the user
        resizes the window and adjusts the action parameters accordingly.
        """
        fbuf_size = glfw.get_framebuffer_size(self.window)
        win_size = glfw.get_window_size(self.window)
        fb_width = fbuf_size[0]
        fb_height = fbuf_size[1]
        win_width = win_size[0]
        win_height = win_size[1]
        glViewport(0, 0, fb_width, fb_height)
        self.action.update_window_size(fb_width, fb_height, win_width, win_height)

    def _clipping_planes(self):
        """Enable or disable clipping planes based on GUI parameters.

        This method enables or disables the clipping planes based on the settings
        specified in the GUI parameters.
        """
        if self.action.gguip.clip_bool[0]:
            glEnable(GL_CLIP_DISTANCE0)
        else:
            glDisable(GL_CLIP_DISTANCE0)

        if self.action.gguip.clip_bool[1]:
            glEnable(GL_CLIP_DISTANCE1)
        else:
            glDisable(GL_CLIP_DISTANCE1)

        if self.action.gguip.clip_bool[2]:
            glEnable(GL_CLIP_DISTANCE2)
        else:
            glDisable(GL_CLIP_DISTANCE2)

        # Grid clipping planes
        if self.action.gguip.show_grid:
            glEnable(GL_CLIP_DISTANCE3)
            glEnable(GL_CLIP_DISTANCE4)
            glEnable(GL_CLIP_DISTANCE5)
            glEnable(GL_CLIP_DISTANCE6)
        else:
            glDisable(GL_CLIP_DISTANCE3)
            glDisable(GL_CLIP_DISTANCE4)
            glDisable(GL_CLIP_DISTANCE5)
            glDisable(GL_CLIP_DISTANCE6)
