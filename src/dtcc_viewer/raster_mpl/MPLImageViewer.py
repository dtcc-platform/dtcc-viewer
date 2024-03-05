import matplotlib.pyplot as plt
import numpy as np


class MPLImageViewer:
    def __init__(self, image):
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(image, cmap="gray")
        self.ax.set_title("Raster")
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.start_x = None
        self.start_y = None

        self.fig.canvas.mpl_connect("button_press_event", self.on_button_press)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.fig.canvas.mpl_connect("scroll_event", self.on_mousewheel)

    def on_button_press(self, event):
        if event.button == 1:
            self.start_x = event.xdata
            self.start_y = event.ydata

    def on_move(self, event):
        if event.button == 1 and self.start_x and self.start_y:
            x = event.xdata
            y = event.ydata
            dx = self.start_x - x
            dy = self.start_y - y
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
            self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
            self.start_x = x
            self.start_y = y
            self.fig.canvas.draw()

    def on_mousewheel(self, event):
        scale = 1.0
        if event.button == "down":
            scale /= 1.2
        elif event.button == "up":
            scale *= 1.2
        x = event.xdata
        y = event.ydata
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        self.ax.set_xlim(
            xlim[0] * scale + (1 - scale) * x, xlim[1] * scale + (1 - scale) * x
        )
        self.ax.set_ylim(
            ylim[0] * scale + (1 - scale) * y, ylim[1] * scale + (1 - scale) * y
        )
        self.fig.canvas.draw()

    def show(self):
        plt.show()


# # Load image (replace with your own image path)
# image = plt.imread("path/to/image.jpg")

# # Create image viewer
# viewer = ImageViewer(image)

# # Show image viewer
# plt.show()
