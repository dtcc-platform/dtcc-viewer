import numpy as np
import time
from pprint import pp
from string import Template
from OpenGL.GL import *
from abc import ABC, abstractmethod
from typing import Any
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrp_data import DataWrapper
from dtcc_viewer.opengl.parameters import GuiParametersObj
from dtcc_viewer.opengl.interaction import Action
from dtcc_viewer.opengl.utils import Shading
from dtcc_viewer.opengl.parameters import GuiParametersGlobal
from dtcc_viewer.opengl.environment import Environment


class GlObject(ABC):

    guip: GuiParametersObj  # GUI parameters

    data_wrapper: DataWrapper  # Data wrapper for the mesh
    data_texture: int  # Texture for data
    texture_slot: int  # GL_TEXTURE0, GL_TEXTURE1, etc.
    texture_idx: int  # Texture index 0 for GL_TEXTURE0, 1 for GL_TEXTURE1, etc.

    def preprocess(self):
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
        """Create texture for data."""

        self.data_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.data_texture)

        # Configure texture filtering and wrapping options
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        width = self.data_wrapper.col_count
        height = self.data_wrapper.row_count
        key = self.data_wrapper.get_keys()[0]
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
        if self.guip.update_data_tex:
            self._update_data_texture()
            self.guip.update_data_tex = False

    def update_data_caps(self):
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
