
import glfw
from dtcc_viewer.opengl_viewer.camera import Camera
from dtcc_viewer.opengl_viewer.utils import MeshColor, MeshShading, ParticleColor

class Interaction:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.last_x = self.width/2.0 
        self.last_y = self.height/2.0
        self.camera = Camera(self.width, self.height)
        self.left_first_mouse = True
        self.left_mbtn_pressed = False
        self.right_first_mouse = True 
        self.right_mbtn_pressed = False
        self.mouse_on_gui = False

        self.mesh_draw = True
        self.mesh_color = MeshColor.color
        self.mesh_shading = MeshShading.shaded_fancy
        self.mesh_rotate = False
        
        self.particles_draw = True
        self.particle_color = ParticleColor.color
        self.particles_scale = 1.0

    def set_mouse_on_gui(self, mouse_on_gui):
        self.mouse_on_gui = mouse_on_gui    

    def update_window_size(self, width, height):
        self.width = width
        self.height = height
        self.camera.update_window_size(width, height)

    def key_input_callback(self, window, key, scancode, action, mode):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        if key == glfw.KEY_Q and action == glfw.PRESS:
            self.mesh_draw = not self.mesh_draw

        if key == glfw.KEY_W and action == glfw.PRESS:
            if(self.mesh_color == MeshColor.color):
                self.mesh_color = MeshColor.white
            elif(self.mesh_color == MeshColor.white):
                self.mesh_color = MeshColor.color

        if key == glfw.KEY_E and action == glfw.PRESS:
            if(self.mesh_shading == MeshShading.shaded_basic):
                self.mesh_shading = MeshShading.shaded_fancy
            elif(self.mesh_shading == MeshShading.shaded_fancy):
                self.mesh_shading = MeshShading.shaded_shadows
            elif(self.mesh_shading == MeshShading.shaded_shadows):
                self.mesh_shading = MeshShading.wireframe
            elif(self.mesh_shading == MeshShading.wireframe):
                self.mesh_shading = MeshShading.shaded_basic       

        if key == glfw.KEY_R and action == glfw.PRESS:
            self.mesh_rotate = not self.mesh_rotate

        if key == glfw.KEY_A and action == glfw.PRESS:                   
            self.particles_draw = not self.particles_draw     
                       
        if key == glfw.KEY_S and action == glfw.PRESS:
            if(self.particle_color == ParticleColor.color):
                self.particle_color = ParticleColor.white
            elif(self.particle_color == ParticleColor.white):
                self.particle_color = ParticleColor.color

        if key == glfw.KEY_D and action == glfw.PRESS:
            self.particles_scale -= 0.2 * self.particles_scale

        if key == glfw.KEY_F and action == glfw.PRESS:
            self.particles_scale += 0.2 * self.particles_scale


    def scroll_input_callback(self, window, xoffset, yoffset):
        self.camera.process_scroll_movement(xoffset, yoffset) 
        
    def mouse_input_callback(self, window, button, action, mod):  
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self.left_mbtn_pressed = True
        elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.left_mbtn_pressed = False
            self.left_first_mouse = True
        elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
            self.right_mbtn_pressed = True
        elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
            self.right_mbtn_pressed = False
            self.right_first_mouse = True    
            
    
    def mouse_look_callback(self, window, xpos, ypos):
        if (not self.mouse_on_gui):        
            if(self.left_mbtn_pressed):
                if self.left_first_mouse:
                    self.last_x = xpos
                    self.last_y = ypos
                    self.left_first_mouse = False

                xoffset = xpos - self.last_x
                yoffset = self.last_y - ypos
                self.last_x = xpos
                self.last_y = ypos
                self.camera.process_mouse_rotation(xoffset, yoffset)

            elif(self.right_mbtn_pressed):
                if self.right_first_mouse:
                    self.last_x = xpos
                    self.last_y = ypos
                    self.right_first_mouse = False

                xoffset = -(xpos - self.last_x)
                yoffset = (ypos - self.last_y)
                
                self.camera.process_mouse_panning(xoffset, yoffset)

                if not self.right_first_mouse:
                    self.last_x = xpos
                    self.last_y = ypos
                    