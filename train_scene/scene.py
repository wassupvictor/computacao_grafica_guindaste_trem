"""Recursos OpenGL e composicao/renderizacao da cena."""

import math

import numpy as np
import pygame
from OpenGL.GL import (
    GL_BACK,
    GL_BLEND,
    GL_CLAMP_TO_BORDER,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_COMPONENT24,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_NEAREST,
    GL_NONE,
    GL_REPEAT,
    GL_RGBA,
    GL_RGBA8,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    GL_TEXTURE_BORDER_COLOR,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRUE,
    GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    glActiveTexture,
    glBindFramebuffer,
    glBindTexture,
    glBindVertexArray,
    glBlendFunc,
    glCheckFramebufferStatus,
    glClear,
    glClearColor,
    glCullFace,
    glDisable,
    glDrawBuffer,
    glEnable,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenTextures,
    glGenerateMipmap,
    glGetUniformLocation,
    glReadBuffer,
    glTexImage2D,
    glTexParameterfv,
    glTexParameteri,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
    glViewport,
)
from OpenGL.GL.shaders import compileProgram, compileShader

from .animation import TrainState, track_position
from .camera import Camera
from .crane import CraneController
from .geometry import make_cube, make_cylinder, make_sphere, make_track_geometry
from .hud import ControlsHud
from .math3d import (
    look_at,
    normalize,
    orthographic,
    perspective,
    rotation_x,
    rotation_y,
    rotation_z,
    scale_matrix,
    segment_model,
    translation,
)
from .settings import (
    CARGO_WAGON_OFFSETS,
    CRANE_X,
    CRANE_Z,
    CRATE_COLORS,
    CRATE_HALF_SIZE,
    CRATE_SOURCES,
    SHADOW_SIZE,
    TRACK_Z,
    WHEEL_RADIUS,
    WAGON_COLORS,
)
from .shaders import (
    DEPTH_FRAGMENT_SHADER,
    DEPTH_VERTEX_SHADER,
    FRAGMENT_SHADER,
    VERTEX_SHADER,
)


def set_matrix(program, uniform_name, matrix):
    glUniformMatrix4fv(
        glGetUniformLocation(program, uniform_name),
        1,
        GL_TRUE,
        np.asarray(matrix, dtype=np.float32),
    )


def create_train_texture():
    surface = pygame.Surface((128, 128), flags=pygame.SRCALPHA, depth=32)
    surface.fill((31, 83, 145, 255))
    pygame.draw.rect(surface, (238, 174, 48, 255), (0, 14, 128, 18))
    pygame.draw.rect(surface, (19, 46, 75, 255), (0, 96, 128, 32))
    for x in range(0, 128, 32):
        pygame.draw.rect(surface, (46, 109, 177, 255), (x, 42, 16, 45))
    image = pygame.image.tostring(surface, "RGBA", True)
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 128, 128, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glBindTexture(GL_TEXTURE_2D, 0)
    return texture


def make_shadow_target():
    framebuffer = glGenFramebuffers(1)
    depth_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, depth_texture)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, SHADOW_SIZE, SHADOW_SIZE, 0,
        GL_DEPTH_COMPONENT, GL_FLOAT, None
    )
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
    glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, (1.0, 1.0, 1.0, 1.0))
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_texture, 0)
    glDrawBuffer(GL_NONE)
    glReadBuffer(GL_NONE)
    status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    if status != GL_FRAMEBUFFER_COMPLETE:
        raise RuntimeError(f"Framebuffer de shadow mapping invalido: 0x{status:x}")
    return framebuffer, depth_texture


class Scene:
    def __init__(self):
        self.cube, self.cylinder, self.sphere = make_cube(), make_cylinder(), make_sphere()
        self.program = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )
        self.depth_program = compileProgram(
            compileShader(DEPTH_VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(DEPTH_FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )
        self.train_texture = create_train_texture()
        self.shadow_fbo, self.shadow_texture = make_shadow_target()
        self.track_pieces = make_track_geometry()
        self.controls_hud = ControlsHud()
        self.train, self.camera, self.crane, self.paused = (
            TrainState(),
            Camera(),
            CraneController(),
            False,
        )
        self.light_direction = normalize((-0.45, -1.0, -0.35))
        light_eye = -self.light_direction * 24.0
        self.light_space = orthographic(-28, 28, -18, 18, 1, 70) @ look_at(
            light_eye, (0, 0, 5), (0, 1, 0)
        )
        self.ground_model = (
                translation(0, -0.20, TRACK_Z) @ scale_matrix(25.0, 0.18, 7.0)
        )
        self.platform_model = (
                translation(0, 0.10, TRACK_Z + 1.55) @ scale_matrix(2.65, 0.18, 0.72)
        )
        self.signal_pole_model = (
                translation(2.3, 1.20, TRACK_Z + 1.55) @ scale_matrix(0.10, 1.25, 0.10)
        )
        self.signal_head_model = (
                translation(2.3, 2.52, TRACK_Z + 1.55) @ scale_matrix(0.28, 0.38, 0.25)
        )

    def _draw(self, mesh, model, color, textured=False, emissive=0.0, alpha=1.0):
        glUniformMatrix4fv(glGetUniformLocation(self.program, "uModel"), 1, GL_TRUE, model)
        glUniform3f(glGetUniformLocation(self.program, "uBaseColor"), *color)
        glUniform1i(glGetUniformLocation(self.program, "uUseTexture"), int(textured))
        glUniform1f(glGetUniformLocation(self.program, "uEmissive"), emissive)
        glUniform1f(glGetUniformLocation(self.program, "uAlpha"), alpha)
        glUniform1f(glGetUniformLocation(self.program, "uShininess"), 36.0)
        if textured:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.train_texture)
            glUniform1i(glGetUniformLocation(self.program, "uColorTexture"), 0)
        mesh.draw()

    def _draw_shadow(self, mesh, model):
        glUniformMatrix4fv(
            glGetUniformLocation(self.depth_program, "uModel"), 1, GL_TRUE, model
        )
        mesh.draw()

    def _train_parts(self):
        position = track_position(self.train.lap_distance)
        root = translation(*position)
        wheel_rotation = self.train.wheel_distance / WHEEL_RADIUS
        parts = []

        def add(mesh, local, color, textured=False, emissive=0.0):
            parts.append((mesh, root @ local, color, textured, emissive))

        add(
            self.cube,
            translation(0, 0.54, 0) @ scale_matrix(1.12, 0.20, 0.53),
            (0.12, 0.15, 0.18),
        )
        add(
            self.cube,
            translation(0, 0.98, 0) @ scale_matrix(1.42, 0.45, 0.68),
            (1, 1, 1),
            True,
        )
        add(
            self.cube,
            translation(-0.15, 1.46, 0) @ scale_matrix(0.85, 0.12, 0.62),
            (0.16, 0.20, 0.24),
        )
        add(
            self.cube,
            translation(0, 0.69, 0) @ scale_matrix(1.50, 0.07, 0.72),
            (0.78, 0.50, 0.14),
        )
        for side in (-1, 1):
            add(
                self.cube,
                translation(-0.05, 0.92, side * 0.695)
                @ scale_matrix(1.12, 0.045, 0.025),
                (0.93, 0.65, 0.20),
            )
        add(
            self.cylinder,
            translation(0.62, 1.57, 0) @ scale_matrix(0.13, 0.26, 0.13),
            (0.13, 0.16, 0.18),
        )
        add(
            self.cylinder,
            translation(0.62, 1.80, 0) @ scale_matrix(0.19, 0.055, 0.19),
            (0.13, 0.16, 0.18),
        )
        for x in (-0.55, -0.05):
            add(
                self.sphere,
                translation(x, 1.48, 0) @ scale_matrix(0.12, 0.10, 0.12),
                (0.86, 0.61, 0.18),
            )

        for x in (-0.78, -0.18, 0.42):
            for side in (-1, 1):
                add(
                    self.cube,
                    translation(x, 1.18, side * 0.688) @ scale_matrix(0.22, 0.20, 0.025),
                    (0.12, 0.52, 0.72),
                )
        add(self.cube, translation(1.435, 1.04, 0) @ scale_matrix(0.025, 0.26, 0.36), (0.60, 0.82, 0.90))
        add(self.cube, translation(1.47, 0.69, 0) @ scale_matrix(0.13, 0.08, 0.58), (0.18, 0.20, 0.21))
        for grille_z in (-0.38, -0.19, 0.0, 0.19, 0.38):
            add(
                self.cube,
                translation(1.51, 0.83, grille_z)
                @ scale_matrix(0.025, 0.14, 0.025),
                (0.72, 0.76, 0.78),
            )
        add(
            self.sphere,
            translation(1.49, 1.38, 0) @ scale_matrix(0.13, 0.13, 0.13),
            (1.0, 0.83, 0.40),
            emissive=0.65,
        )
        for side in (-1, 1):
            add(
                self.sphere,
                translation(1.48, 1.12, side * 0.43) @ scale_matrix(0.09, 0.09, 0.09),
                (1.0, 0.88, 0.55),
                emissive=0.22,
            )
            for x in (-0.82, 0.82):
                wheel_center_y = 0.60
                wheel_center_z = side * 0.59
                wheel = (
                        translation(x, wheel_center_y, wheel_center_z)
                        @ rotation_x(math.pi / 2)
                        @ rotation_y(wheel_rotation)
                        @ scale_matrix(WHEEL_RADIUS, 0.15, WHEEL_RADIUS)
                )
                add(self.cylinder, wheel, (0.12, 0.13, 0.14))
                wheel_frame = (
                        translation(x, wheel_center_y, wheel_center_z)
                        @ rotation_x(math.pi / 2)
                        @ rotation_y(wheel_rotation)
                )
                for spoke_index in range(4):
                    spoke_angle = spoke_index * math.pi / 2
                    spoke = (
                            wheel_frame
                            @ translation(
                        WHEEL_RADIUS * 0.48 * math.cos(spoke_angle),
                        WHEEL_RADIUS * 0.48 * math.sin(spoke_angle),
                        side * 0.153,
                    )
                            @ rotation_z(spoke_angle)
                            @ scale_matrix(WHEEL_RADIUS * 0.48, 0.025, 0.035)
                    )
                    add(self.cube, spoke, (0.76, 0.66, 0.38))
                hub = (
                        translation(x, wheel_center_y, side * 0.68)
                        @ rotation_x(math.pi / 2)
                        @ scale_matrix(0.10, 0.10, 0.025)
                )
                add(self.cylinder, hub, (0.72, 0.65, 0.40))
        for wagon_index, offset in enumerate(CARGO_WAGON_OFFSETS):
            wagon = root @ translation(offset, 0, 0)
            cargo_color = WAGON_COLORS[wagon_index]

            def add_cargo(mesh, local, color):
                parts.append((mesh, wagon @ local, color, False, 0.0))

            add_cargo(
                self.cube,
                translation(0, 0.55, 0) @ scale_matrix(1.12, 0.15, 0.55),
                (0.16, 0.18, 0.20),
            )
            for side in (-1, 1):
                add_cargo(
                    self.cube,
                    translation(0, 0.99, side * 0.49)
                    @ scale_matrix(1.05, 0.29, 0.06),
                    cargo_color,
                )
            for end in (-1, 1):
                add_cargo(
                    self.cube,
                    translation(end * 1.05, 0.99, 0)
                    @ scale_matrix(0.06, 0.29, 0.49),
                    cargo_color,
                )
            for side in (-1, 1):
                add_cargo(
                    self.cube,
                    translation(0, 1.30, side * 0.49)
                    @ scale_matrix(1.05, 0.16, 0.06),
                    cargo_color,
                )
            for end in (-1, 1):
                add_cargo(
                    self.cube,
                    translation(end * 1.05, 1.30, 0)
                    @ scale_matrix(0.06, 0.16, 0.49),
                    cargo_color,
                )
            if wagon_index < len(self.train.loaded_crate_indices):
                crate_index = self.train.loaded_crate_indices[wagon_index]
                add_cargo(
                    self.cube,
                    translation(0, 0.94, 0) @ scale_matrix(*CRATE_HALF_SIZE),
                    CRATE_COLORS[crate_index],
                )
            for side in (-1, 1):
                for axle_x in (-0.72, 0.72):
                    wheel_y = 0.37
                    wheel_z = side * 0.59
                    cargo_wheel = (
                            translation(axle_x, wheel_y, wheel_z)
                            @ rotation_x(math.pi / 2)
                            @ rotation_y(wheel_rotation)
                            @ scale_matrix(WHEEL_RADIUS, 0.15, WHEEL_RADIUS)
                    )
                    add_cargo(self.cylinder, cargo_wheel, (0.12, 0.13, 0.14))
                    wheel_face = (
                            translation(axle_x, wheel_y, side * 0.68)
                            @ rotation_x(math.pi / 2)
                            @ scale_matrix(0.10, 0.10, 0.025)
                    )
                    add_cargo(self.cylinder, wheel_face, (0.72, 0.65, 0.40))
        return parts

    def _crane_parts(self):
        parts = []

        def add(mesh, model, color, emissive=0.0):
            parts.append((mesh, model, color, False, emissive))

        chassis_color = (0.88, 0.55, 0.12)
        dark_metal = (0.16, 0.19, 0.21)
        add(
            self.cube,
            translation(CRANE_X, 0.52, CRANE_Z)
            @ scale_matrix(1.05, 0.20, 0.72),
            dark_metal,
        )
        add(
            self.cube,
            translation(CRANE_X, 0.78, CRANE_Z)
            @ scale_matrix(1.35, 0.12, 0.82),
            chassis_color,
        )
        add(
            self.cylinder,
            translation(CRANE_X + 0.12, 0.94, CRANE_Z)
            @ scale_matrix(0.48, 0.12, 0.48),
            (0.20, 0.23, 0.25),
        )
        add(
            self.cylinder,
            translation(CRANE_X + 0.12, 1.06, CRANE_Z)
            @ scale_matrix(0.24, 0.10, 0.24),
            (0.95, 0.68, 0.18),
        )
        add(
            self.cube,
            translation(CRANE_X - 0.62, 1.48, CRANE_Z)
            @ scale_matrix(0.43, 0.60, 0.55),
            chassis_color,
        )
        add(
            self.cube,
            translation(CRANE_X - 0.62, 1.52, CRANE_Z + 0.56)
            @ scale_matrix(0.29, 0.30, 0.025),
            (0.16, 0.53, 0.68),
        )
        add(
            self.cube,
            translation(CRANE_X - 0.62, 1.48, CRANE_Z - 0.56)
            @ scale_matrix(0.29, 0.30, 0.025),
            (0.16, 0.53, 0.68),
        )
        add(
            self.cube,
            translation(CRANE_X - 0.62, 2.10, CRANE_Z)
            @ scale_matrix(0.48, 0.08, 0.60),
            (0.17, 0.20, 0.22),
        )
        add(
            self.cube,
            translation(CRANE_X - 0.62, 1.96, CRANE_Z)
            @ scale_matrix(0.52, 0.045, 0.64),
            chassis_color,
        )
        for side in (-1, 1):
            for axle_x in (-0.78, 0.78):
                wheel = (
                        translation(CRANE_X + axle_x, 0.34, CRANE_Z + side * 0.72)
                        @ rotation_x(math.pi / 2)
                        @ scale_matrix(0.33, 0.16, 0.33)
                )
                add(self.cylinder, wheel, dark_metal)
                hub = (
                    translation(CRANE_X + axle_x, 0.34, CRANE_Z + side * 0.88)
                    @ rotation_x(math.pi / 2)
                    @ scale_matrix(0.13, 0.13, 0.035)
                )
                add(self.cylinder, hub, (0.91, 0.63, 0.18))

        for side in (-1, 1):
            add(
                self.cube,
                translation(CRANE_X, 0.60, CRANE_Z + side * 0.82)
                @ scale_matrix(1.32, 0.07, 0.06),
                (0.20, 0.23, 0.25),
            )
            for x in (-0.72, 0.72):
                add(
                    self.cube,
                    translation(CRANE_X + x, 0.69, CRANE_Z + side * 0.82)
                    @ scale_matrix(0.11, 0.035, 0.07),
                    (0.92, 0.68, 0.20),
                )

        hook_point = self.crane.hook_position
        attached = self.crane.has_crate
        for index, position in enumerate(CRATE_SOURCES):
            if index in self.train.loaded_crate_indices:
                continue
            if index == self.crane.active_crate and attached:
                continue
            if index in self.crane.dropped_crates:
                continue
            add(
                self.cube,
                translation(*position) @ scale_matrix(*CRATE_HALF_SIZE),
                CRATE_COLORS[index],
            )
        for index, position in self.crane.dropped_crates.items():
            add(
                self.cube,
                translation(*position) @ scale_matrix(*CRATE_HALF_SIZE),
                CRATE_COLORS[index],
            )
        if attached:
            add(
                self.cube,
                translation(*hook_point) @ scale_matrix(*CRATE_HALF_SIZE),
                CRATE_COLORS[self.crane.active_crate],
            )

        pivot = np.array((CRANE_X + 0.10, 2.15, CRANE_Z), dtype=np.float32)
        trolley = np.array(
            (hook_point[0], max(2.4, hook_point[1] + 0.88), hook_point[2]),
            dtype=np.float32,
        )
        add(self.cube, segment_model(pivot, trolley, 0.14), chassis_color)
        boom_offset = np.array((0.20, 0.0, 0.0), dtype=np.float32)
        for side in (-1, 1):
            rail_start = pivot + boom_offset * side
            rail_end = trolley + boom_offset * side
            add(
                self.cube,
                segment_model(rail_start, rail_end, 0.045),
                dark_metal,
            )
        for fraction in (0.35, 0.7):
            cross_center = pivot + (trolley - pivot) * fraction
            add(
                self.cube,
                segment_model(
                    cross_center - boom_offset,
                    cross_center + boom_offset,
                    0.035,
                ),
                (0.94, 0.70, 0.24),
            )
        add(
            self.cylinder,
            translation(*pivot)
            @ rotation_x(math.pi / 2)
            @ scale_matrix(0.23, 0.23, 0.16),
            dark_metal,
        )
        add(
            self.cube,
            translation(*trolley) @ scale_matrix(0.22, 0.13, 0.20),
            dark_metal,
        )
        cable_end = hook_point.copy()
        cable_end[1] += CRATE_HALF_SIZE[1] if attached else 0.10
        if trolley[1] - cable_end[1] > 0.08:
            add(
                self.cube,
                segment_model(trolley, cable_end, 0.035),
                dark_metal,
            )
        add(
            self.cube,
            translation(*cable_end) @ scale_matrix(0.12, 0.06, 0.12),
            chassis_color,
        )
        return parts

    def _scene_parts(self):
        parts = [(self.cube, self.ground_model, (0.32, 0.39, 0.30), False, 0.0)]
        parts.extend(
            (self.cube, model, color, False, 0.0) for model, color in self.track_pieces
        )
        parts.extend(
            (
                (self.cube, self.platform_model, (0.70, 0.66, 0.56), False, 0.0),
                (self.cube, self.signal_pole_model, (0.20, 0.22, 0.24), False, 0.0),
                (self.cube, self.signal_head_model, (0.20, 0.22, 0.24), False, 0.0),
            )
        )
        lamp_color = (0.20, 0.95, 0.35) if self.train.stopped else (1.0, 0.48, 0.08)
        lamp = (
                translation(2.3, 2.55, TRACK_Z + 1.26)
                @ scale_matrix(0.13, 0.14, 0.08)
        )
        parts.append((self.sphere, lamp, lamp_color, False, 0.75))
        parts.extend(self._crane_parts())
        parts.extend(self._train_parts())
        return parts

    def render(self, width, height):
        parts = self._scene_parts()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        glViewport(0, 0, SHADOW_SIZE, SHADOW_SIZE)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.depth_program)
        set_matrix(self.depth_program, "uLightSpace", self.light_space)
        for mesh, model, _color, _textured, _emissive in parts:
            self._draw_shadow(mesh, model)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, width, height)
        glClearColor(0.48, 0.70, 0.83, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.program)
        set_matrix(self.program, "uView", self.camera.view_matrix())
        set_matrix(self.program, "uProjection", perspective(48.0, width / max(height, 1), 0.1, 100.0))
        set_matrix(self.program, "uLightSpace", self.light_space)
        glUniform3f(glGetUniformLocation(self.program, "uLightDirection"), *self.light_direction)
        glUniform3f(glGetUniformLocation(self.program, "uCameraPosition"), *self.camera.position)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_texture)
        glUniform1i(glGetUniformLocation(self.program, "uShadowMap"), 1)
        for mesh, model, color, textured, emissive in parts:
            self._draw(mesh, model, color, textured, emissive)
        aim_line_height = 1.35
        aim_line = (
            translation(
                float(self.crane.hook_position[0]),
                aim_line_height,
                float(self.crane.hook_position[2]),
            )
            @ scale_matrix(0.035, aim_line_height, 0.035)
        )
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._draw(
            self.cube,
            aim_line,
            (1.0, 0.04, 0.04),
            emissive=0.65,
            alpha=0.2,
        )
        glDisable(GL_BLEND)
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindVertexArray(0)
        glUseProgram(0)
        self.controls_hud.draw(width, height)
