import os
from utils import VisType
from scene import Window



if __name__ == "__main__":
    
    os.system('clear')

    type = VisType.all

    window = Window(1600, 1400)
    if(type == VisType.particles):
        window.render_particles()
    elif(type == VisType.mesh):
        window.render_mesh()
    elif(type == VisType.all):
        window.render_particles_and_mesh()    
