import unittest

from train_scene.camera import Camera
from train_scene.settings import TRACK_Z


class CameraTests(unittest.TestCase):
    def test_camera_target_is_centered_on_station_platform(self):
        self.assertAlmostEqual(Camera.TARGET[0], 0.0)
        self.assertAlmostEqual(Camera.TARGET[2], TRACK_Z + 1.55)

    def test_presets_are_zoomed_to_the_platform(self):
        for offset in Camera.VIEW_OFFSETS:
            with self.subTest(offset=offset):
                self.assertLess(sum(component**2 for component in offset) ** 0.5, 25)

    def test_each_preset_looks_at_scene_target(self):
        camera = Camera()

        for view_index in range(len(camera.VIEW_OFFSETS)):
            with self.subTest(view_index=view_index):
                camera.set_view(view_index)
                direction_to_target = camera.TARGET - camera.position
                direction_to_target /= (direction_to_target ** 2).sum() ** 0.5

                self.assertEqual(camera.view_index, view_index)
                self.assertTrue(
                    (abs(camera.forward() - direction_to_target) < 1e-5).all()
                )

    def test_top_view_is_above_scene_and_invalid_preset_is_rejected(self):
        camera = Camera()
        camera.set_view(4)
        self.assertGreater(camera.position[1], camera.TARGET[1])
        self.assertLess(camera.forward()[1], -0.99)

        with self.assertRaises(ValueError):
            camera.set_view(5)


if __name__ == "__main__":
    unittest.main()
