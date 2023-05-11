
import glfw
from camera import Camera
from utils import Coloring, Shading

class Interaction:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.last_x = self.width/2.0 
        self.last_y = self.height/2.0
        self.first_mouse = True
        self.camera = Camera(float(self.width)/float(self.height))
        self.left_mbtn_pressed = False
        self.coloring = Coloring.color
        self.shading = Shading.shaded

    def key_input_callback(self, window, key, scancode, action, mode):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        if key == glfw.KEY_W and action == glfw.PRESS:
            if(self.shading == Shading.shaded):
                self.shading = Shading.wireframe
            elif(self.shading == Shading.wireframe):
                self.shading = Shading.shaded

        if key == glfw.KEY_Q and action == glfw.PRESS:
            if(self.coloring == Coloring.color):
                self.coloring = Coloring.white
            elif(self.coloring == Coloring.white):
                self.coloring = Coloring.color 
        
    def scroll_input_callback(self, window, xoffset, yoffset):
        self.camera.process_scroll_movement(xoffset, yoffset) 
        
    def mouse_input_callback(self, window, button, action, mod):  
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self.left_mbtn_pressed = True
        elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.left_mbtn_pressed = False
            self.first_mouse = True
    
    def mouse_look_callback(self, window, xpos, ypos):        
        if(self.left_mbtn_pressed):
            if self.first_mouse:
                self.last_x = xpos
                self.last_y = ypos
                self.first_mouse = False

            xoffset = xpos - self.last_x
            yoffset = self.last_y - ypos
            self.last_x = xpos
            self.last_y = ypos
            self.camera.process_mouse_movement(xoffset, yoffset)