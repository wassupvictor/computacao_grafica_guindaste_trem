"""Painel de controles desenhado sobre a cena OpenGL."""

import ctypes

import pygame
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_CULL_FACE,
    GL_DEPTH_TEST,
    GL_DYNAMIC_DRAW,
    GL_FLOAT,
    GL_FALSE,
    GL_FRAGMENT_SHADER,
    GL_LINEAR,
    GL_RGBA,
    GL_RGBA8,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRIANGLES,
    GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glBindBuffer,
    glBindTexture,
    glBindVertexArray,
    glBlendFunc,
    glBufferData,
    glDisable,
    glDrawArrays,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenTextures,
    glGenVertexArrays,
    glGetUniformLocation,
    glTexImage2D,
    glTexParameteri,
    glUniform1i,
    glUseProgram,
    glVertexAttribPointer,
)
from OpenGL.GL.shaders import compileProgram, compileShader


HUD_VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec2 aPosition;
layout(location = 1) in vec2 aTexCoord;
out vec2 vTexCoord;
void main() {
    vTexCoord = aTexCoord;
    gl_Position = vec4(aPosition, 0.0, 1.0);
}
"""

HUD_FRAGMENT_SHADER = """#version 330 core
in vec2 vTexCoord;
uniform sampler2D uPanel;
out vec4 fragColor;
void main() {
    fragColor = texture(uPanel, vTexCoord);
}
"""


class ControlsHud:
    WIDTH = 390
    HEIGHT = 216
    MARGIN = 16

    def __init__(self):
        self.program = compileProgram(
            compileShader(HUD_VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(HUD_FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )
        self.texture = glGenTextures(1)
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self._create_panel_texture()
        self._configure_vertex_buffer()

    def _create_panel_texture(self):
        panel = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA, 32)
        pygame.draw.rect(panel, (12, 21, 31, 218), panel.get_rect(), border_radius=10)
        pygame.draw.rect(
            panel,
            (107, 177, 197, 255),
            panel.get_rect(),
            width=2,
            border_radius=10,
        )
        title_font = pygame.font.Font(None, 28)
        body_font = pygame.font.Font(None, 23)
        panel.blit(title_font.render("CONTROLES", True, (255, 211, 105)), (14, 11))
        lines = (
            "1-5   Visões de câmera",
            "Esq / Dir   Girar a lança",
            "Cima / Baixo   Estender / recolher",
            "Espaço   Pegar / soltar caixa",
            "Linha vermelha   Mira do gancho",
            "P   Pausar / retomar",
            "F11   Tela cheia",
            "Esc   Sair",
        )
        for index, line in enumerate(lines):
            text = body_font.render(line, True, (241, 246, 249))
            panel.blit(text, (15, 43 + index * 21))

        image = pygame.image.tostring(panel, "RGBA", True)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA8,
            self.WIDTH,
            self.HEIGHT,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            image,
        )
        glBindTexture(GL_TEXTURE_2D, 0)

    def _configure_vertex_buffer(self):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 6 * 4 * 4, None, GL_DYNAMIC_DRAW)
        stride = 4 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(
            1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * 4)
        )
        glBindVertexArray(0)

    def draw(self, screen_width, screen_height):
        left = self.MARGIN
        top = self.MARGIN
        right = min(left + self.WIDTH, screen_width - self.MARGIN)
        bottom = min(top + self.HEIGHT, screen_height - self.MARGIN)
        width, height = right - left, bottom - top
        if width <= 0 or height <= 0:
            return

        x_left = 2.0 * left / screen_width - 1.0
        x_right = 2.0 * right / screen_width - 1.0
        y_top = 1.0 - 2.0 * top / screen_height
        y_bottom = 1.0 - 2.0 * bottom / screen_height
        vertices = (
            (x_left, y_bottom, 0.0, 0.0),
            (x_right, y_bottom, 1.0, 0.0),
            (x_right, y_top, 1.0, 1.0),
            (x_left, y_bottom, 0.0, 0.0),
            (x_right, y_top, 1.0, 1.0),
            (x_left, y_top, 0.0, 1.0),
        )

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(self.program)
        glUniform1i(glGetUniformLocation(self.program, "uPanel"), 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(vertices) * 4 * 4,
            (ctypes.c_float * (len(vertices) * 4))(
                *(coordinate for vertex in vertices for coordinate in vertex)
            ),
            GL_DYNAMIC_DRAW,
        )
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
