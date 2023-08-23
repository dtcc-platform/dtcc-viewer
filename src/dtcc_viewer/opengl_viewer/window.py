import glfw
import imgui
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.point_cloud_gl import PointCloudGL
from dtcc_viewer.opengl_viewer.mesh_gl import MeshGL
from dtcc_viewer.opengl_viewer.utils import MeshShading

from dtcc_viewer.opengl_viewer.gui import GuiParameters, Gui, GuiParametersExample
from imgui.integrations.glfw import GlfwRenderer

from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData


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
    point_clouds: list[PointCloudGL]
    mesh: MeshGL
    pc: PointCloudGL
    gui: Gui
    guip: GuiParameters  # Gui parameters common for the whole window
    width: int
    height: int
    interaction: Interaction
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
        self.width = width
        self.height = height
        self.interaction = Interaction(width, height)

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
            self.width, self.height, "OpenGL Window", None, None
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
        glfw.set_cursor_pos_callback(self.window, self.interaction.mouse_look_callback)
        glfw.set_key_callback(self.window, self.interaction.key_input_callback)
        glfw.set_mouse_button_callback(
            self.window, self.interaction.mouse_input_callback
        )
        glfw.set_scroll_callback(self.window, self.interaction.scroll_input_callback)

        self.time, self.time_acum, self.fps = 0.0, 0.0, 0

    def render_multi(
        self, mesh_data_list: list[MeshData], pc_data_list: list[PointCloudData]
    ):
        """Render multiple MeshData and PointCloudData objects.

        This method renders multiple meshes and point clouds in the window.
        It updates the rendering loop, handles user interactions, and displays
        the GUI elements for each rendered object.

        Parameters
        ----------
        mesh_data_list : list[MeshData]
            List of MeshData objects to render.
        pc_data_list : list[PointCloudData]
            List of PointCloudData objects to render.
        """

        self.meshes = []
        self.point_clouds = []

        for mesh in mesh_data_list:
            mesh_gl = MeshGL(
                mesh.name, mesh.vertices, mesh.face_indices, mesh.edge_indices
            )
            self.meshes.append(mesh_gl)

        for pc in pc_data_list:
            pc_gl = PointCloudGL(pc.name, 0.2, pc.points, pc.colors)
            self.point_clouds.append(pc_gl)

        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(
                self.guip.color[0],
                self.guip.color[1],
                self.guip.color[2],
                self.guip.color[3],
            )

            self._render_point_clouds()
            self._render_meshes()
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            # add individual ui for each point cloud
            for i, pc in enumerate(self.point_clouds):
                self.gui.draw_pc_gui(pc.guip, i)
                self.gui.draw_separator()

            for i, mesh in enumerate(self.meshes):
                self.gui.draw_mesh_gui(mesh.guip, i)
                self.gui.draw_separator()

            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)
            glfw.swap_buffers(self.window)

        glfw.terminate()

    def render_point_cloud(self, pc_data_obj: PointCloudData):
        """Render a single PointCloudData object.

        This method renders a single point cloud object in the window. It updates
        the rendering loop, handles user interactions, and displays the GUI elements
        for the rendered point cloud.

        Parameters
        ----------
        pc_data_obj : PointCloudData
            The PointCloudData object to render.
        """

        self.pc = PointCloudGL(
            pc_data_obj.name, 0.2, pc_data_obj.points, pc_data_obj.colors
        )
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(
                self.guip.color[0],
                self.guip.color[1],
                self.guip.color[2],
                self.guip.color[3],
            )

            self._render_point_cloud()
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_pc_gui(self.pc.guip, 1)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)
            glfw.swap_buffers(self.window)

        glfw.terminate()

    def render_mesh(self, mesh_data_obj: MeshData):
        """Render a single MeshData object.

        This method renders a single mesh object in the window. It updates the rendering
        loop, handles user interactions, and displays the GUI elements for the rendered mesh.

        Parameters
        ----------
        mesh_data_obj : MeshData
            The MeshData object to render.
        """

        self.mesh = MeshGL(
            mesh_data_obj.name,
            mesh_data_obj.vertices,
            mesh_data_obj.face_indices,
            mesh_data_obj.edge_indices,
        )
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(
                self.guip.color[0],
                self.guip.color[1],
                self.guip.color[2],
                self.guip.color[3],
            )

            self._render_mesh()
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_mesh_gui(self.mesh.guip, 1)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)
            glfw.swap_buffers(self.window)

    def render_pc_and_mesh(self, pc_data_obj: PointCloudData, mesh_data_obj: MeshData):
        """Render a PointCloudData and a MeshData object.

        This method renders both a point cloud and a mesh object in the window. It updates
        the rendering loop, handles user interactions, and displays the GUI elements for both
        the rendered point cloud and mesh.

        Parameters
        ----------
        pc_data_obj : PointCloudData
            The PointCloudData object to render.
        mesh_data_obj : MeshData
            The MeshData object to render.
        """
        self.pc = PointCloudGL(
            pc_data_obj.name, 0.2, pc_data_obj.points, pc_data_obj.colors
        )
        self.mesh = MeshGL(
            mesh_data_obj.name,
            mesh_data_obj.vertices,
            mesh_data_obj.face_indices,
            mesh_data_obj.edge_indices,
        )
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(
                self.guip.color[0],
                self.guip.color[1],
                self.guip.color[2],
                self.guip.color[3],
            )

            self._render_mesh()
            self._render_point_cloud()
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_pc_gui(self.pc.guip, 1)
            self.gui.draw_mesh_gui(self.mesh.guip, 1)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)

            glfw.swap_buffers(self.window)

    def render_empty(self):
        """Render an empty window with an example GUI.

        This method renders an empty window and displays an example GUI for demonstration
        purposes. It updates the rendering loop and handles user interactions.
        """
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        guip_example = GuiParametersExample()

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(
                guip_example.color[0],
                guip_example.color[1],
                guip_example.color[2],
                guip_example.color[3],
            )

            self.gui.init_draw(self.impl)
            self.gui.draw_example_gui(guip_example)
            self.gui.end_draw(self.impl)

            glfw.swap_buffers(self.window)

    def _render_point_cloud(self):
        """Render the currently displayed point cloud.

        This method renders the currently displayed point cloud object using OpenGL.
        """
        if self.pc.guip.show:
            self.pc.render(self.interaction)

    def _render_point_clouds(self):
        """Render all the point clouds in the window.

        This method renders all the point cloud objects in the window using OpenGL.
        """
        for pc in self.point_clouds:
            if pc.guip.show:
                pc.render(self.interaction)

    def _render_mesh(self):
        """Render the currently displayed mesh.

        This method renders the currently displayed mesh object using OpenGL.
        """
        mguip = self.mesh.guip
        if mguip.show:
            if mguip.mesh_shading == 0:
                self.mesh.render_lines(self.interaction)
            elif mguip.mesh_shading == 1:
                self.mesh.render_ambient(self.interaction)
            elif mguip.mesh_shading == 2:
                self.mesh.render_diffuse(self.interaction)
            elif mguip.mesh_shading == 3:
                self.mesh.render_shadows(self.interaction)

    def _render_meshes(self):
        """Render all the meshes in the window.

        This method renders all the mesh objects in the window using OpenGL.
        """
        for mesh in self.meshes:
            mguip = mesh.guip
            if mguip.show:
                if mguip.mesh_shading == MeshShading.wireframe:
                    mesh.render_lines(self.interaction)
                elif mguip.mesh_shading == MeshShading.shaded_ambient:
                    mesh.render_ambient(self.interaction)
                elif mguip.mesh_shading == MeshShading.shaded_diffuse:
                    mesh.render_diffuse(self.interaction)
                elif mguip.mesh_shading == MeshShading.shaded_shadows:
                    mesh.render_shadows(self.interaction)

    def _fps_calculations(self, print_results=True):
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
                print("FPS:" + str(self.fps))
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
        fb_size = glfw.get_framebuffer_size(self.window)
        width = fb_size[0]
        height = fb_size[1]
        glViewport(0, 0, width, height)
        self.interaction.update_window_size(width, height)
