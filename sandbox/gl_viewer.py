import pyglet
import numpy as np
from pyglet.gl import *

from typing import List, Any
import ctypes

class MeshViewer(pyglet.window.Window):

    def __init__(self, width, height, title, mesh):
        super().__init__(width, height, title)
        self.mesh = mesh
        glClearColor(1,0,1,1)

    def on_draw(self):
        self.clear()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.width/self.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -10)
        glBegin(GL_TRIANGLES)
        for face in self.mesh.faces:
            for vertex in face:
                vertex_coord_list = list(self.mesh.vertices[vertex])
                vertex_coord_float = (ctypes.c_float * len(vertex_coord_list))(*vertex_coord_list)    
                glVertex3fv(vertex_coord_float)
        glEnd()

class Triangle:
        def __init__(self):
            self.vertices = [
                (-1, -1, 0),
                (1, -1, 0),
                (0, 1, 0),
            ]
            self.faces = [
                (0, 1, 2),
            ]


if __name__ == '__main__':
    
    mesh = Triangle()
    mesh_viewer = MeshViewer(1024, 756, "Mesh Viewer", mesh)
    pyglet.app.run()




