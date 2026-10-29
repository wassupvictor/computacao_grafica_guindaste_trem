import unittest

from train_scene.animation import TrainState
from train_scene.settings import (
    CARGO_WAGON_OFFSETS,
    STATION_DISTANCE,
    STOP_ADVANCES,
    TRAIN_SPEED,
    TRAVEL_LENGTH,
)


class TrainStateTests(unittest.TestCase):
    def test_motion_uses_elapsed_time_and_pause_freezes_it(self):
        state = TrainState()
        state.update(0.8, paused=False)
        self.assertAlmostEqual(state.total_distance, TRAIN_SPEED * 0.8)

        state.update(2.0, paused=True)
        self.assertAlmostEqual(state.total_distance, TRAIN_SPEED * 0.8)

    def test_train_waits_for_crane_loading_before_advancing(self):
        state = TrainState()
        first_stop = STATION_DISTANCE + STOP_ADVANCES[0]
        state.update(first_stop / TRAIN_SPEED, paused=False)
        self.assertTrue(state.stopped)
        self.assertEqual(state.loaded_wagons, 0)

        state.update(10.0, paused=False)
        self.assertTrue(state.stopped)
        self.assertEqual(state.loaded_wagons, 0)

        self.assertTrue(state.load_current_wagon(0))
        self.assertFalse(state.stopped)
        self.assertEqual(state.loaded_wagons, 1)
        self.assertEqual(state.loaded_crate_indices, [0])

        state.update(0.4, paused=False)
        self.assertAlmostEqual(
            state.lap_distance, first_stop + TRAIN_SPEED * 0.4
        )

    def test_train_finishes_at_track_end(self):
        state = TrainState(
            lap_distance=TRAVEL_LENGTH - 1.0,
            stop_index=len(CARGO_WAGON_OFFSETS),
            loaded_wagons=len(CARGO_WAGON_OFFSETS),
        )
        state.update(1.0 / TRAIN_SPEED, paused=False)

        self.assertTrue(state.finished)
        self.assertAlmostEqual(state.lap_distance, TRAVEL_LENGTH)
        state.update(1.0, paused=False)
        self.assertAlmostEqual(state.lap_distance, TRAVEL_LENGTH)


if __name__ == "__main__":
    unittest.main()
