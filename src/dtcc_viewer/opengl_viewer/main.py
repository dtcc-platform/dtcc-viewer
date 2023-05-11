import os
from utils import VisType
from window import Window



if __name__ == "__main__":
    
    os.system('clear')

    type = VisType.all

    file_particle_data = '../../../data/models/CitySurface_pc1109k.txt'
    file_mesh_data = '../../../data/models/CitySurface.obj'

    window = Window(1600, 1400)
    if(type == VisType.particles):
        window.render_particles(file_particle_data)
    elif(type == VisType.mesh):
        window.render_mesh(file_mesh_data)
    elif(type == VisType.all):
        window.render_particles_and_mesh(file_particle_data, file_mesh_data)    
