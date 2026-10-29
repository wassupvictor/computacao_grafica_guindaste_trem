"""Controles manuais e estado de operacao do guindaste."""

import math

import numpy as np
import pygame

from .settings import (
    CRANE_X,
    CRANE_Z,
    CRATE_COLORS,
    CRATE_HALF_SIZE,
    CRATE_SOURCES,
    TRACK_Z,
    WAGON_COLORS,
)


class CraneController:
    MIN_REACH = 1.0
    MAX_REACH = 4.0
    HOOK_TOP = 3.0
    ROTATION_SPEED = 1.4
    REACH_SPEED = 1.5
    WINCH_SPEED = 2.8
    PICKUP_TOLERANCE = 0.55
    WAGON_HALF_WIDTH = 0.9
    WAGON_HALF_DEPTH = 0.38

    def __init__(self):
        first_source = np.asarray(CRATE_SOURCES[0], dtype=np.float32)
        relative = first_source - (CRANE_X, first_source[1], CRANE_Z)
        self.angle = math.atan2(float(relative[0]), float(relative[2]))
        self.reach = float(np.linalg.norm(relative[[0, 2]]))
        self.hook_y = self.HOOK_TOP
        self.state = "idle"
        self.active_crate = None
        self.pick_source = None
        self.dropped_crates = {}
        self.drop_target_y = None

    @property
    def has_crate(self):
        return self.state in ("lifting", "carrying", "lowering_to_drop")

    @property
    def hook_position(self):
        return np.array(
            (
                CRANE_X + math.sin(self.angle) * self.reach,
                self.hook_y,
                CRANE_Z + math.cos(self.angle) * self.reach,
            ),
            dtype=np.float32,
        )

    def update(self, keys, delta_time, train):
        if self.state in ("idle", "carrying"):
            self.angle += (
                int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            ) * self.ROTATION_SPEED * delta_time
            self.reach += (
                int(keys[pygame.K_UP]) - int(keys[pygame.K_DOWN])
            ) * self.REACH_SPEED * delta_time
            self.reach = max(self.MIN_REACH, min(self.MAX_REACH, self.reach))
        self._advance_action(delta_time, train)

    def press_space(self, train):
        if self.state == "idle":
            hook_position = self.hook_position
            available_crates = (
                index
                for index in range(len(CRATE_SOURCES))
                if index not in train.loaded_crate_indices
            )
            candidates = [
                (
                    float(
                        np.linalg.norm(
                            hook_position[[0, 2]]
                            - np.asarray(
                                self.dropped_crates.get(
                                    index, CRATE_SOURCES[index]
                                ),
                                dtype=np.float32,
                            )[[0, 2]]
                        )
                    ),
                    index,
                )
                for index in available_crates
            ]
            if not candidates:
                return False
            horizontal_distance, crate_index = min(candidates)
            if horizontal_distance > self.PICKUP_TOLERANCE:
                return False
            source = np.asarray(
                self.dropped_crates.get(crate_index, CRATE_SOURCES[crate_index]),
                dtype=np.float32,
            )
            self.active_crate = crate_index
            self.pick_source = source
            self.state = "lowering_to_pick"
            return True

        if self.state == "carrying":
            over_wagon = train.stopped and self._over_wagon(self.hook_position)
            if over_wagon:
                wagon_index = train.stop_index - 1
                wagon_color = WAGON_COLORS[wagon_index]
                crate_color = CRATE_COLORS[self.active_crate]
                if crate_color != wagon_color:
                    return False
                self.drop_target_y = 0.94
            else:
                self.drop_target_y = CRATE_HALF_SIZE[1]
            self.state = "lowering_to_drop"
            return True

        return False

    def _over_wagon(self, position):
        return (
            abs(float(position[0])) <= self.WAGON_HALF_WIDTH
            and abs(float(position[2]) - TRACK_Z) <= self.WAGON_HALF_DEPTH
        )

    def _advance_action(self, delta_time, train):
        remaining_time = delta_time
        while remaining_time > 0.0:
            if self.state == "lowering_to_pick":
                target_y = float(self.pick_source[1])
                direction = -1
            elif self.state == "lifting":
                target_y = self.HOOK_TOP
                direction = 1
            elif self.state == "lowering_to_drop":
                target_y = self.drop_target_y
                direction = -1
            elif self.state == "raising_after_drop":
                target_y = self.HOOK_TOP
                direction = 1
            else:
                return

            distance = abs(target_y - self.hook_y)
            if distance > 1e-6:
                consumed = min(remaining_time, distance / self.WINCH_SPEED)
                self.hook_y += direction * self.WINCH_SPEED * consumed
                remaining_time -= consumed
                if consumed < distance / self.WINCH_SPEED:
                    return

            if self.state == "lowering_to_pick":
                self.dropped_crates.pop(self.active_crate, None)
                self.state = "lifting"
            elif self.state == "lifting":
                self.state = "carrying"
                return
            elif self.state == "lowering_to_drop":
                drop_position = self.hook_position.copy()
                loaded = (
                    self.drop_target_y == 0.94
                    and self._over_wagon(drop_position)
                    and train.load_current_wagon(self.active_crate)
                )
                if not loaded:
                    drop_position[1] = CRATE_HALF_SIZE[1]
                    self.dropped_crates[self.active_crate] = drop_position
                self.state = "raising_after_drop"
            elif self.state == "raising_after_drop":
                self.active_crate = None
                self.pick_source = None
                self.drop_target_y = None
                self.state = "idle"
                return
