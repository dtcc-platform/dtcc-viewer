import numpy as np
import time
from pprint import pp
from string import Template
from OpenGL.GL import *
from abc import ABC, abstractmethod
from typing import Any
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.data_wrapper import DataWrapper
from dtcc_viewer.opengl.parameters import GuiParametersObj
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.utils import Shading
from dtcc_viewer.opengl.parameters import GuiParametersGlobal
from dtcc_viewer.opengl.environment import Environment


class GlObject(ABC):
    """
    Abstract base class for OpenGL objects.

    Attributes
    ----------
    guip: GuiParametersObj
        GUI parameters.
    data_wrapper: DataWrapper
        Data wrapper for the mesh.
    data_texture: int
        Texture for data.
    texture_slot: int
        Texture slot for OpenGL texture unit.
    texture_idx: int
        Texture index, 0 for ``GL_TEXTURE0``, 1 for ``GL_TEXTURE1``, etc.
    """

    guip: GuiParametersObj
    data_wrapper: DataWrapper
    data_texture: int
    texture_slot: int
    texture_idx: int

    def preprocess(self):
        """Preprocess method to create textures, geometry, and shaders."""
        self._create_textures()
        self._create_geometry()
        self._create_shaders()

    @abstractmethod
    def _create_textures():
        pass

    @abstractmethod
    def _create_geometry():
        pass

    @abstractmethod
    def _create_shaders():
        pass

    def _create_data_texture(self) -> None:
        """Create texture for data storage.

        TODO: Enable vector data to be stored in a texture.
        In OpenGL, textures can have multiple channels for data storage, typically
        represented by different color components such as red, green, blue, and alpha.
        In this current implementation only the red channel (GL_RED) is being used to
        store data, which means each texel (texture element) in the texture contains a
        single floating-point value. When accessing the texture in the shader using
        texelFetch (see shader code), only the red channel (r) of the texel is used to
        retrieve floating-point values.

        To enable vector data to be stored in a texture, multiple channels can
        be used by configuring the texture with a different internal format, such as
        GL_RGB or GL_RGBA, and appropriately handle the data in shader code, by
        access
        """
        self.data_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

        # Configure texture filtering and wrapping options
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        width = self.data_wrapper.col_count
        height = self.data_wrapper.row_count
        key = self.data_wrapper.get_keys()[0]  # Using the first key as default
        default_data = self.data_wrapper.data_mat_dict[key]

        # Transfer data to the texture
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_R32F,
            width,
            height,
            0,
            GL_RED,
            GL_FLOAT,
            default_data,
        )

    def _update_data_texture(self):
        """Update the data texture with the current data."""
        index = self.guip.data_idx
        key = self.data_wrapper.get_keys()[index]
        width = self.data_wrapper.col_count
        height = self.data_wrapper.row_count
        data = self.data_wrapper.data_mat_dict[key]
        tic = time.perf_counter()

        self._bind_data_texture()
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RED, GL_FLOAT, data)
        self._unbind_data_texture()

        toc = time.perf_counter()
        info(f"Data texture updated. Time elapsed: {toc - tic:0.4f} seconds")

    def update_data_texture(self):
        """Update the data texture if the user has triggered an update."""
        if self.guip.update_data_tex:
            self._update_data_texture()
            self.guip.update_data_tex = False

    def update_data_caps(self):
        """Update the data min and max values if the user has triggered an update."""
        if self.guip.update_caps:
            self.guip.calc_min_max()
            self.guip.update_caps = False

    def _bind_data_texture(self):
        """Bind the data texture."""
        glActiveTexture(self.texture_slot)
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

    def _unbind_data_texture(self):
        """Unbind the currently bound data texture."""
        glActiveTexture(self.texture_slot)
        glBindTexture(GL_TEXTURE_2D, 0)
