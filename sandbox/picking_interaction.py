import glfw
import time
import pyrr
from OpenGL.GL import *
from OpenGL.GLU import *
from dtcc_viewer.opengl.camera import Camera


class PickingInteraction:
    """Handles mouse and keyboard interaction with the viewer.

    This class manages user input, such as keyboard, mouse button clicks, and cursor
    movement, to control the camera's behavior within the viewer window.

    Attributes
    ----------
    width : int
        The width of the viewer window.
    height : int
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
    """

    width: int
    height: int
    last_x: float
    last_y: float
    camera: Camera
    left_first_mouse: bool
    left_mbtn_pressed: bool
    right_first_mouse: bool
    right_mbtn_pressed: bool
    mouse_on_gui: bool
    tic: float
    toc: float
    tictoc_duration: float
    picking: bool
    picked_x: float
    picked_y: float

    render_fbo: bool
    cmap_index: int
    cmap_index_max: int

    # Selection rays
    ray_nds: pyrr.Vector3  # Ray in normalised device coordinates
    ray_clip: pyrr.Vector4  # Ray in homogenous clip coordinates
    ray_eye: pyrr.Vector4  # Ray in eye camera coordinates
    ray_wrld: pyrr.Vector3  # Ray in world coordinates

    def __init__(self, width, height):
        """Initialize the Interaction object with the provided width and height.

        Parameters
        ----------
        width : int
            The width of the viewer window.
        height : int
            The height of the viewer window.
        """
        self.width = width
        self.height = height
        self.last_x = self.width / 2.0
        self.last_y = self.height / 2.0
        self.camera = Camera(self.width, self.height)
        self.left_first_mouse = True
        self.left_mbtn_pressed = False
        self.right_first_mouse = True
        self.right_mbtn_pressed = False
        self.mouse_on_gui = False
        self.picking = False
        self.render_fbo = False

        self.cmap_index = 1
        self.cmap_index_max = 3

    def set_mouse_on_gui(self, mouse_on_gui):
        """Set the flag indicating whether the mouse cursor is over the GUI window.

        Parameters
        ----------
        mouse_on_gui : bool
            True if the mouse is over the GUI, False otherwise.
        """
        self.mouse_on_gui = mouse_on_gui

    def update_window_size(self, width, height):
        """Update width and height of the viewer window and adjust the camera settings.

        Parameters
        ----------
        width : int
            The new width of the viewer window.
        height : int
            The new height of the viewer window.
        """

        self.width = width
        self.height = height
        self.camera.update_window_aspect_ratio(width, height)

        print(self.width, self.height)

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
        if key == glfw.KEY_F and action == glfw.PRESS:
            self.render_fbo = not self.render_fbo

        if key == glfw.KEY_C and action == glfw.PRESS:
            self.cmap_index += 1
            if self.cmap_index > self.cmap_index_max:
                self.cmap_index = 1

        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)

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
                self.picked_x = xpos
                self.picked_y = self.height - ypos

        elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
            self.right_mbtn_pressed = True
        elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
            self.right_mbtn_pressed = False
            self.right_first_mouse = True

    def get_selection_click_screen_coords(self):
        """Get the screen coordinates of the selection click.

        Returns
        -------
        float
            The x-coordinate of the selection click.
        float
            The y-coordinate of the selection click.
        """
        return self.last_x, self.last_y

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
