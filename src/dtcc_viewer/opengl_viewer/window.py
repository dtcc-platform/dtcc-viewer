import glfw
import imgui
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from imgui.integrations.glfw import GlfwRenderer
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl_viewer.interaction import Action
from dtcc_viewer.opengl_viewer.pointcloud_gl import PointCloudGL
from dtcc_viewer.opengl_viewer.mesh_gl import MeshGL
from dtcc_viewer.opengl_viewer.model_gl import ModelGL
from dtcc_viewer.opengl_viewer.utils import Shading
from dtcc_viewer.opengl_viewer.linestring_gl import LineStringGL
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper
from dtcc_viewer.opengl_viewer.pointcloud_wrapper import PointCloudWrapper
from dtcc_viewer.opengl_viewer.scene import Scene
from dtcc_viewer.opengl_viewer.gui import Gui
from dtcc_viewer.opengl_viewer.parameters import GuiParameters


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
    meshes : list[MeshGL]
        List of MeshGL objects representing rendered meshes.
    point_clouds : list[PointCloudGL]
        List of PointCloudGL objects representing rendered point clouds.
    mesh : MeshGL
        The currently displayed MeshGL object.
    pc : PointCloudGL
        The currently displayed PointCloudGL object.
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

    meshes: list[MeshGL]
    pointclouds: list[PointCloudGL]
    roadnetworks: list[LineStringGL]
    model: ModelGL
    mesh: MeshGL
    pc: PointCloudGL
    gui: Gui
    guip: GuiParameters  # Gui parameters common for the whole window
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
        self.guip = GuiParameters()
        self.io = imgui.get_io()

        if not glfw.init():
            raise Exception("glfw can not be initialised!")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(
            self.win_width, self.win_height, "OpenGL Window", None, None
        )  # Create window

        if not self.window:
            glfw.terminate()
            raise Exception("glfw window can not be created!")

        glfw.set_window_pos(self.window, 400, 200)

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

        self.time, self.time_acum, self.fps = 0.0, 0.0, 0

        self._update_window_framebuffer_size()

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

        self.meshes = []
        self.pointclouds = []
        self.roadnetworks = []
        scene.preprocess_drawing()

        for city in scene.city_wrappers:
            if city.building_mw is not None:
                mesh_gl_bld = MeshGL(city.building_mw)
                self.meshes.append(mesh_gl_bld)
            if city.terrain_mw is not None:
                mesh_gl_ter = MeshGL(city.terrain_mw)
                self.meshes.append(mesh_gl_ter)

        for mesh in scene.mesh_wrappers:
            mesh_gl = MeshGL(mesh)
            self.meshes.append(mesh_gl)

        for pc in scene.pcs_wrappers:
            pc_gl = PointCloudGL(pc)
            self.pointclouds.append(pc_gl)

        for rn in scene.rnd_wrappers:
            rn_gl = LineStringGL(rn)
            self.roadnetworks.append(rn_gl)

        # Create model from meshes
        self.model = ModelGL(self.meshes, self.pointclouds, self.roadnetworks, scene.bb)

        self.model.create_picking_fbo(self.action)

        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

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

            # True if the user has clicked on the GUI
            if self.action.picking:
                self.model.evaluate_picking(self.action)

            # Render the model
            self.model.render(self.action, self.guip)

            # Render the GUI
            self.gui.render_gui(self.model, self.impl, self.guip)

            self._calc_fps()

            glfw.swap_buffers(self.window)

        glfw.terminate()

    def _render_point_clouds(self):
        """Render all the point clouds in the window.

        This method renders all the point cloud objects in the window using OpenGL.
        """
        for pc in self.pointclouds:
            if pc.guip.show:
                pc.render(self.action, self.guip)

    def _render_road_networks(self):
        """Render all the road networks in the window."""
        for rn in self.roadnetworks:
            mguip = rn.guip
            if mguip.show:
                rn.render(self.action, self.guip)

    def _calc_fps(self, print_results=True):
        """Perform FPS calculations.

        This method calculates the frames per second (FPS) for the rendering loop.
        It updates the FPS count and prints the results if specified.

        Parameters
        ----------
        print_results : bool, optional
            Whether to print the calculated FPS results (default is True).
        """

        new_time = glfw.get_time()
        time_passed = new_time - self.time
        self.time = new_time
        self.time_acum += time_passed
        self.fps += 1

        if self.time_acum > 1:
            self.time_acum = 0
            if print_results:
                info(f"FPS: {self.fps}")
            self.fps = 0

    def _window_resize_callback(self, window, width, height):
        """Callback for window resize events.

        This method is a callback function that gets called when the window is resized.
        It updates the viewport size and interaction parameters.

        Parameters
        ----------
        window : int
            The GLFW window.
        width : int
            The new width of the window.
        height : int
            The new height of the window.
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
        info(f"Window size: {win_width} x {win_height}")
        info(f"Frame bufffer size: {fb_width} x {fb_height}")

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
