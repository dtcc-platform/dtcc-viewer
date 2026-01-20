"""Fluent scene builder for composing multi-object visualizations."""

from typing import List
from dtcc_core.model import Object, Mesh, Surface, MultiSurface
from dtcc_viewer.opengl.parts import Parts
from dtcc_viewer.opengl.utils import concatenate_meshes
from dtcc_viewer.logging import info, warning


class _GroupedMesh:
    """Internal wrapper for grouped mesh objects with Parts for clickability."""

    def __init__(self, mesh: Mesh, parts: Parts):
        self.mesh = mesh
        self.parts = parts


class SceneBuilder:
    """Fluent builder for composing multi-object visualizations.

    This class provides a convenient API for viewing multiple DTCC objects
    together with optional data coloring.

    Examples
    --------
    # Chained single expression
    dtcc_viewer.scene().add(city).add(mesh, data=heights).view()

    # Assignable/modifiable
    s = dtcc_viewer.scene()
    s.add(city)
    s.add(mesh, data=heights)
    s.view()
    """

    def __init__(self, width=1200, height=800, situation=None):
        """Initialize the scene builder.

        Parameters
        ----------
        width : int
            Window width (default 1200)
        height : int
            Window height (default 800)
        situation : Situation, optional
            Geographic situation for sun positioning (enables dynamic shadows)
        """
        self._items = []  # List of (object, name, kwargs)
        self._width = width
        self._height = height
        self._situation = situation

    def add(self, obj, name=None, **kwargs):
        """Add an object with optional visualization parameters.

        Parameters
        ----------
        obj : DTCC object
            Mesh, City, PointCloud, Building, Surface, etc.
        name : str, optional
            Display name for the object. Auto-generated if not provided.
        data : array, optional
            Data for coloring (meshes, pointclouds, linestrings)
        size : float, optional
            Point size (pointclouds only, default 0.2)
        view_pointcloud : bool, optional
            Whether to show pointcloud for City objects (default False)

        Returns
        -------
        SceneBuilder
            Returns self for method chaining
        """
        if name is None:
            name = f"{type(obj).__name__}_{len(self._items)}"
        self._items.append((obj, name, kwargs))
        return self

    def size(self, width, height):
        """Set window dimensions.

        Parameters
        ----------
        width : int
            Window width in pixels
        height : int
            Window height in pixels

        Returns
        -------
        SceneBuilder
            Returns self for method chaining
        """
        self._width = width
        self._height = height
        return self

    def add_group(self, objects: List[Object], name: str = None, **kwargs):
        """Add a group of objects merged into a single representation.

        All objects must have the same geometry type (Mesh or Surface/MultiSurface).
        Individual objects remain clickable through the Parts system.

        Parameters
        ----------
        objects : List[Object]
            List of Object instances to merge. All must have the same geometry type.
        name : str, optional
            Display name for the group. Auto-generated if not provided.
        data : array, optional
            Data for coloring the merged mesh.

        Returns
        -------
        SceneBuilder
            Returns self for method chaining

        Raises
        ------
        ValueError
            If objects list is empty, contains mixed geometry types, or has
            unsupported geometry types (e.g., PointCloud).
        """
        # Filter out None values
        objects = [obj for obj in objects if obj is not None]

        if not objects:
            raise ValueError("Cannot add empty group")

        if name is None:
            name = f"Group_{len(self._items)}"

        # Detect geometry type
        geom_type = self._detect_geometry_type(objects)

        if geom_type is None:
            raise ValueError("No valid geometry found in objects")

        if geom_type == "mesh":
            merged_mesh, parts = self._merge_mesh_objects(objects)
            if merged_mesh is not None:
                self._items.append((_GroupedMesh(merged_mesh, parts), name, kwargs))
                info(f"Added group '{name}' with {parts.count} mesh parts")
        elif geom_type == "surface":
            merged_mesh, parts = self._merge_surface_objects(objects)
            if merged_mesh is not None:
                self._items.append((_GroupedMesh(merged_mesh, parts), name, kwargs))
                info(f"Added group '{name}' with {parts.count} surface parts")
        else:
            raise ValueError(
                f"Unsupported geometry type '{geom_type}' for add_group. "
                "Use add() for individual objects instead."
            )

        return self

    def _detect_geometry_type(self, objects: List[Object]) -> str:
        """Detect the common geometry type across all objects.

        Returns one of: 'mesh', 'surface', or None.
        Raises ValueError if objects have mixed geometry types.
        """
        detected_type = None

        for obj in objects:
            obj_type = None

            # Check for direct Mesh geometry first
            if obj.mesh is not None:
                obj_type = "mesh"
            # Then check LOD properties (Surface/MultiSurface)
            elif obj.lod3 is not None or obj.lod2 is not None or obj.lod1 is not None or obj.lod0 is not None:
                obj_type = "surface"

            if obj_type is None:
                warning(f"Object '{obj.id}' has no supported geometry, skipping")
                continue

            if detected_type is None:
                detected_type = obj_type
            elif detected_type != obj_type:
                raise ValueError(
                    f"All objects must have the same geometry type. "
                    f"Found both '{detected_type}' and '{obj_type}'."
                )

        return detected_type

    def _merge_mesh_objects(self, objects: List[Object]):
        """Merge objects with Mesh geometry into a single mesh with Parts."""
        meshes = []
        uuids = []
        attributes = []

        for obj in objects:
            mesh = obj.mesh
            if mesh is not None and len(mesh.faces) > 0:
                meshes.append(mesh)
                uuids.append(obj.id)
                attributes.append(obj.attributes)
            else:
                warning(f"Object '{obj.id}' has no valid mesh, skipping")

        if not meshes:
            warning("No valid meshes found in group")
            return None, None

        parts = Parts(meshes, uuids, attributes)
        merged_mesh = concatenate_meshes(meshes)
        info(f"Merged {len(meshes)} meshes into single mesh with {len(merged_mesh.faces)} faces")
        return merged_mesh, parts

    def _merge_surface_objects(self, objects: List[Object]):
        """Merge objects with Surface/MultiSurface geometry into a single mesh with Parts."""
        meshes = []
        uuids = []
        attributes = []

        for obj in objects:
            # Get highest available LOD
            geom = obj.lod3 or obj.lod2 or obj.lod1 or obj.lod0
            if geom is None:
                warning(f"Object '{obj.id}' has no LOD geometry, skipping")
                continue

            # Convert Surface to MultiSurface if needed
            if isinstance(geom, Surface):
                geom = MultiSurface(surfaces=[geom])

            # Mesh the MultiSurface
            mesh = geom.mesh(clean=False)
            if mesh is not None and len(mesh.faces) > 0:
                meshes.append(mesh)
                uuids.append(obj.id)
                attributes.append(obj.attributes)
            else:
                warning(f"Object '{obj.id}' surface meshing failed, skipping")

        if not meshes:
            warning("No valid surface meshes found in group")
            return None, None

        parts = Parts(meshes, uuids, attributes)
        merged_mesh = concatenate_meshes(meshes)
        info(f"Merged {len(meshes)} surfaces into single mesh with {len(merged_mesh.faces)} faces")
        return merged_mesh, parts

    def view(self):
        """Render the scene in a window.

        Opens a viewer window displaying all added objects.
        """
        from dtcc_viewer.opengl.window import Window
        from dtcc_viewer.opengl.scene import Scene as OpenGLScene

        window = Window(self._width, self._height)
        gl_scene = OpenGLScene(self._situation)

        for obj, name, kwargs in self._items:
            self._add_to_scene(gl_scene, obj, name, kwargs)

        window.render(gl_scene)

    def _add_to_scene(self, gl_scene, obj, name, kwargs):
        """Dispatch to appropriate Scene.add_* method based on object type."""
        from dtcc_core.model import (
            Mesh,
            PointCloud,
            City,
            Building,
            Surface,
            MultiSurface,
            LineString,
            MultiLineString,
            Bounds,
            Grid,
            VolumeGrid,
            VolumeMesh,
            RoadNetwork,
            Raster,
        )

        data = kwargs.get("data")

        # Handle grouped objects first
        if isinstance(obj, _GroupedMesh):
            gl_scene.add_mesh_with_parts(name, obj.mesh, obj.parts, data=data)
        elif isinstance(obj, Mesh):
            gl_scene.add_mesh(name, obj, data=data)
        elif isinstance(obj, PointCloud):
            gl_scene.add_pointcloud(
                name, obj, size=kwargs.get("size", 0.2), data=data
            )
        elif isinstance(obj, City):
            gl_scene.add_city(
                name, obj, view_pointcloud=kwargs.get("view_pointcloud", False)
            )
        elif isinstance(obj, Building):
            gl_scene.add_building(name, obj)
        elif isinstance(obj, Surface):
            gl_scene.add_surface(name, obj)
        elif isinstance(obj, MultiSurface):
            gl_scene.add_multisurface(name, obj)
        elif isinstance(obj, LineString):
            gl_scene.add_linestring(name, obj, data=data)
        elif isinstance(obj, MultiLineString):
            gl_scene.add_multilinestring(name, obj, data=data)
        elif isinstance(obj, Bounds):
            gl_scene.add_bounds(name, obj)
        elif isinstance(obj, Grid):
            gl_scene.add_grid(name, obj)
        elif isinstance(obj, VolumeGrid):
            gl_scene.add_volume_grid(name, obj)
        elif isinstance(obj, VolumeMesh):
            gl_scene.add_volume_mesh(name, obj)
        elif isinstance(obj, RoadNetwork):
            gl_scene.add_roadnetwork(name, obj)
        elif isinstance(obj, Raster):
            gl_scene.add_raster(name, obj)
        else:
            gl_scene.add_object(name, obj)


def scene(width=1200, height=800, situation=None):
    """Create a scene builder for composing multi-object visualizations.

    Parameters
    ----------
    width : int
        Window width (default 1200)
    height : int
        Window height (default 800)
    situation : Situation, optional
        Geographic situation for sun positioning (enables dynamic shadows).
        Create with dtcc_viewer.opengl.Situation(lon, lat, start, end).

    Returns
    -------
    SceneBuilder
        Fluent builder for adding objects

    Examples
    --------
    # Chained single expression
    import dtcc_viewer
    dtcc_viewer.scene().add(city).add(mesh, data=heights).view()

    # Assignable/modifiable
    s = dtcc_viewer.scene()
    s.add(city)
    s.add(mesh, data=heights)
    s.view()

    # With window size
    dtcc_viewer.scene().size(1600, 1200).add(mesh).view()

    # With dynamic sun shadows
    from dtcc_viewer.opengl import Situation
    import pandas as pd
    sit = Situation(lon=12.5, lat=55.7,
                    start=pd.Timestamp("2024-06-21 06:00"),
                    end=pd.Timestamp("2024-06-21 20:00"))
    dtcc_viewer.scene(situation=sit).add(city).view()
    """
    return SceneBuilder(width, height, situation)
