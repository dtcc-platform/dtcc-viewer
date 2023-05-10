import tkinter as tk
from PIL import Image, ImageTk


class TkImageViewer:
    def __init__(self, master, pil_image):
        self.master = master
        self.image = pil_image
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas = tk.Canvas(
            self.master, width=self.image.width, height=self.image.height
        )
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.start_x = None
        self.start_y = None

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def on_move(self, event):
        if self.start_x and self.start_y:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.canvas.scan_dragto(-x + self.start_x, -y + self.start_y, gain=1)

    def on_mousewheel(self, event):
        scale = 1.0
        if event.num == 5 or event.delta == -120:
            scale /= 1.2
        if event.num == 4 or event.delta == 120:
            scale *= 1.2
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", x, y, scale, scale)

    def on_resize(self, event):
        w, h = event.width, event.height
        self.canvas.config(width=w, height=h)


# root = tk.Tk()
# viewer = ImageViewer(root, "path/to/image.jpg")
# root.mainloop()
