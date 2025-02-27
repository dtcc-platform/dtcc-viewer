import numpy as np
from dtcc_viewer.utils import *
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.wrapper import Wrapper
from dtcc_core.model import Surface, MultiSurface
from dtcc_viewer.opengl.utils import BoundingBox
from dtcc_viewer.opengl.wrp_mesh import MeshWrapper
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_viewer.opengl.parts import Parts
from typing import Any


class SurfaceWrapper(Wrapper):

    name: str
    mesh_wrp: MeshWrapper

    def __init__(self, name: str, surface: Surface, mts: int) -> None:
        """Initialize a SurfaceWrapper object."""
        self.name = name
        mesh = surface.mesh()
        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts)
        else:
            warning(f"Surface called '{name}' could not be converted to mesh.")

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_wrp.get_vertex_positions()


class MultiSurfaceWrapper(Wrapper):

    name: str
    mesh_wrp: MeshWrapper

    def __init__(self, name: str, multi_surface: MultiSurface, mts: int) -> None:
        """Initialize a MultiSurfaceWrapper object."""
        self.name = name
        mesh, parts, fields = self._get_mesh_parts_fields(multi_surface)

        if mesh is not None:
            self.mesh_wrp = MeshWrapper(name, mesh, mts, data=fields, parts=parts)
        else:
            warning(f"MultiSurface called '{name}' could not be converted to mesh.")

    def preprocess_drawing(self, bb_global: BoundingBox):
        self.mesh_wrp.preprocess_drawing(bb_global)

    def get_vertex_positions(self):
        return self.mesh_wrp.get_vertex_positions()

    def _get_mesh_parts_fields(self, ms: MultiSurface):
        # Assuming the field has one data point per surface
        fields = {}
        meshes = []

        for i, field in enumerate(ms.fields):
            if field.dim == 1 and len(field.values) == len(ms.surfaces):
                data = field.values
                fields[field.name] = data
            elif field.dim != 1:
                warning("Viewer only supports scalar fields in current implementation")
                warning(f"Field '{field.name}' has dimension != 1. Skipping.")
            elif len(field.values) != len(ms.surfaces):
                warning(
                    f"Field '{field.name}' has {len(field.values)} values, but there are {len(ms.surfaces)} surfaces."
                )

        # Create a mesh for each surface and match data to vertices in the mesh
        for i, surface in enumerate(ms.surfaces):
            mesh = surface.mesh()
            meshes.append(mesh)

        parts = Parts(meshes)
        mesh = concatenate_meshes(meshes)

        new_fields = {}
        for key, data in fields.items():
            new_data = []
            for i in range(len(ms.surfaces)):
                new_data.extend([data[i]] * len(meshes[i].faces))

            new_fields[key] = np.array(new_data)

        return mesh, parts, new_fields
