from pyglet.gl import *

class Triangle:

    def __init__(self):

        self.vertices = pyglet.graphics.vertex_list(3, ('v3f', [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]),
                                                       ('c3B', [100,200,220,200,110,100,100,250,100]))

class Quad1:
    def __init__(self):
        self.vertices = pyglet.graphics.vertex_list_indexed(4, [0,1,2,2,3,0],
                                                               ('v3f', [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.5, 0.5, 0.0, -0.5, 0.5, 0.0]),
                                                               ('c3f', [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]))

class Quad2:
    def __init__(self):
        self.index = [0,1,2,2,3,0]
        self.vertex = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.5, 0.5, 0.0, -0.5, 0.5, 0.0]
        self.color = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
        self.vertices = pyglet.graphics.vertex_list_indexed(4, self.index, ('v3f',self.vertex), ('c3f',self.color))

class Quad3:
    def __init__(self):
        self.index = [0,1,2,2,3,0]
        self.vertex = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.5, 0.5, 0.0, -0.5, 0.5, 0.0]
        self.color = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]

    def render(self):    
        self.vertices = pyglet.graphics.draw_indexed(4, GL_TRIANGLES, self.index, ('v3f',self.vertex), ('c3f',self.color))


class MyWindow(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.set_minimum_size(400, 300)
        glClearColor(0.2,0.3,0.2,1.0)

        self.triangle = Triangle()
        self.quad1 = Quad1()
        self.quad2 = Quad2()
        self.quad3 = Quad2()

    def on_draw(self):
        self.clear()
        #Draw mode GL_TRIANGLES
        #self.triangle.vertices.draw(GL_TRIANGLES)
        #self.quad1.vertices.draw(GL_TRIANGLES)
        #self.quad2.vertices.draw(GL_TRIANGLES)
        self.quad3.vertices.draw(GL_TRIANGLES)

    def on_resize(self, width, height):
        glViewport(0,0,width, height)        

if __name__ == "__main__":
    window = MyWindow(1000, 800, "My pyglet window", resizable = True)
    #window.on_draw()
    pyglet.app.run()