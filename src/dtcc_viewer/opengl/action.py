import glfw
import time
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.camera import Camera
from dtcc_viewer.opengl.environment import Environment
from dtcc_viewer.opengl.utils import CameraView, CameraProjection, BoundingBox
from dtcc_viewer.opengl.parameters import GuiParametersGlobal


class Action:
    """Handles mouse and keyboard interaction with the viewer.

    This class manages user input, such as keyboard, mouse button clicks, and cursor
    movement, to control the camera's behavior within the viewer window.

    Attributes
    ----------
    fbuf_width : int
        The width of the frame buffer.
    fbuf_height : int
        The height of frame buffer.
    win_width : int
        The width of the viewer window.
    win_height : int
        The height of the viewer window.
    last_x : float
        The last known x-coordinate of the mouse cursor.
    last_y : float
        The last known y-coordinate of the mouse cursor.
    camera : Camera
        The camera instance used for view manipulation.
    left_first_mouse : bool
        Flag indicating if this is the first mouse movement after a left-click.
    left_mbtn_pressed : bool
        Flag indicating if the left mouse button is currently pressed.
    right_first_mouse : bool
        Flag indicating if this is the first mouse movement after a right-click.
    right_mbtn_pressed : bool
        Flag indicating if the right mouse button is currently pressed.
    mouse_on_gui : bool
        Flag indicating if the mouse cursor is over the graphical user interface (GUI).
    show_shadow_texture : bool
        Flag indicating if the shadow texture should be drawn.
    show_picking_texture : bool
        Flag indicating if the picking texture should be drawn.
    zoom_selected : bool
        Flag indicating if the selected object should be zoomed in on.
    picking : bool
        Flag indicating if the user is currently picking an object.
    picked_x : float
        The x-coordinate in screen space of the picked object.
    picked_y : float
        The y-coordinate in screen space of the picked object.
    picked_id : int
        The ID of the picked object.
    tic : float
        The time at which the LMB was pressed.
    toc : float
        The time at which the LMB was released.
    tictoc_duration : float
        The duration between the LMB press and release.
    """

    fbuf_width: int  # Framwbuffer width
    fbuf_height: int  # Framebuffer height
    win_width: int  # Screen width (same as framebuffer width for non retina displays)
    win_height: int  # Screen height (same as framebuffer width for non retina displays)
    last_x: float
    last_y: float
    camera: Camera
    left_first_mouse: bool
    left_mbtn_pressed: bool
    right_first_mouse: bool
    right_mbtn_pressed: bool
    mouse_on_gui: bool

    gguip: GuiParametersGlobal

    show_shadow_texture: bool
    show_picking_texture: bool
    update_zoom_selected: bool

    # Tracking mouse picking clicks
    picking: bool
    picked_x: float
    picked_y: float
    picked_id: int
    tic: float
    toc: float
    tictoc_duration: float

    def __init__(self, width, height):
        """Initialize the Interaction object with the provided width and height.

        Parameters
        ----------
        width : int
            The width of the viewer window.
        height : int
            The height of the viewer window.
        """
        self.fbuf_width = width
        self.fbuf_height = height
        self.last_x = self.fbuf_width / 2.0
        self.last_y = self.fbuf_height / 2.0
        self.camera = Camera(self.fbuf_width, self.fbuf_height)
        self.left_first_mouse = True
        self.left_mbtn_pressed = False
        self.right_first_mouse = True
        self.right_mbtn_pressed = False
        self.mouse_on_gui = False
        self.show_shadow_texture = False
        self.show_picking_texture = False
        self.picking = False
        self.picked_x = 0
        self.picked_y = 0
        self.picked_id = -1
        self.update_zoom_selected = False

        self.gguip = GuiParametersGlobal()

    def initialise_camera(self, bb_global: BoundingBox):
        self._set_camera_distance_to_target(2.0 * bb_global.size)
        self._calc_near_far_planes(bb_global)
        self._save_init_camera()

    def _set_camera_distance_to_target(self, distance_to_target):
        self.camera.distance_to_target = distance_to_target
        self.camera.update_camera_vectors()

    def _save_init_camera(self):
        self.camera.save_init_camera()

    def _calc_near_far_planes(self, bb_global: BoundingBox):
        self.camera.calc_near_far_planes(bb_global)

    def update_view(self):
        self.camera.update_view(self.gguip.camera_view)
        self.gguip.update_camera = False

    def zoom_selected(self, distance_to_target, new_target):
        self.camera.zoom_selected(distance_to_target, new_target)

    def set_mouse_on_gui(self, mouse_on_gui):
        """Set the flag indicating whether the mouse cursor is over the GUI window.

        Parameters
        ----------
        mouse_on_gui : bool
            True if the mouse is over the GUI, False otherwise.
        """
        self.mouse_on_gui = mouse_on_gui

    def update_window_size(self, fb_width, fb_height, win_width, win_height):
        """Update width and height of the viewer window and adjust the camera settings.

        Parameters
        ----------
        width : int
            The new width of the viewer window.
        height : int
            The new height of the viewer window.
        """
        self.fbuf_width = fb_width
        self.fbuf_height = fb_height
        self.win_width = win_width
        self.win_height = win_height
        self.camera.update_window_aspect_ratio(fb_width, fb_height)

    def key_input_callback(self, window, key, scancode, action, mode):
        """Callback function for handling keyboard input.

        Parameters
        ----------
        window : object
            The GLFW window object.
        key : int
            The key that was pressed or released.
        scancode : int
            The system-specific scancode of the key.
        action : int
            The action (press, release, repeat) performed on the key.
        mode : int
            The modifier keys (shift, ctrl, alt) held down during the key action.
        """
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)
            info("Viewer terminated")
        elif key == glfw.KEY_S and action == glfw.PRESS:
            self.show_shadow_texture = not self.show_shadow_texture
            info(f"Draw shadow map: {self.show_shadow_texture}")
        elif key == glfw.KEY_D and action == glfw.PRESS:
            self.show_picking_texture = not self.show_picking_texture
            info(f"Draw picking texture: {self.show_picking_texture}")
        elif key == glfw.KEY_Z and action == glfw.PRESS:
            self.update_zoom_selected = True
        elif key == glfw.KEY_X and action == glfw.PRESS:
            self.camera.reset_init_camera()
            self.gguip.camera_view = CameraView.PERSPECTIVE
            self.gguip.camera_projection = CameraProjection.PERSPECTIVE
            info("Camera reset to initial position")
        elif key == glfw.KEY_1 and action == glfw.PRESS:
            self.camera.update_view(CameraView.PERSPECTIVE)
            self.gguip.camera_view = CameraView.PERSPECTIVE
            info("Perspective view set")
        elif key == glfw.KEY_2 and action == glfw.PRESS:
            self.camera.update_view(CameraView.TOP)
            self.gguip.camera_view = CameraView.TOP
            info("Top view set")
        elif key == glfw.KEY_3 and action == glfw.PRESS:
            self.camera.update_view(CameraView.FRONT)
            self.gguip.camera_view = CameraView.FRONT
            info("Front view set")
        elif key == glfw.KEY_4 and action == glfw.PRESS:
            self.camera.update_view(CameraView.BACK)
            self.gguip.camera_view = CameraView.BACK
            info("Back view set")
        elif key == glfw.KEY_5 and action == glfw.PRESS:
            self.camera.update_view(CameraView.LEFT)
            self.gguip.camera_view = CameraView.LEFT
            info("Left view set")
        elif key == glfw.KEY_6 and action == glfw.PRESS:
            self.camera.update_view(CameraView.RIGHT)
            self.gguip.camera_view = CameraView.RIGHT
            info("Right view set")

    def scroll_input_callback(self, window, xoffset, yoffset):
        """Callback function for handling mouse scroll input.

        Parameters
        ----------
        window : object
            The GLFW window object.
        xoffset : float
            The horizontal scroll offset.
        yoffset : float
            The vertical scroll offset.
        """
        self.camera.process_scroll_movement(xoffset, yoffset)

    def mouse_input_callback(self, window, button, action, mod):
        """Callback function for handling mouse button input.

        Parameters
        ----------
        window : object
            The GLFW window object.
        button : int
            The mouse button pressed or released.
        action : int
            The action (press or release) performed on the button.
        mod : int
            The modifier keys (shift, ctrl, alt) held down during the button action.
        """

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self.left_mbtn_pressed = True
            self.tic = time.perf_counter()
        elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.left_mbtn_pressed = False
            self.left_first_mouse = True
            self.toc = time.perf_counter()
            self.tictoc_duration = self.toc - self.tic
            if self.tictoc_duration < 0.2:
                self.picking = True
                (xpos, ypos) = glfw.get_cursor_pos(window)
                xpos = (self.fbuf_width / self.win_width) * xpos
                ypos = (self.fbuf_height / self.win_height) * ypos
                self.picked_x = xpos
                self.picked_y = self.fbuf_height - ypos

        elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
            self.right_mbtn_pressed = True
        elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
            self.right_mbtn_pressed = False
            self.right_first_mouse = True

    def mouse_look_callback(self, window, xpos, ypos):
        """Callback function for mouse cursor movement for view rotation and panning.

        Parameters
        ----------
        window : object
            The GLFW window object.
        xpos : float
            The new x-coordinate of the mouse cursor.
        ypos : float
            The new y-coordinate of the mouse cursor.
        """
        if not self.mouse_on_gui:
            if self.left_mbtn_pressed:
                if self.left_first_mouse:
                    self.last_x = xpos
                    self.last_y = ypos
                    self.left_first_mouse = False

                xoffset = xpos - self.last_x
                yoffset = self.last_y - ypos
                self.last_x = xpos
                self.last_y = ypos
                self.camera.process_mouse_rotation(xoffset, yoffset)

            elif self.right_mbtn_pressed:
                if self.right_first_mouse:
                    self.last_x = xpos
                    self.last_y = ypos
                    self.right_first_mouse = False

                xoffset = -(xpos - self.last_x)
                yoffset = ypos - self.last_y

                self.camera.process_mouse_panning(xoffset, yoffset)

                if not self.right_first_mouse:
                    self.last_x = xpos
                    self.last_y = ypos
