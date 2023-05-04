from pyglet.gl import *
from pyglet_triangle import Triangle

class MyWindow(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.set_minimum_size(400, 300)
        glClearColor(0.2,0.3,0.2,1.0)

        self.triangle = Triangle() 

    def on_draw(self):
        self.clear()
        glDrawArrays(GL_TRIANGLES, 0, 3)

    def on_resize(self, width, height):
        glViewport(0,0,width, height)        

if __name__ == "__main__":

    print(glGetString(GL_VERSION))  
    
    window = MyWindow(1000, 800, "My pyglet window", resizable = True)
    pyglet.app.run()