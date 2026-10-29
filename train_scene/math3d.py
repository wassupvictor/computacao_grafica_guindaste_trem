"""Operacoes matriciais usadas pela camera e pelos modelos."""

import math

import numpy as np


def translation(x, y, z):
    matrix = np.identity(4, dtype=np.float32)
    matrix[:3, 3] = (x, y, z)
    return matrix


def scale_matrix(x, y, z):
    return np.diag((x, y, z, 1.0)).astype(np.float32)


def rotation_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array(
        ((1, 0, 0, 0), (0, c, -s, 0), (0, s, c, 0), (0, 0, 0, 1)),
        dtype=np.float32,
    )


def rotation_y(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array(
        ((c, 0, s, 0), (0, 1, 0, 0), (-s, 0, c, 0), (0, 0, 0, 1)),
        dtype=np.float32,
    )


def rotation_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array(
        ((c, -s, 0, 0), (s, c, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
        dtype=np.float32,
    )


def segment_model(start, end, width, depth=None):
    start = np.asarray(start, dtype=np.float32)
    end = np.asarray(end, dtype=np.float32)
    vector = end - start
    length = float(np.linalg.norm(vector))
    if length < 1e-6:
        raise ValueError("Um segmento precisa ter comprimento positivo.")
    direction = vector / length
    up = np.array((0.0, 1.0, 0.0), dtype=np.float32)
    cross = np.cross(up, direction)
    sine = float(np.linalg.norm(cross))
    cosine = float(np.dot(up, direction))
    if sine < 1e-6:
        rotation = np.identity(4, dtype=np.float32)
        if cosine < 0:
            rotation = rotation_x(math.pi)
    else:
        x, y, z = cross / sine
        skew = np.array(
            ((0, -z, y), (z, 0, -x), (-y, x, 0)),
            dtype=np.float32,
        )
        rotation = np.identity(4, dtype=np.float32)
        rotation[:3, :3] += skew * sine + (skew @ skew) * (1.0 - cosine)
    half_depth = width if depth is None else depth
    midpoint = (start + end) / 2.0
    return (
            translation(*midpoint)
            @ rotation
            @ scale_matrix(width, length / 2.0, half_depth)
    )


def normalize(vector):
    vector = np.asarray(vector, dtype=np.float32)
    length = float(np.linalg.norm(vector))
    if length < 1e-8:
        raise ValueError("Nao e possivel normalizar um vetor nulo.")
    return vector / length


def perspective(fov_degrees, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_degrees) / 2.0)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = f / aspect
    matrix[1, 1] = f
    matrix[2, 2] = (far + near) / (near - far)
    matrix[2, 3] = (2.0 * far * near) / (near - far)
    matrix[3, 2] = -1.0
    return matrix


def look_at(eye, target, up):
    forward = normalize(np.asarray(target, dtype=np.float32) - eye)
    side = normalize(np.cross(forward, up))
    corrected_up = np.cross(side, forward)
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, :3] = side
    matrix[1, :3] = corrected_up
    matrix[2, :3] = -forward
    matrix[0, 3] = -np.dot(side, eye)
    matrix[1, 3] = -np.dot(corrected_up, eye)
    matrix[2, 3] = np.dot(forward, eye)
    return matrix


def orthographic(left, right, bottom, top, near, far):
    matrix = np.identity(4, dtype=np.float32)
    matrix[0, 0] = 2.0 / (right - left)
    matrix[1, 1] = 2.0 / (top - bottom)
    matrix[2, 2] = -2.0 / (far - near)
    matrix[0, 3] = -(right + left) / (right - left)
    matrix[1, 3] = -(top + bottom) / (top - bottom)
    matrix[2, 3] = -(far + near) / (far - near)
    return matrix
