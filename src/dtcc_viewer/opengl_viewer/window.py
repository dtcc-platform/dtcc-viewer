import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl_viewer.interaction import Interaction
from dtcc_viewer.opengl_viewer.particles import Particle
from dtcc_viewer.opengl_viewer.mesh import Mesh
from dtcc_viewer.opengl_viewer.mesh_fancy import MeshFancy
from dtcc_viewer.opengl_viewer.mesh_fancy_shadows import MeshShadow
from dtcc_viewer.opengl_viewer.utils import Shading

class Window:

    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height
        self.interaction = Interaction(width, height)

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

        # Register callback functions to enable mouse and keyboard interaction
        glfw.set_window_size_callback(self.window, self._window_resize_callback)
        glfw.set_cursor_pos_callback(self.window, self.interaction.mouse_look_callback)
        glfw.set_key_callback(self.window, self.interaction.key_input_callback)
        glfw.set_mouse_button_callback(self.window, self.interaction.mouse_input_callback)
        glfw.set_scroll_callback(self.window, self.interaction.scroll_input_callback)

        # Calls can be made after the contex is made current
        glfw.make_context_current(self.window)

        self.time, self.time_acum, self.fps = 0.0, 0.0, 0

    def render_particles(self, points:np.ndarray):
        self.particles = Particle(0.1, 10, points)
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.particles.render(self.interaction)
            self._fps_calculations()
            glfw.swap_buffers(self.window)

        glfw.terminate()       
    
    def render_mesh(self, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray = None): 
        self.mesh = Mesh(vertices, faces, edges)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if self.interaction.shading == Shading.shaded:
                self.mesh.render_triangels(self.interaction)
            elif self.interaction.shading == Shading.wireframe:    
                self.mesh.render_lines(self.interaction)

            self._fps_calculations()
            glfw.swap_buffers(self.window)
    
    def render_fancy_mesh(self, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray = None): 
        self.mesh = MeshFancy(vertices, faces, edges)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if self.interaction.shading == Shading.shaded:
                self.mesh.render_triangels(self.interaction)
            elif self.interaction.shading == Shading.wireframe:    
                self.mesh.render_lines(self.interaction)

            self._fps_calculations()
            glfw.swap_buffers(self.window)        
    
    def render_fancy_shadows_mesh(self, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray = None): 
        self.mesh = MeshShadow(vertices, faces, edges)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            self.mesh.render_shadow_map(glfw.get_time())
            self.mesh.render_model_with_shadows(self.interaction)
            
            self._fps_calculations()
            glfw.swap_buffers(self.window)        
    

    def render_particles_and_mesh(self, filename_particles:str, filename_mesh:str):
        self.particles = Particle(0.3, 12, filename_particles)        
        self.mesh = Mesh(filename_mesh)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if self.interaction.shading == Shading.shaded:
                self.mesh.render_triangels(self.interaction)
            elif self.interaction.shading == Shading.wireframe:    
                self.mesh.render_lines(self.interaction)

            self.particles.render(self.interaction)    
            self._fps_calculations()
            glfw.swap_buffers(self.window)
        
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
        glViewport(0, 0, width, height)
        self.interaction.width = width
        self.interaction.height = height
        self.interaction.camera.aspect_ratio = width / height 
