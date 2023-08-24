import glfw
from dtcc_viewer.opengl_viewer.camera import Camera


class Interaction:
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
        self.camera.update_window_size(width, height)

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
        elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.left_mbtn_pressed = False
            self.left_first_mouse = True
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
