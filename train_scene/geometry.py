"""Malhas OpenGL e geometria estatica do ambiente."""

import math
from ctypes import c_void_p

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FALSE,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glDrawElements,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glVertexAttribPointer,
)

from .math3d import scale_matrix, translation
from .settings import TRACK_END_X, TRACK_START_X, TRACK_Z


class Mesh:
    """Malha intercalada: position(0), normal(1) e uv(2)."""

    def __init__(self, vertices, indices):
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        self.index_count = len(indices)
        data = np.asarray(vertices, dtype=np.float32)
        index_data = np.asarray(indices, dtype=np.uint32)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)
        stride = 8 * data.itemsize
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(        1, 3, GL_FLOAT, GL_FALSE, stride, c_void_p(3 * data.itemsize))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(        2, 2, GL_FLOAT, GL_FALSE, stride, c_void_p(6 * data.itemsize))
        glBindVertexArray(0)

    def draw(self):
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)


def make_cube():
    faces = (
        ((0, 0, 1), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))),
        ((0, 0, -1), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1))),
        ((1, 0, 0), ((1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1))),
        ((-1, 0, 0), ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1))),
        ((0, 1, 0), ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1))),
        ((0, -1, 0), ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1))),
    )
    vertices, indices = [], []
    uvs = ((0, 0), (1, 0), (1, 1), (0, 1))
    for normal, corners in faces:
        offset = len(vertices)
        vertices.extend((*corner, *normal, *uv) for corner, uv in zip(corners, uvs))
        indices.extend((offset, offset + 1, offset + 2, offset, offset + 2, offset + 3))
    return Mesh(vertices, indices)


def make_cylinder(segments=24):
    vertices, indices = [], []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x, z = math.cos(angle), math.sin(angle)
        vertices.extend(
            (
                (x, -1, z, x, 0, z, i / segments, 0),
                (x, 1, z, x, 0, z, i / segments, 1),
            )
        )
    for i in range(segments):
        lower = i * 2
        upper = lower + 1
        next_lower = ((i + 1) % segments) * 2
        next_upper = next_lower + 1
        indices.extend((lower, upper, next_lower, upper, next_upper, next_lower))

    for y, normal_y, reverse in ((-1, -1, True), (1, 1, False)):
        center = len(vertices)
        vertices.append((0, y, 0, 0, normal_y, 0, 0.5, 0.5))
        ring = len(vertices)
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            x, z = math.cos(angle), math.sin(angle)
            vertices.append((x, y, z, 0, normal_y, 0, 0.5 + x * 0.5, 0.5 + z * 0.5))
        for i in range(segments):
            a, b = ring + i, ring + (i + 1) % segments
            indices.extend((center, a, b) if reverse else (center, b, a))
    return Mesh(vertices, indices)


def make_sphere(rings=16, segments=24):
    vertices, indices = [], []
    for row in range(rings + 1):
        v = row / rings
        latitude = math.pi * (v - 0.5)
        y = math.sin(latitude)
        radius = math.cos(latitude)
        for column in range(segments + 1):
            u = column / segments
            longitude = 2.0 * math.pi * u
            x, z = radius * math.cos(longitude), radius * math.sin(longitude)
            vertices.append((x, y, z, x, y, z, u, v))
    for row in range(rings):
        for column in range(segments):
            a = row * (segments + 1) + column
            b = a + segments + 1
            indices.extend((a, b, a + 1, a + 1, b, b + 1))
    return Mesh(vertices, indices)


def make_track_geometry():
    pieces = []
    sleeper_count = 64
    for i in range(sleeper_count):
        x = TRACK_START_X + 0.35 + i * (TRACK_END_X - TRACK_START_X - 0.70) / (sleeper_count - 1)
        sleeper = translation(x, 0.08, TRACK_Z) @ scale_matrix(0.18, 0.10, 0.85)
        pieces.append((sleeper, (0.27, 0.18, 0.10)))
    for side in (-0.55, 0.55):
        rail = (
                translation(0.0, 0.15, TRACK_Z + side)
                @ scale_matrix((TRACK_END_X - TRACK_START_X) / 2.0, 0.13, 0.12)
        )
        pieces.append((rail, (0.43, 0.48, 0.52)))
    return pieces
