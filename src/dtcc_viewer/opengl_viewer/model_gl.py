import math
import numpy as np
import pyrr
from pprint import pp
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from dtcc_viewer.opengl_viewer.interaction import Action
from dtcc_viewer.opengl_viewer.utils import Shading, BoundingBox, color_to_id
from dtcc_viewer.logging import info, warning
from dtcc_viewer.opengl_viewer.mesh_gl import MeshGL
from dtcc_viewer.opengl_viewer.pointcloud_gl import PointCloudGL
from dtcc_viewer.opengl_viewer.linestring_gl import LineStringGL
from dtcc_viewer.opengl_viewer.environment import Environment
from dtcc_viewer.opengl_viewer.parameters import GuiParameters, GuiParametersModel

from dtcc_viewer.opengl_viewer.shaders_debug import (
    vertex_shader_debug_shadows,
    fragment_shader_debug_shadows,
    vertex_shader_debug_picking,
    fragment_shader_debug_picking,
)

from dtcc_viewer.opengl_viewer.shaders_mesh_picking import (
    vertex_shader_picking,
    fragment_shader_picking,
)


class ModelGL:
    """Holds a collection of meshes for rendering with multi-mesh dependent features.

    This class contains a collection of meshes and related features for rendering of
    effects lite shadows and coloring for object picking. ModelGL extens the features
    of the mesh_gl with more shading options.

    """

    meshes: list[MeshGL]
    pointclouds: list[PointCloudGL]
    linestrings: list[LineStringGL]

    guip: GuiParametersModel  # Gui parameters for the model
    env: Environment  # Collection of environment data like light sources etc.

    # The model class has a VAO, VBO and EBO for a debug quad which are used to render
    # global features like the shadow map and the picking textures to the screen.
    VAO_debug: int  # OpenGL Vertex attribut object for debug quad
    VBO_debug: int  # OpenGL Vertex buffer object for debug quad
    EBO_debug: int  # OpenGL Element buffer object for debug quad

    quad_vertices: np.ndarray  # Vertices for the debug quad
    quad_indices: np.ndarray  # Indices for the debug quad

    # The model calss has uniform locations for the shadow map shader and the picking
    # shader since these are "global" actions performed for the whole model
    uloc_shmp: dict  # Uniform locations for the shadow map shader
    uloc_dbsh: dict  # Uniform locations for redering the shadow map on a quad
    uloc_dbpi: dict  # Uniform locations for rendering picking texture on a quad
    uloc_pick: dict  # Uniform locations for the picking shader

    # The model calss also has the shader programs for shadow map and picking rendering
    # since these are "global" actions performed for the whole model
    shader_shmp: int  # Shader program for rendering of the shadow map to the frame buffer
    shader_pick: int  # Shader program for picking
    shader_dbsh: int  # Shader program for debug rendering of the shadow map to a quad
    shader_dbpi: int  # Shader program for debug rendering of picking texture to a quad

    FBO_shadows: int  # OpenGL Frame Buffer Objects
    shadow_depth_map: int  # Depth map identifier
    shadow_map_resolution: int  # Resolution of the shadow map, same in x and y.
    shadow_border_color: np.ndarray  # color for the border of the shadow map
    lsm: np.ndarray  # Light space matrix for shadow map rendering

    def __init__(
        self,
        msh: list[MeshGL],
        pcs: list[PointCloudGL],
        rns: list[LineStringGL],
        bb_global: BoundingBox,
    ):
        self.meshes = msh
        self.pointclouds = pcs
        self.linestrings = rns

        self.guip = GuiParametersModel("Model", shading=Shading.wireshaded)
        self.env = Environment(bb_global)

        self.uloc_shmp = {}
        self.uloc_dbsh = {}
        self.uloc_dbpi = {}
        self.uloc_pick = {}

        self._offset_picking_ids()
        self._create_debug_quad()
        self._create_shadow_map()
        self._create_shader_picking()
        self._create_shader_debug_shadows()
        self._create_shader_debug_picking()
        self._set_constats()

        pass

    def _set_constats(self) -> None:
        """Set constant values like light position and color."""

        self.light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.loop_counter = 120

    def create_picking_fbo(self, action: Action) -> None:
        window_w = action.fbuf_width
        window_h = action.fbuf_height

        self.FBO_picking = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_picking)  # Bind our frame buffer

        self.pick_texture = glGenTextures(1)
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

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
            info("Framebuffer for picking is complete")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Unbind our frame buffer

        pass

    def _offset_picking_ids(self) -> None:
        id_offset = 0
        id_offsets = []
        id_offsets.append(0)

        for mesh in self.meshes:
            id_offset += np.max(mesh.vertices[9::10]) + 1
            id_offsets.append(id_offset)

        for i, mesh in enumerate(self.meshes):
            mesh.vertices[9::10] += id_offsets[i]

    def _create_debug_quad(self) -> None:
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
        """Create shader for rendering shadow map."""

        self.shader_dbsh = compileProgram(
            compileShader(vertex_shader_debug_shadows, GL_VERTEX_SHADER),
            compileShader(fragment_shader_debug_shadows, GL_FRAGMENT_SHADER),
        )

    def _create_shader_picking(self) -> None:
        """Create shader for picking."""

        self.shader_pick = compileProgram(
            compileShader(vertex_shader_picking, GL_VERTEX_SHADER),
            compileShader(fragment_shader_picking, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.shader_pick)

        self.uloc_pick["model"] = glGetUniformLocation(self.shader_pick, "model")
        self.uloc_pick["project"] = glGetUniformLocation(self.shader_pick, "project")
        self.uloc_pick["view"] = glGetUniformLocation(self.shader_pick, "view")

    def _create_shader_debug_picking(self) -> None:
        """Create shader for rendering shadow map."""

        self.shader_dbpi = compileProgram(
            compileShader(vertex_shader_debug_picking, GL_VERTEX_SHADER),
            compileShader(fragment_shader_debug_picking, GL_FRAGMENT_SHADER),
        )

    def evaluate_picking(self, action: Action):
        if not action.mouse_on_gui:
            self._draw_picking_texture(action)
            self._evaluate_picking(action)
        else:
            action.picking = False

    def _evaluate_picking(self, action: Action) -> None:
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        x = action.picked_x
        y = action.picked_y

        # print(x, y, interaction.width, interaction.height)

        data = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        picked_id_new = color_to_id(data)

        if picked_id_new == action.picked_id:
            action.picked_id = -1
        else:
            action.picked_id = picked_id_new
            # print(self.picked_id)

        action.picking = False

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _draw_picking_texture(self, action: Action) -> None:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Camera input
        move = action.camera.get_move_matrix()
        view = action.camera.get_view_matrix()
        proj = action.camera.get_perspective_matrix()

        # Picking pass
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO_picking)
        glEnable(GL_DEPTH_TEST)
        # glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_pick)

        glUniformMatrix4fv(self.uloc_pick["model"], 1, GL_FALSE, move)
        glUniformMatrix4fv(self.uloc_pick["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(self.uloc_pick["project"], 1, GL_FALSE, proj)

        # Draw meshes to the texture
        for mesh_gl in self.meshes:
            mesh_gl.triangles_draw_call()

    def _render_pick_texture(self, action: Action, gguip: GuiParameters) -> None:
        self._draw_picking_texture(action)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Apply the picking texture to the debug quad which spans th whole screen.
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.shader_dbpi)  # Use the debug picking shader
        glBindVertexArray(self.VAO_debug)
        glBindTexture(GL_TEXTURE_2D, self.pick_texture)

        # Draw the quad
        self._debug_quad_draw_call()
        glEnable(GL_DEPTH_TEST)

    def render(self, action: Action, gguip: GuiParameters) -> None:
        self._render_meshes(action, gguip)
        self._render_pcs(action, gguip)
        self._render_rns(action, gguip)

        self._update_light_position()
        self._update_color_caps()

    def _render_meshes(self, action: Action, gguip: GuiParameters) -> None:
        if self.guip.shading == Shading.wireframe:
            self._render_lines(action, gguip)
        elif self.guip.shading == Shading.ambient:
            self._render_ambient(action, gguip)
        elif self.guip.shading == Shading.diffuse:
            self._render_diffuse(action, gguip)
        elif self.guip.shading == Shading.wireshaded:
            self._render_wireshaded(action, gguip)
        elif self.guip.shading == Shading.shadows:
            self._render_shadows(action, gguip)
        elif self.guip.shading == Shading.picking:
            self._render_pick_texture(action, gguip)
        else:
            warning("Shading not set for model instance")
        pass

    def _render_pcs(self, action: Action, gguip: GuiParameters) -> None:
        for pc in self.pointclouds:
            guip = pc.guip
            if guip.show:
                pc.render(action, gguip)

    def _render_rns(self, action: Action, gguip: GuiParameters) -> None:
        for rn_gl in self.linestrings:
            guip = rn_gl.guip
            if guip.show:
                rn_gl.render(action, gguip)

    def _render_lines(self, action: Action, gguip: GuiParameters) -> None:
        for mesh in self.meshes:
            if mesh.guip.show:
                mesh.render_lines(action, gguip, self.guip)

    def _render_ambient(self, action: Action, gguip: GuiParameters) -> None:
        for mesh in self.meshes:
            if mesh.guip.show:
                mesh.render_ambient(action, gguip, self.guip)

    def _render_diffuse(self, action: Action, gguip: GuiParameters) -> None:
        for mesh in self.meshes:
            if mesh.guip.show:
                mesh.render_diffuse(action, self.env, gguip, self.guip)

    def _render_wireshaded(self, action: Action, gguip: GuiParameters) -> None:
        for mesh in self.meshes:
            if mesh.guip.show:
                mesh.render_wireshaded(action, self.env, gguip, self.guip)

    def _render_shadows(self, action: Action, gguip: GuiParameters) -> None:
        """Generates a shadow map and renders the mesh with shadows by sampling that
        shadow map.
        """
        if action.show_shadow_texture:
            self._render_shadows_pass1(action)
            self._render_debug_shadow_map(action)
        else:
            self._render_shadows_pass1(action)
            self._render_shadows_pass2(action, gguip)

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

        for mesh in self.meshes:
            # In this pass, only meshes that should cast shadows are added.
            if mesh.guip.show and mesh.cast_shadows:
                mesh.render_shadows_pass1(action, self.env, self.lsm)

    def _render_shadows_pass2(self, action: Action, gguip: GuiParameters) -> None:
        """Render the model with shadows by sampling the shadow map frame buffer."""
        # Second pass: Render objects with the shadow map computed in the first pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Setting default buffer
        glViewport(0, 0, action.fbuf_width, action.fbuf_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Bind the shadow map texture so that it can be sampled in the shader
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_map)

        # Set up individual mesh parameters and uniforms for rendering
        for mesh in self.meshes:
            if mesh.guip.show:
                mesh.render_shadows_pass2(action, self.env, gguip, self.guip, self.lsm)

    def _render_debug_shadow_map(self, interaction: Action) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, interaction.fbuf_width, interaction.fbuf_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_dbsh)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.shadow_depth_map)
        self._debug_quad_draw_call()

    def _debug_quad_draw_call(self) -> None:
        glBindVertexArray(self.VAO_debug)
        glDrawElements(GL_TRIANGLES, len(self.quad_indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def _update_light_position(self) -> None:
        if self.guip.animate_light:
            self.env._calc_light_position()

    def _update_color_caps(self):
        for mesh in self.meshes:
            mesh.update_color_caps()

        for pc in self.pointclouds:
            pc.update_color_caps()

        for ls in self.linestrings:
            ls.update_color_caps()
