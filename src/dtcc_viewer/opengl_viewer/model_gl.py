from dtcc_viewer.opengl_viewer.mesh_gl import MeshGL
from dtcc_viewer.opengl_viewer.mesh_wrapper import MeshWrapper
from dtcc_viewer.opengl_viewer.utils import Submeshes


class ModelGL:
    """Holds a collection of meshes for rendering with multi-mesh dependent features.

    This class contains a collection of meshes and related features for rendering of
    effects lite shadows and coloring for object picking. ModelGL extens the features
    of the mesh_gl with more shading options.

    """

    meshes_gl: list[MeshGL]

    def __init__(
        self, mesh_wrappers: list[MeshWrapper], submeshes: list[Submeshes] = None
    ):
        self.meshes_gl = []

        for mesh_wrapper in mesh_wrappers:
            mesh_gl = MeshGL(mesh_wrapper)
            self.meshes_gl.append(mesh_gl)

        pass
