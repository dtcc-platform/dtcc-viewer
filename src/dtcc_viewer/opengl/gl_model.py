import math
import numpy as np
import pyrr
from pprint import pp
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl.action import Action
from dtcc_viewer.opengl.utils import Shading, BoundingBox, color_to_id
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl.gl_mesh import GlMesh
from dtcc_viewer.opengl.gl_points import GlPoints
from dtcc_viewer.opengl.gl_lines import GlLines
from dtcc_viewer.opengl.gl_raster import GlRaster
from dtcc_viewer.opengl.gl_object import GlObject
from dtcc_viewer.opengl.environment import Environment
from dtcc_viewer.opengl.parameters import GuiParametersModel

from dtcc_viewer.shaders.shaders_debug import (
    vertex_shader_debug_shadows,
    fragment_shader_debug_shadows,
    vertex_shader_debug_picking,
    fragment_shader_debug_picking,
)

from dtcc_viewer.shaders.shaders_mesh_picking import (
    vertex_shader_picking,
    fragment_shader_picking,
)


class GlModel:
    """Holds a collection of GlObjects for rendering with multi-obj dependent features.

    This class contains a collection of meshes, point clouds, line stings, rasters and
    related features for rendering of effects lite shadows and coloring for object
    picking.

    The GlModel calss has the shader for shadow maps and object picking since these are
    "global" actions performed for the whole model. For example, one GlMesh may cast
    shadows on another GlMesh so the shadow map needs to be rendered for the two meshes
    simultaneously.

    The model class also has a VAO, VBO, EBO, quad vertices and quad indices for the
    purpouse of debuging global features like the shadow map and the picking textures.
    In such cases, the quad is drawn on the whole screen and the texture is applied to
    the quad for display.

    The model class also holds the texture slots which are used to do two things: 1) to
    render shadow maps and picking textures, 2) to store data for visualisation. The
    number of texture slots available is limited by the graphics card typcally in the
    range of 16-32. Thats means 14-30 slots are available for data storage. Each
    GlObject in the model is given 1 texture slot for data storage.

    Attributes
    ----------
    gl_objects: list[GlObject]
        A list that contains all the OpenGL objects (`GlObject`) that belong to this model.
    env: Environment
        Collection of environment data like light sources etc.
    guip: GuiParametersModel
        Graphical user interface parameters for the model.
    VAO_debug: int
        OpenGL Vertex attribut object for debug quad.
    VB0_debug: int
        OpenGL Vertex buffer object for debug quad.
    EBO_debug: int
        OpenGL Element buffer object for debug quad.
    quad_vertices: np.ndarray
        Vertices for the debug quad.
    quad_indices: np.ndarray
        Indices for the debug quad.
    uloc_shmp: dict
        Uniform locations for the shadow map shader.
    uloc_dbsh: dict
        Uniform locations for redering the shadow map on a quad.
    uloc_dbpi: dict
        Uniform locations for rendering picking texture on a quad.
    uloc_pick: dict
        Uniform locations for the picking shader.
    shader_shmp: int
        Shader program for rendering of the shadow map.
    shader_pick: int
        Shader program for picking.
    shader_dbsh: int
        Shader program for debug rendering of the shadow map to a quad.
    shader_dbpi: int
        Shader program for debug rendering of picking texture to a quad.
    FBO_shadows: int
        OpenGL Frame Buffer Objects.
    shadow_depth_map: int
        Depth map identifier.
    shadow_map_resolution: int
        Resolution of the shadow map, same in x and y.
    shadow_border_color: np.ndarray
        Color for the border of the shadow map.
    lsm: np.ndarray
        Light space matrix for shadow map rendering.
    tex_slot_shadow_map: int
        GL_TEXTURE0, GL_TEXTURE1, etc.
    tex_slot_picking: int
        GL_TEXTURE0, GL_TEXTURE1, etc.
    """

    gl_objects: list[GlObject]
    guip: GuiParametersModel
    env: Environment
    VAO_debug: int
    VBO_debug: int
    EBO_debug: int
    quad_vertices: np.ndarray
    quad_indices: np.ndarray
    uloc_shmp: dict
    uloc_dbsh: dict
    uloc_dbpi: dict
    uloc_pick: dict
    shader_shmp: int
    shader_pick: int
    shader_dbsh: int
    shader_dbpi: int
    FBO_shadows: int
    shadow_depth_map: int
    shadow_map_resolution: int
    shadow_border_color: np.ndarray
    lsm: np.ndarray
    tex_slot_shadow_map: int
    tex_slot_picking: int

    def __init__(self, gl_objects: list[GlObject], bb_global: BoundingBox):
        """Initialize the GlModel object."""
        self.gl_objects = gl_objects

        self.guip = GuiParametersModel("Model", shading=Shading.WIRESHADED)
        self.env = Environment(bb_global)

        self.uloc_shmp = {}
        self.uloc_dbsh = {}
        self.uloc_dbpi = {}
        self.uloc_pick = {}

    def preprocess(self):

        if not self._distribute_texture_slots():
            warning("Texture slots distribution failed!")
            return False

        self._create_debug_quad()
        self._create_shadow_map()
        self._create_shader_picking()
        self._create_shader_debug_shadows()
        self._create_shader_debug_picking()
        self._set_constats()

        for obj in self.gl_objects:
            obj.preprocess()

        return True

    def filter_gl_type(self, gl_type):
        """Filter the gl_objects list by type."""
        if gl_type == GlMesh:
            return [mesh for mesh in self.gl_objects if isinstance(mesh, GlMesh)]
        elif gl_type == GlPoints:
            return [pc for pc in self.gl_objects if isinstance(pc, GlPoints)]
        elif gl_type == GlLines:
            return [lss for lss in self.gl_objects if isinstance(lss, GlLines)]
        elif gl_type == GlRaster:
            return [rst for rst in self.gl_objects if isinstance(rst, GlRaster)]
        else:
            raise ValueError("Invalid gl_type")

    def _set_constats(self) -> None:
        """Set constant values like light position and color."""

        self.light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.loop_counter = 120

    def create_picking_fbo(self, action: Action) -> None:
        """Create a frame buffer object for object picking."""
        window_w = action.fbuf_width
        window_h = action.fbuf_height

        self.FBO_picking = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_picking)  # Bind our frame buffer

        self.pick_texture = glGenTextures(1)
        glActiveTexture(self.tex_slot_picking)  # Activate assigned texture slot
        glBindTexture(GL_TEXTURE_2D, self.pick_texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, window_w, window_h, 0, GL_RGB, GL_FLOAT, None
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)  # Unbind our texture
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.pick_texture, 0
        )

        RBO = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, RBO)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, window_w, window_h)
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, RBO
        )

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            warning("Framebuffer for picking is failed")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Unbind our frame buffer

    def _distribute_texture_slots(self) -> None:
        """Distribute texture slots to all the meshes, pointclouds, lines."""

        texture_slots = self._get_texture_slots()

        # The first slot GL_TEXTURE0 is reserved for the shadow map
        self.tex_slot_shadow_map = texture_slots[0]
        self.tex_idx_shadow_map = 0

        # The second slot GL_TEXTURE1 is reserved for the picking texture
        self.tex_slot_picking = texture_slots[1]
        self.tex_idx_picking = 1

        if len(self.gl_objects) > len(texture_slots) - 2:
            warning("Not enough texture slots for all rendable entities.")
            return False

        next_idx = 2

        for obj in self.gl_objects:
            obj.texture_slot = texture_slots[next_idx]
            obj.texture_idx = next_idx
            next_idx += 1

        return True

    def _create_debug_quad(self) -> None:
        """Create a quad for debuging purposes."""
        tex_min = 0
        tex_max = 1

        self.quad_vertices = [
            -1.0,
            -1.0,
            tex_min,
            tex_min,
            1.0,
            -1.0,
            tex_max,
            tex_min,
            -1.0,
            1.0,
            tex_min,
            tex_max,
            1.0,
            -1.0,
            tex_max,
            tex_min,
            -1.0,
            1.0,
            tex_min,
            tex_max,
            1.0,
            1.0,
            tex_max,
            tex_max,
        ]
        self.quad_indices = [
            0,
            1,
            2,
            3,
            4,
            5,
        ]

        self.quad_vertices = np.array(self.quad_vertices, dtype=np.float32)
        self.quad_indices = np.array(self.quad_indices, dtype=np.uint32)

        self.VAO_debug = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_debug)

        # Vertex buffer
        size = len(self.quad_vertices) * 4  # Size in bytes
        self.VBO_debug = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_debug)
        glBufferData(GL_ARRAY_BUFFER, size, self.quad_vertices, GL_STATIC_DRAW)

        # Element buffer
        size = len(self.quad_indices) * 4  # Size in bytes
        self.EBO_debug = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_debug)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, self.quad_indices, GL_STATIC_DRAW)

        # Position (x, y)
        glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))

        # Texture coordinates (x, y)
        glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))

    def _create_shadow_map(self) -> None:
        """Set up framebuffer and texture for shadow map rendering."""
        # Frambuffer for the shadow map
        self.FBO_shadows = glGenFramebuffers(1)

        # Creating a texture which will be used as the framebuffers depth buffer
        self.shadow_depth_map = glGenTextures(1)
        glActiveTexture(self.tex_slot_shadow_map)  # Activate assigned texture slot
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_map)
        self.shadow_map_resolution = 1024 * 8
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_DEPTH_COMPONENT,
            self.shadow_map_resolution,
            self.shadow_map_resolution,
            0,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
            None,
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        self.shadow_border_color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        glTexParameterfv(
            GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, self.shadow_border_color
        )

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_shadows)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.shadow_depth_map, 0
        )
        # Disable drawing to the color attachements since we only care about the depth
        glDrawBuffer(GL_NONE)

        # We don't want to read color attachements either
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _create_shader_debug_shadows(self) -> None:
        """Create shader for rendering the shadow map onto a quad for debugging."""

        self.shader_dbsh = compileProgram(
            compileShader(vertex_shader_debug_shadows, GL_VERTEX_SHADER),
            compileShader(fragment_shader_debug_shadows, GL_FRAGMENT_SHADER),
        )

    def _create_shader_picking(self) -> None:
        """Create shader for picking rendering."""

        self.shader_pick = compileProgram(
            compileShader(vertex_shader_picking, GL_VERTEX_SHADER),
            compileShader(fragment_shader_picking, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_pick)

        self.uloc_pick["model"] = glGetUniformLocation(self.shader_pick, "model")
        self.uloc_pick["project"] = glGetUniformLocation(self.shader_pick, "project")
        self.uloc_pick["view"] = glGetUniformLocation(self.shader_pick, "view")

        self.uloc_pick["clip_x"] = glGetUniformLocation(self.shader_pick, "clip_x")
        self.uloc_pick["clip_y"] = glGetUniformLocation(self.shader_pick, "clip_y")
        self.uloc_pick["clip_z"] = glGetUniformLocation(self.shader_pick, "clip_z")

    def _create_shader_debug_picking(self) -> None:
        """Create shader for rendering the picking texture onto a quad."""

        self.shader_dbpi = compileProgram(
            compileShader(vertex_shader_debug_picking, GL_VERTEX_SHADER),
            compileShader(fragment_shader_debug_picking, GL_FRAGMENT_SHADER),
        )

        self.uloc_dbpi["screenTex"] = glGetUniformLocation(
            self.shader_dbpi, "screenTex"
        )

    def zoom_selected(self, action: Action) -> None:
        """Zoom the camera to the selected object."""
        if self.guip.picked_cp is None or self.guip.picked_size is None:
            action.update_zoom_selected = False
            info("Zoom selected: No object selected for zooming")
            return

        # Calculate the distance to the target object
        distance_to_target = 5.0 * self.guip.picked_size
        target = self.guip.picked_cp
        action.zoom_selected(distance_to_target, target)
        action.update_zoom_selected = False
        info(
            f"Zoom selected: New camera position centered on object {self.guip.picked_id}"
        )

    def evaluate_picking(self, action: Action) -> None:
        """Evaluate the picking texture to find the picked object."""
        if not action.mouse_on_gui:
            self._draw_picking_texture(action)
            self._evaluate_picking(action)
        else:
            action.picking = False

    def _draw_picking_texture(self, action: Action) -> None:
        """Draw the picking texture to the frame buffer."""

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Camera input
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix(action.gguip)
        proj = action.camera.get_projection_matrix(action.gguip)

        # Picking pass
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_picking)
        glEnable(GL_DEPTH_TEST)
        # glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_pick)

        glUniformMatrix4fv(self.uloc_pick["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_pick["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_pick["project"], 1, GL_FALSE, proj)

        (xdom, ydom, zdom) = self._get_clip_domains()

        glUniform1f(self.uloc_pick["clip_x"], (xdom * action.gguip.clip_dist[0]))
        glUniform1f(self.uloc_pick["clip_y"], (ydom * action.gguip.clip_dist[1]))
        glUniform1f(self.uloc_pick["clip_z"], (zdom * action.gguip.clip_dist[2]))

        # Draw meshes to the texture
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.triangles_draw_call()

    def _evaluate_picking(self, action: Action) -> None:
        """Get picking texture color under the mouse click and compute object id."""
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        x = action.picked_x
        y = action.picked_y

        p_color = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        picked_id_new = color_to_id(p_color)

        # Background color
        p_color = np.array([p_color[0], p_color[1], p_color[2]], dtype=int)
        b_color = np.array(np.round(np.array(action.gguip.color) * 255), dtype=int)

        background_click = False
        if np.all(b_color[0:3] == p_color[0:3]):
            background_click = True

        if picked_id_new == action.picked_id or background_click:
            action.picked_id = -1
            self.guip.picked_id = -1
            self.guip.picked_cp = None
            self.guip.picked_uuid = ""
            self.guip.picked_metadata = ""
        else:
            action.picked_id = picked_id_new
            self.guip.picked_id = picked_id_new
            self._find_object_from_id(picked_id_new)
            self._find_data_from_id(picked_id_new)

        action.picking = False

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _render_pick_texture(self, action: Action) -> None:
        """Render the picking texture to a quad that spans the screen for debugging."""
        self._draw_picking_texture(action)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Apply the picking texture to the debug quad which spans th whole screen.
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.shader_dbpi)  # Use the debug picking shader
        glBindVertexArray(self.VAO_debug)

        glActiveTexture(self.tex_slot_picking)
        glBindTexture(GL_TEXTURE_2D, self.pick_texture)
        glUniform1i(self.uloc_dbpi["screenTex"], self.tex_idx_picking)

        # Draw the quad
        self._debug_quad_draw_call()
        glEnable(GL_DEPTH_TEST)

    def render(self, action: Action) -> None:
        """Render all gl_objects in the model."""
        self._render_meshes(action)
        self._render_points(action)
        self._render_lines(action)
        self._render_rasters(action)

        self._update_light_position()
        self._update_data_caps()
        self._update_data_textures()

    def _render_meshes(self, action: Action) -> None:
        """Render meshes base of display mode."""
        self.guip.animate_light = False
        if self.guip.shading == Shading.WIREFRAME:
            self._render_wireframe(action)
        elif self.guip.shading == Shading.AMBIENT:
            self._render_ambient(action)
        elif self.guip.shading == Shading.DIFFUSE:
            self._render_diffuse(action)
        elif self.guip.shading == Shading.WIRESHADED:
            self._render_wireshaded(action)
        elif self.guip.shading == Shading.SHADOWS_STATIC:
            self._render_shadows(action)
        elif self.guip.shading == Shading.SHADOWS_DYNAMIC:
            self.guip.animate_light = True
            self._render_shadows(action)
        elif self.guip.shading == Shading.PICKING:
            self._render_pick_texture(action)
        else:
            warning("Shading not set for model instance")

        self._render_normals(action)

    def _render_normals(self, action: Action) -> None:
        """Render normals for all meshes."""
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.render_normals(action)

    def _render_points(self, action: Action) -> None:
        """Render point clouds."""
        for obj in self.gl_objects:
            if isinstance(obj, GlPoints):
                guip = obj.guip
                if guip.show:
                    obj.render(action)

    def _render_lines(self, action: Action) -> None:
        """Render lines"""
        for obj in self.gl_objects:
            if isinstance(obj, GlLines):
                guip = obj.guip
                if guip.show:
                    obj.render(action)

    def _render_rasters(self, action: Action) -> None:
        """Render rasters"""
        for obj in self.gl_objects:
            if isinstance(obj, GlRaster):
                guip = obj.guip
                if guip.show:
                    obj.render(action)

    def _render_wireframe(self, action: Action) -> None:
        """Render meshes in wireframe display mode."""
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.render_wireframe(action, self.env, self.guip)

    def _render_ambient(self, action: Action) -> None:
        """Render meshes in ambient display mode."""
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.render_ambient(action, self.guip)

    def _render_diffuse(self, action: Action) -> None:
        """Render meshes in diffuse display mode."""
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.render_diffuse(action, self.env, self.guip)

    def _render_wireshaded(self, action: Action) -> None:
        """Render meshes in wireshaded display mode."""
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.render_wireshaded(action, self.env, self.guip)

    def _render_shadows(self, action: Action) -> None:
        """Generates a shadow map and renders the mesh with shadows."""
        if action.show_shadow_texture:
            self._render_shadows_pass1(action)
            self._render_debug_shadow_map(action)
        else:
            self._render_shadows_pass1(action)
            self._render_shadows_pass2(action)

    def _render_shadows_pass1(self, action: Action) -> None:
        """Render a shadow map to the frame buffer."""
        # first pass: Render shadow map and save to the frame buffer
        rad = self.env.radius_xy
        far = 1.25 * self.env.diameter_xy
        light_proj = pyrr.matrix44.create_orthogonal_projection(
            -rad, rad, -rad, rad, 0.1, far, dtype=np.float32
        )
        light = self.env.light_pos
        target = np.array([0, 0, 0], dtype=np.float32)
        up = np.array([0, 0, 1], dtype=np.float32)
        light_view = pyrr.matrix44.create_look_at(light, target, up, dtype=np.float32)
        self.lsm = pyrr.matrix44.multiply(light_view, light_proj)

        glViewport(0, 0, self.shadow_map_resolution, self.shadow_map_resolution)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_shadows)

        # Only clearing depth buffer since there is no color attachement
        glClear(GL_DEPTH_BUFFER_BIT)

        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                # In this pass, only meshes that should cast shadows are added.
                if obj.guip.show and obj.cast_shadows:
                    obj.render_shadows_pass1(self.lsm)

    def _render_shadows_pass2(self, action: Action) -> None:
        """Render the model with shadows by sampling the shadow map frame buffer."""
        # Second pass: Render objects with the shadow map computed in the first pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Setting default buffer
        glViewport(0, 0, action.fbuf_width, action.fbuf_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Bind the shadow map texture so that it can be sampled in the shader
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_map)

        # Set up individual mesh parameters and uniforms for rendering
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                if obj.guip.show:
                    obj.render_shadows_pass2(action, self.env, self.guip, self.lsm)

    def _render_debug_shadow_map(self, interaction: Action) -> None:
        """Render the shadow map to a quad for debugging."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, interaction.fbuf_width, interaction.fbuf_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_dbsh)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_map)
        self._debug_quad_draw_call()

    def _debug_quad_draw_call(self) -> None:
        """Draw the debug quad."""
        glBindVertexArray(self.VAO_debug)
        glDrawElements(GL_TRIANGLES, len(self.quad_indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def _update_light_position(self) -> None:
        """Update the light position for dynamic shadows."""
        if self.guip.animate_light:
            self.env._calc_light_position()

    def _update_data_caps(self):
        """Update the data value caps for sliders."""
        for obj in self.gl_objects:
            obj.update_data_caps()

    def _update_data_textures(self):
        """Update the data textures for visualisation."""
        for obj in self.gl_objects:
            obj.update_data_texture()

    def _find_object_from_id(self, id):
        """Find the object that has the id and set the picked object."""
        self.guip.picked_uuid = None
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):  # Only meshes are pickable atm
                if obj.parts is not None:
                    if obj.parts.id_exists(id):
                        self.guip.picked_attributes = obj.parts.get_attributes(id)
                        break

    def _find_data_from_id(self, id):
        """Calculate mesh related the data for the picked object."""
        sucess = False
        for obj in self.gl_objects:
            if isinstance(obj, GlMesh):
                vertex_ids = obj.get_vertex_ids()
                vertex_idx = np.where(vertex_ids == id)[0]
                if len(vertex_idx) > 0:
                    f_count = len(vertex_idx) // 3
                    v_count = len(vertex_idx)
                    (avrg_pt, radius) = obj.get_average_vertex_position(vertex_idx)
                    sucess = True
                    break

        # Assign to
        if sucess:
            self.guip.picked_mesh_face_count = f_count
            self.guip.picked_mesh_vertex_count = v_count
            self.guip.picked_cp = avrg_pt
            self.guip.picked_size = radius
        else:
            self.guip.picked_cp = None
            self.guip.picked_size = None

    def _get_texture_slots(self):
        """Get the available texture slots."""
        texture_slots = [
            GL_TEXTURE0,
            GL_TEXTURE1,
            GL_TEXTURE2,
            GL_TEXTURE3,
            GL_TEXTURE4,
            GL_TEXTURE5,
            GL_TEXTURE6,
            GL_TEXTURE7,
            GL_TEXTURE8,
            GL_TEXTURE9,
            GL_TEXTURE10,
            GL_TEXTURE11,
            GL_TEXTURE12,
            GL_TEXTURE13,
            GL_TEXTURE14,
            GL_TEXTURE15,
        ]

        return texture_slots

    def _get_clip_domains(self):
        """Get the clipping domains."""
        xdom = 0.5 * self.env.bb_global.xdom
        ydom = 0.5 * self.env.bb_global.ydom
        zdom = 0.5 * self.env.bb_global.zdom
        return xdom, ydom, zdom
