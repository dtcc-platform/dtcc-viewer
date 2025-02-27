from dtcc_viewer.notebook_functions import is_notebook
from dtcc_core.model import Raster
from PIL import Image

from .MPLImageViewer import MPLImageViewer

try:
    from .TkImageViewers import TkImageViewer
except ImportError:
    HAS_TKINTER = False
else:
    HAS_TKINTER = True


def view(raster: Raster, show_in_browser=False):
    if not is_notebook() and not HAS_TKINTER:
        raise Exception(
            "Raster view only works in Jupyter notebooks or if tkinter is installed"
        )

    if is_notebook():
        img = raster.data
        viewer = MPLImageViewer(img)
