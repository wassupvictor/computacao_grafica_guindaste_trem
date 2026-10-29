"""Estado temporal do trem, paradas e carregamento."""

from dataclasses import dataclass, field

import numpy as np

from .settings import (
    STATION_DISTANCE,
    STOP_ADVANCES,
    CRATE_COLORS,
    TRAIN_SPEED,
    TRAIN_START_X,
    TRACK_Z,
    TRAVEL_LENGTH,
    WAGON_COLORS,
)


def track_position(distance):
    return np.array(
        (TRAIN_START_X + distance, 0.0, TRACK_Z),
        dtype=np.float32,
    )


@dataclass
class TrainState:
    lap_distance: float = 0.0
    total_distance: float = 0.0
    wheel_distance: float = 0.0
    direction: int = 1
    stop_index: int = 0
    loaded_wagons: int = 0
    loaded_crate_indices: list[int] = field(default_factory=list)
    finished: bool = False
    waiting_for_crane: bool = False

    @property
    def stopped(self):
        return self.waiting_for_crane

    def load_current_wagon(self, crate_index):
        if not self.waiting_for_crane or self.stop_index <= 0:
            return False
        wagon_index = self.stop_index - 1
        if not 0 <= crate_index < len(CRATE_COLORS):
            return False
        if CRATE_COLORS[crate_index] != WAGON_COLORS[wagon_index]:
            return False
        if crate_index in self.loaded_crate_indices:
            return False
        self.loaded_crate_indices.append(crate_index)
        self.loaded_wagons = self.stop_index
        self.waiting_for_crane = False
        return True

    def update(self, delta_time, paused):
        if paused or self.finished:
            return
        remaining_time = delta_time
        while remaining_time > 0.0:
            if self.stopped:
                break
            if self.direction > 0:
                if self.stop_index < len(STOP_ADVANCES):
                    target_distance = (
                            STATION_DISTANCE + STOP_ADVANCES[self.stop_index]
                    )
                else:
                    target_distance = TRAVEL_LENGTH
            else:
                target_distance = (
                    STATION_DISTANCE if self.lap_distance > STATION_DISTANCE else 0.0
                )
            distance_to_target = abs(target_distance - self.lap_distance)
            seconds_to_target = distance_to_target / TRAIN_SPEED
            if remaining_time < seconds_to_target:
                distance = TRAIN_SPEED * remaining_time
                self.lap_distance += self.direction * distance
                self.total_distance += distance
                self.wheel_distance += self.direction * distance
                remaining_time = 0.0
            else:
                distance = distance_to_target
                self.lap_distance = target_distance
                self.total_distance += distance
                self.wheel_distance += self.direction * distance
                remaining_time -= seconds_to_target
                if self.stop_index < len(STOP_ADVANCES):
                    cargo_index = self.stop_index
                    self.stop_index += 1
                    if 0 <= cargo_index < self.loaded_wagons:
                        continue
                    self.waiting_for_crane = True
                    break
                else:
                    self.finished = True
                    break
