import math
import unittest

import pygame

from train_scene.animation import TrainState
from train_scene.crane import CraneController
from train_scene.settings import CRANE_X, CRANE_Z, CRATE_SOURCES


class NoKeys:
    def __getitem__(self, _key):
        return False


class PressedKey:
    def __init__(self, key):
        self.key = key

    def __getitem__(self, key):
        return key == self.key


class CraneControllerTests(unittest.TestCase):
    def test_arrow_keys_rotate_and_extend_the_crane(self):
        crane = CraneController()
        initial_angle, initial_reach = crane.angle, crane.reach

        crane.update(PressedKey(pygame.K_RIGHT), 0.5, TrainState())
        crane.update(PressedKey(pygame.K_UP), 0.5, TrainState())

        self.assertAlmostEqual(crane.angle, initial_angle + 0.7)
        self.assertAlmostEqual(crane.reach, initial_reach + 0.75)

    def test_space_picks_box_then_lowers_it_into_waiting_wagon(self):
        train = TrainState(waiting_for_crane=True, stop_index=1)
        crane = CraneController()

        self.assertTrue(crane.press_space(train))
        crane.update(NoKeys(), 2.0, train)
        self.assertEqual(crane.state, "carrying")
        self.assertEqual(train.loaded_wagons, 0)

        crane.angle = 0.0
        crane.reach = 3.2
        self.assertTrue(crane.press_space(train))
        crane.update(NoKeys(), 0.8, train)

        self.assertEqual(train.loaded_wagons, 1)
        self.assertFalse(train.stopped)
        self.assertNotIn(0, crane.dropped_crates)

    def test_matching_crate_can_be_loaded_at_its_wagon_stop(self):
        train = TrainState(
            waiting_for_crane=True,
            stop_index=2,
            loaded_wagons=1,
            loaded_crate_indices=[0],
        )
        crane = CraneController()
        second_source = CRATE_SOURCES[1]
        crane.angle = math.atan2(
            second_source[0] - CRANE_X,
            second_source[2] - CRANE_Z,
        )
        crane.reach = math.hypot(
            second_source[0] - CRANE_X,
            second_source[2] - CRANE_Z,
        )

        self.assertTrue(crane.press_space(train))
        self.assertEqual(crane.active_crate, 1)
        crane.update(NoKeys(), 2.0, train)
        crane.angle = 0.0
        crane.reach = 3.2
        self.assertTrue(crane.press_space(train))
        crane.update(NoKeys(), 0.8, train)

        self.assertEqual(train.loaded_crate_indices, [0, 1])
        self.assertEqual(train.loaded_wagons, 2)
        self.assertFalse(train.stopped)

    def test_wrong_color_cannot_be_dropped_into_waiting_wagon(self):
        train = TrainState(waiting_for_crane=True, stop_index=1)
        crane = CraneController()
        second_source = CRATE_SOURCES[1]
        crane.angle = math.atan2(
            second_source[0] - CRANE_X,
            second_source[2] - CRANE_Z,
        )
        crane.reach = math.hypot(
            second_source[0] - CRANE_X,
            second_source[2] - CRANE_Z,
        )
        self.assertTrue(crane.press_space(train))
        self.assertEqual(crane.active_crate, 1)
        crane.update(NoKeys(), 2.0, train)
        crane.angle = 0.0
        crane.reach = 3.2

        self.assertFalse(crane.press_space(train))
        self.assertEqual(crane.state, "carrying")
        self.assertEqual(train.loaded_wagons, 0)
        self.assertTrue(train.stopped)

    def test_crate_dropped_outside_wagon_can_be_picked_up_again(self):
        train = TrainState(waiting_for_crane=True, stop_index=1)
        crane = CraneController()
        self.assertTrue(crane.press_space(train))
        crane.update(NoKeys(), 2.0, train)

        crane.angle = 1.0
        crane.reach = 2.0
        self.assertTrue(crane.press_space(train))
        crane.update(NoKeys(), 2.0, train)
        self.assertIn(0, crane.dropped_crates)
        self.assertEqual(train.loaded_wagons, 0)

        dropped_position = crane.dropped_crates[0]
        crane.angle = math.atan2(
            float(dropped_position[0] - CRANE_X),
            float(dropped_position[2] - CRANE_Z),
        )
        crane.reach = float(
            (
                (dropped_position[0] - CRANE_X) ** 2
                + (dropped_position[2] - CRANE_Z) ** 2
            )
            ** 0.5
        )
        crane.update(NoKeys(), 2.0, train)
        self.assertTrue(crane.press_space(train))
        crane.update(NoKeys(), 2.0, train)

        self.assertNotIn(0, crane.dropped_crates)
        self.assertEqual(crane.state, "carrying")

    def test_space_only_picks_the_box_at_the_hook(self):
        train = TrainState(waiting_for_crane=True, stop_index=1)
        crane = CraneController()
        crane.angle = 0.0

        self.assertFalse(crane.press_space(train))
        self.assertEqual(crane.state, "idle")
        self.assertIsNone(crane.active_crate)


if __name__ == "__main__":
    unittest.main()
