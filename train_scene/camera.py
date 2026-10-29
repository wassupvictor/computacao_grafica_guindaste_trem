"""Cinco posicoes fixas de camera selecionaveis pelo teclado."""

import math

import numpy as np

from .math3d import look_at, normalize
from .settings import TRACK_Z


class Camera:
    TARGET = np.array((0.0, 0.8, TRACK_Z + 1.55), dtype=np.float32)
    VIEW_OFFSETS = (
        (0.0, 8.0, 22.0),
        (0.0, 8.0, -22.0),
        (18.0, 8.0, 0.0),
        (-18.0, 8.0, 0.0),
        (0.0, 20.0, 1.0),
    )

    def __init__(self):
        self.position = np.zeros(3, dtype=np.float32)
        self.yaw, self.pitch = 0.0, 0.0
        self.view_index = 0
        self.set_view(0)

    def forward(self):
        return normalize(
            (
                math.sin(self.yaw) * math.cos(self.pitch),
                math.sin(self.pitch),
                -math.cos(self.yaw) * math.cos(self.pitch),
            )
        )

    def set_view(self, view_index):
        if not 0 <= view_index < len(self.VIEW_OFFSETS):
            raise ValueError(f"Posicao de camera invalida: {view_index}")
        self.view_index = view_index
        self.position = self.TARGET + np.asarray(
            self.VIEW_OFFSETS[view_index], dtype=np.float32
        )
        direction = normalize(self.TARGET - self.position)
        self.yaw = math.atan2(float(direction[0]), float(-direction[2]))
        self.pitch = math.asin(float(direction[1]))

    def view_matrix(self):
        return look_at(self.position, self.position + self.forward(), (0, 1, 0))
