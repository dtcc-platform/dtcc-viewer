import glfw
import imgui
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.point_cloud_gl import PointCloudGL
from dtcc_viewer.opengl_viewer.mesh_gl import MeshGL
from dtcc_viewer.opengl_viewer.utils import MeshShading

from dtcc_viewer.opengl_viewer.gui import GuiParameters, Gui
from imgui.integrations.glfw import GlfwRenderer

from dtcc_viewer.opengl_viewer.mesh_data import MeshData
from dtcc_viewer.opengl_viewer.point_cloud_data import PointCloudData

class Window:

    meshes: list[MeshGL]
    point_clouds: list[PointCloudGL]
    mesh: MeshGL
    pc: PointCloudGL
    gui: Gui
    guip: GuiParameters
    width: int
    height: int
    interaction: Interaction
    impl: GlfwRenderer
    fps: int
    time: float
    time_acum: float

    def __init__(self, width:int, height:int):
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
        self.window = glfw.create_window(self.width, self.height, "OpenGL Window", None, None)      # Create window

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
        glfw.set_mouse_button_callback(self.window, self.interaction.mouse_input_callback)
        glfw.set_scroll_callback(self.window, self.interaction.scroll_input_callback)

        self.time, self.time_acum, self.fps = 0.0, 0.0, 0

    def render_multi(self, mesh_data_list:list[MeshData], pc_data_list:list[PointCloudData]):
        
        self.meshes = []
        self.point_clouds = []

        for mesh in mesh_data_list:
            mesh_gl = MeshGL(mesh.vertices, mesh.face_indices, mesh.edge_indices)
            self.meshes.append(mesh_gl)
        
        for pc in pc_data_list:
            pc_gl = PointCloudGL(0.1, 10, pc.points, pc.colors)
            self.point_clouds.append(pc_gl)
        
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(self.guip.color[0], self.guip.color[1], self.guip.color[2], self.guip.color[3])

            self._render_point_clouds(self.guip)
            self._render_meshes(self.guip)
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_pc_gui(self.guip)
            self.gui.draw_mesh_gui(self.guip)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)
            glfw.swap_buffers(self.window)

        glfw.terminate()   
        

    def render_point_cloud(self, points:np.ndarray, colors:np.ndarray):
        self.pc = PointCloudGL(0.1, 10, points, colors)
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(self.guip.color[0], self.guip.color[1], self.guip.color[2], self.guip.color[3])

            self._render_point_cloud(self.guip)
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_pc_gui(self.guip)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)
            glfw.swap_buffers(self.window)

        glfw.terminate()       
    
    def render_mesh(self, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray = None): 
        self.mesh = MeshGL(vertices, faces, edges)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(self.guip.color[0], self.guip.color[1], self.guip.color[2], self.guip.color[3])

            self._render_mesh(self.guip)
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_mesh_gui(self.guip)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)
            glfw.swap_buffers(self.window)        
    
    def render_pc_and_mesh(self, points:np.ndarray, colors:np.ndarray, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray = None ):
        self.pc = PointCloudGL(0.2, 10, points, colors)        
        self.mesh = MeshGL(vertices, faces, edges)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(self.guip.color[0], self.guip.color[1], self.guip.color[2], self.guip.color[3])

            self._render_mesh(self.guip)
            self._render_point_cloud(self.guip)
            self._fps_calculations()

            self.gui.init_draw(self.impl)
            self.gui.draw_pc_gui(self.guip)
            self.gui.draw_mesh_gui(self.guip)
            self.gui.draw_apperance_gui(self.guip)
            self.gui.end_draw(self.impl)

            self.interaction.set_mouse_on_gui(self.io.want_capture_mouse)

            glfw.swap_buffers(self.window)

    def render_empty(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(self.guip.color[0], self.guip.color[1], self.guip.color[2], self.guip.color[3])
        
            self.gui.init_draw(self.impl)
            self.gui.draw_example_gui(self.guip)
            self.gui.end_draw(self.impl)

            glfw.swap_buffers(self.window)      

    def _render_point_cloud(self, guip:GuiParameters):
        if guip.show_pc:    
            self.pc.render(self.interaction, guip)    

    def _render_point_clouds(self, guip:GuiParameters):
        for pc in self.point_clouds:
            if guip.show_pc:    
                pc.render(self.interaction, guip)    
        
    def _render_mesh(self, guip:GuiParameters):    
        if guip.show_mesh:
            if guip.combo_selected_index == 0:
                self.mesh.render_lines(self.interaction, guip)
            elif guip.combo_selected_index == 1:
                self.mesh.render_basic(self.interaction, guip)
            elif guip.combo_selected_index == 2:
                    self.mesh.render_fancy(self.interaction, guip)
            elif guip.combo_selected_index == 3:
                    self.mesh.render_fancy_shadows(self.interaction, guip)

    def _render_meshes(self, guip:GuiParameters):    
        for mesh in self.meshes:    
            if guip.show_mesh:
                if guip.combo_selected_index == 0:
                    mesh.render_lines(self.interaction, guip)
                elif guip.combo_selected_index == 1:
                    mesh.render_basic(self.interaction, guip)
                elif guip.combo_selected_index == 2:
                    mesh.render_fancy(self.interaction, guip)
                elif guip.combo_selected_index == 3:
                    mesh.render_fancy_shadows(self.interaction, guip)

    def _fps_calculations(self, print_results = True):
        new_time = glfw.get_time()
        time_passed = new_time - self.time
        self.time = new_time
        self.time_acum += time_passed
        self.fps += 1

        if(self.time_acum > 1):
            self.time_acum = 0
            if(print_results):
                print("FPS:" + str(self.fps))
            self.fps = 0
   
    def _window_resize_callback(self, window, width, height):
        fb_size = glfw.get_framebuffer_size(self.window)
        width = fb_size[0]
        height = fb_size[1]
        glViewport(0, 0, width, height)
        self.interaction.update_window_size(width, height)
         
