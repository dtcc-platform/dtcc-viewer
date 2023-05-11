import os
import numpy as np
import math
import pyrr
from pprint import pp


def valid_number(num):
    if num == '':
        return 0
    return num

def convert_to_color(rgb_str):
    rgb = float(rgb_str)
    c = 0
    if rgb > 0:
        c = 255.0 / rgb
    return c 

def import_point_cloud_from_txt(filename):
    point_cloud = []
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            
            parts = line.split(',')
            if(len(parts) >= 3):
                point = pyrr.Vector3([float(parts[0]), float(parts[1]), float(parts[2])])
                point_cloud.append(point)
    
    return point_cloud


class ObjLoader:

    buffer = []
    colors = []

    @staticmethod
    def search_data(data_values, coordinates, skip, data_type):
        for d in data_values:
            if d == skip:
                continue
            if data_type == 'float':
                coordinates.append(float(d))
            elif data_type == 'int':
                coordinates.append(int(d)-1)
                

    @staticmethod # For glDrawArrays, only coordinates
    def create_sorted_vertex_buffer(indices_data, vertices):
        for i, ind in enumerate(indices_data):
            if i % 3 == 0: # sort vertex coordinates
                #Add coord
                start = ind * 3
                end1 = start + 3             
                ObjLoader.buffer.extend(vertices[start:end1])
                ObjLoader.colors.extend([1.0, 0.0, 0.0])


    @staticmethod # For glDrawArrays, coordinates and normals / colors
    def create_sorted_vertex_buffer_2(indices_data, vertices, normals_or_color):
        for i, ind in enumerate(indices_data):
            if i % 3 == 0: # sort vertex coordinates
                start = ind * 3
                end = start + 3             
                ObjLoader.buffer.extend(vertices[start:end])    
            elif i % 3 == 2: # sort normals         
                start = ind * 3
                end = start + 3             
                ObjLoader.buffer.extend(normals_or_color[start:end])
    
    @staticmethod # For glDrawElements
    def create_unsorted_vertex_buffer(indices_data, vertices, textures, normals):             
        # To be implemented
        pass

    @staticmethod
    def load_model(file):
        vert_coords = [] # Vertex coordinates
        vert_colors = []
        vert_normals = []
        vert_texcrd = []
        
        face_vert_indices = []
        face_norm_indices = []
        face_texc_indices = []

        edge_vert_indices = []
        
        with open(file, 'r') as f:
            line = f.readline()

            while line:
                values = line.split()
                if len(values) > 0:  
                    if values[0] == 'v':
                        if len(values) == 4:
                            vert_coords.append(float(values[1]))
                            vert_coords.append(float(values[2]))
                            vert_coords.append(float(values[3]))
                        elif len(values) == 7:
                            vert_coords.append(float(values[1]))
                            vert_coords.append(float(values[2]))
                            vert_coords.append(float(values[3]))
                            vert_colors.append(float(values[4])/255)
                            vert_colors.append(float(values[5])/255)
                            vert_colors.append(float(values[6])/255)
                    elif values[0] == 'vn':
                        if len(values) == 4:
                            vert_normals.append(float(values[1]))
                            vert_normals.append(float(values[2]))
                            vert_normals.append(float(values[3]))
                    elif values[0] == 'vt':
                        if len(values) == 4:
                            vert_texcrd.append(float(values[1]))
                            vert_texcrd.append(float(values[2]))
                            vert_texcrd.append(float(values[3]))
                    elif values[0] == 'f':
                        edges = []
                        for value in values[1:]:
                            val = value.split('/')
                            face_vert_indices.append(int(valid_number(val[0]))-1)
                            face_norm_indices.append(int(valid_number(val[2]))-1)
                            edges.append(int(valid_number(val[0]))-1)
                        for i in range(len(edges)):
                            if i < len(edges)-1:
                                edge_vert_indices.append(edges[i])
                                edge_vert_indices.append(edges[i+1])
                            else:
                                edge_vert_indices.append(edges[i])
                                edge_vert_indices.append(edges[0])    
                               

                line = f.readline()

        buffer = combine_coord_color(vert_coords, vert_colors)
        buffer  = np.array(buffer, dtype='float32')
        
        vert_coords  = np.array(vert_coords, dtype='float32')
        vert_colors  = np.array(vert_colors, dtype='float32')

        vert_normals = np.array(vert_normals, dtype='float32')
        vert_texcrd  = np.array(vert_texcrd, dtype='float32')

        face_vert_indices = np.array(face_vert_indices, dtype='uint32')
        face_norm_indices = np.array(face_norm_indices, dtype='uint32')

        edge_vert_indices = np.array(edge_vert_indices, dtype='uint32')
        
        return face_vert_indices, vert_coords, vert_colors, buffer, edge_vert_indices  
    
def combine_coord_color(vert_coords, vert_colors):

    buffer = []
    for i in range(len(vert_coords)):
        if i % 3 == 0:    
            start = i 
            end = i + 3
            buffer.extend(vert_coords[start:end])
            buffer.extend(vert_colors[start:end])

    return buffer

if __name__ == "__main__":

    os.system('clear')

    filename = 'data/city_point_cloud_69k.txt'

    #pc = import_point_cloud_from_txt(filename)

    #pp(pc)

    filename_obj = "../data/models/CitySurface.obj"

    [face_indices, vert_coords, vert_colors, buffer, edge_indices] = ObjLoader.load_model(filename_obj)

    #pp(edge_indices)



