from abc import ABC, abstractmethod


class GLObject(ABC):

    def __init__(self):
        self._id = None

    @abstractmethod
    def preprocess(self):
        pass

    @abstractmethod
    def _create_textures():
        pass

    @abstractmethod
    def _create_geometry():
        pass

    @abstractmethod
    def _create_shaders():
        pass
