import numpy as np
from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians


class Camera:
    """Camera used for viewing geometry and nagivation in a GLFW window.

    This class defines a camera with various attributes and methods for controlling
    its position, orientation, and view matrix.

    Attributes
    ----------
    camera_pos : Vector3
        The position of the camera.
    camera_front : Vector3
        The front direction of the camera.
    camera_up : Vector3
        The up direction of the camera.
    camera_right : Vector3
        The right direction of the camera.
    camera_target : Vector3
        The target point that the camera is looking at.
    camera_direction : Vector3
        The direction vector from the camera position to the target.
    distance_to_target : float
        The distance from the camera position to the target.
    width : int
        The width of the camera's viewport.
    heigh : int
        The height of the camera's viewport.
    aspect_ratio : float
        The aspect ratio of the camera's viewport.
    near_plane : float
        The near clipping plane distance.
    far_plane : float
        The far clipping plane distance.
    fov : int
        The field of view angle.
    mouse_sensitivity : float
        The sensitivity of mouse movement for rotation.
    scroll_sensitivity : float
        The sensitivity of mouse scroll for zooming.
    jaw : int
        The yaw rotation angle.
    pitch : int
        The pitch rotation angle.
    """

    def __init__(self, width, height):
        """Initialize the Camera object with the provided width and height.

        Parameters
        ----------
        width : int
            The width of the viewport.
        height : int
            The height of the viewport.
        """

        self.camera_pos = Vector3([0.0, 10.0, 3.0])
        self.camera_front = Vector3([0.0, 0.0, -1.0])
        self.camera_up = Vector3([0.0, 0.0, 1.0])
        self.camera_right = Vector3([1.0, 0.0, 0.0])
        self.camera_target = Vector3([0.0, 0.0, 0.0])
        self.camera_direction = Vector3([0.0, 0.0, 0.0])
        self.distance_to_target = 100.0

        self.width = width
        self.heigh = height
        self.aspect_ratio = float(width) / float(height)
        self.near_plane = 0.1
        self.far_plane = 10000
        self.fov = 25
        self.mouse_sensitivity = -0.25
        self.scroll_sensitivity = -0.1
        self.jaw = -90
        self.pitch = 0

        self.update_camera_vectors()

    def update_window_size(self, width, height) -> None:
        """Update the camera's viewport dimensions.

        Parameters
        ----------
        width : int
            The new width of the viewport.
        height : int
            The new height of the viewport.
        """
        self.width = width
        self.heigh = height
        self.aspect_ratio = float(width) / float(height)

    def set_aspect_ratio(self, aspect_ratio) -> None:
        """Set the camera's aspect ratio.

        Parameters
        ----------
        aspect_ratio : float
            The new aspect ratio value.
        """
        self.aspect_ratio = aspect_ratio

    def get_view_matrix(self) -> None:
        """Get the view matrix of the camera.

        Returns
        -------
        matrix44
            The view matrix of the camera.
        """
        return matrix44.create_look_at(
            self.camera_pos, self.camera_target, self.camera_up
        )

    def get_perspective_matrix(self) -> np.ndarray[any]:
        """Get the perspective projection matrix of the camera.

        Returns
        -------
        matrix44
            The perspective projection matrix of the camera.
        """
        return matrix44.create_perspective_projection(
            self.fov, self.aspect_ratio, self.near_plane, self.far_plane
        )

    def get_move_matrix(self):
        """Get the move matrix which positions the object around the origin.

        Returns
        -------
        matrix44
            The move matrix.
        """
        return matrix44.create_from_translation(Vector3([0, 0, 0]))

    def process_mouse_rotation(
        self, xoffset: float, yoffset: float, constrain_pitch=True
    ) -> None:
        """Process mouse movement for camera rotation.

        Parameters
        ----------
        xoffset : float
            The horizontal mouse movement offset.
        yoffset : float
            The vertical mouse movement offset.
        constrain_pitch : bool, optional
            Whether to constrain the pitch rotation, by default True.
        """
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

    def process_mouse_panning(self, xoffset: float, yoffset: float) -> None:
        """Process mouse movement for camera panning.

        Parameters
        ----------
        xoffset : float
            The horizontal mouse movement offset.
        yoffset : float
            The vertical mouse movement offset.
        """
        panning_sensitivity = self.distance_to_target / 2400
        pan_vector_right = (xoffset * panning_sensitivity) * self.camera_right
        pan_vector_up = (yoffset * panning_sensitivity) * self.camera_up

        self.camera_pos += pan_vector_right + pan_vector_up
        self.camera_target += pan_vector_right + pan_vector_up

        self.camera_direction = vector.normalise(self.camera_target - self.camera_pos)
        self.camera_right = vector.normalise(
            vector3.cross(self.camera_direction, Vector3([0.0, 0.0, 1.0]))
        )
        self.camera_up = vector.normalise(
            vector3.cross(self.camera_right, self.camera_direction)
        )

    def process_scroll_movement(
        self, xoffset: float, yoffset: float, constrain_pitch: bool = True
    ) -> None:
        """Process mouse scroll for adjusting camera distance.

        Parameters
        ----------
        xoffset : float
            The horizontal mouse scroll offset.
        yoffset : float
            The vertical mouse scroll offset.
        constrain_pitch : bool, optional
            Whether to constrain the pitch rotation, by default True.
        """
        self.distance_to_target += self.scroll_sensitivity * yoffset
        self.scroll_sensitivity = -0.1 - 0.02 * self.distance_to_target
        self.update_camera_vectors()

    def update_camera_vectors(self) -> None:
        """Update the camera's direction and orientation based on angles.

        Returns
        -------
        None
        """
        new_direction = Vector3([0.0, 0.0, 0.0])
        new_direction.x = cos(radians(self.jaw)) * cos(radians(self.pitch))
        new_direction.z = sin(radians(self.pitch))
        new_direction.y = sin(radians(self.jaw)) * cos(radians(self.pitch))

        self.camera_pos = (
            self.distance_to_target * vector.normalise(new_direction)
            + self.camera_target
        )

        self.camera_direction = vector.normalise(self.camera_target - self.camera_pos)
        self.camera_right = vector.normalise(
            vector3.cross(self.camera_direction, Vector3([0.0, 0.0, 1.0]))
        )
        self.camera_up = vector.normalise(
            vector3.cross(self.camera_right, self.camera_direction)
        )
