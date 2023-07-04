from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians


class Camera:

    def __init__(self, width, height):        
        self.camera_pos = Vector3([0.0, 10.0, 3.0])
        self.camera_front = Vector3([0.0, 0.0, -1.0])
        self.camera_up = Vector3([0.0, 0.0, 1.0])
        self.camera_right = Vector3([1.0, 0.0, 0.0])
        self.camera_target = Vector3([0.0, 0.0, 0.0]) 
        self.camera_direction = Vector3([0.0, 0.0, 0.0])
        self.distance_to_target = 100.0

        self.width = width
        self.heigh = height
        self.aspect_ratio = float(width)/float(height)
        self.near_plane = 0.1
        self.far_plane = 10000
        self.fov = 25
        self.mouse_sensitivity = -0.25
        self.scroll_sensitivity = -0.1
        self.jaw = -90
        self.pitch = 0

        self.update_camera_vectors()

    def update_window_size(self, width, height):
        self.width = width
        self.heigh = height
        self.aspect_ratio = float(width)/float(height)

    def set_aspect_ratio(self, aspect_ratio):
        self.aspect_ratio = aspect_ratio

    def get_view_matrix(self):
        return matrix44.create_look_at(self.camera_pos, self.camera_target, self.camera_up)

    def get_perspective_matrix(self):
        return matrix44.create_perspective_projection(self.fov, self.aspect_ratio, self.near_plane, self.far_plane)

    def process_mouse_rotation(self, xoffset, yoffset, constrain_pitch = True):
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.jaw += xoffset
        self.pitch += yoffset

        if constrain_pitch:
            if self.pitch > 89.99:
                self.pitch = 89.99
            if self.pitch < -89.99:
                self.pitch = -89.99    

        self.update_camera_vectors()

    def process_mouse_panning(self, xoffset, yoffset):
        
        panning_sensitivity = self.distance_to_target / 2400
        pan_vector_right = (xoffset * panning_sensitivity) * self.camera_right
        pan_vector_up = (yoffset * panning_sensitivity) * self.camera_up
        
        self.camera_pos += pan_vector_right + pan_vector_up
        self.camera_target += pan_vector_right + pan_vector_up

        self.camera_direction = vector.normalise(self.camera_target - self.camera_pos)
        self.camera_right = vector.normalise(vector3.cross(self.camera_direction, Vector3([0.0, 0.0, 1.0])))
        self.camera_up = vector.normalise(vector3.cross(self.camera_right, self.camera_direction))

        pass


    def process_scroll_movement(self, xoffset, yoffset, constrain_pitch = True):
        self.distance_to_target += self.scroll_sensitivity * yoffset
        self.scroll_sensitivity = -0.1 - 0.02 * self.distance_to_target    
        self.update_camera_vectors()


    def update_camera_vectors(self):
        new_direction = Vector3([0.0, 0.0, 0.0]) 
        new_direction.x = cos(radians(self.jaw)) * cos(radians(self.pitch))
        new_direction.z = sin(radians(self.pitch))
        new_direction.y = sin(radians(self.jaw)) * cos(radians(self.pitch))

        self.camera_pos = self.distance_to_target * vector.normalise(new_direction) + self.camera_target

        self.camera_direction = vector.normalise(self.camera_target - self.camera_pos)
        self.camera_right = vector.normalise(vector3.cross(self.camera_direction, Vector3([0.0, 0.0, 1.0])))
        self.camera_up = vector.normalise(vector3.cross(self.camera_right, self.camera_direction))

    


        
        

        