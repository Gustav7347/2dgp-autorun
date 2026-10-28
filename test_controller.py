import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d as p
import auto_run
import boy


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        patches = [
            patch.object(boy, 'get_time', side_effect=lambda: self.now),
            patch.object(auto_run, 'get_time', side_effect=lambda: self.now),
            patch.object(boy, 'get_canvas_width', return_value=800),
            patch.object(auto_run, 'get_canvas_width', return_value=800),
            patch.object(boy, 'load_image', return_value=Mock()),
        ]
        for replacement in patches:
            replacement.start()
            self.addCleanup(replacement.stop)
        self.boy = boy.Boy()

    def key(self, key, kind=p.SDL_KEYDOWN, repeat=0):
        self.boy.handle_event(SimpleNamespace(type=kind, key=key, repeat=repeat))

    def tick(self, now):
        self.now = now
        self.boy.update()

    def test_autorun_speed_and_scaled_rendering(self):
        self.key(p.SDLK_a)
        self.tick(100.25)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.assertEqual(self.boy.x, 500)
        self.boy.draw()
        self.assertEqual(self.boy.image.clip_draw.call_args.args[-2:], (300, 300))
        self.assertEqual(self.boy.frame, 1)

    def test_both_edges_and_multiple_reflections(self):
        self.key(p.SDLK_a)
        self.tick(100.625)
        self.assertEqual((self.boy.x, self.boy.face_dir), (650, -1))
        self.tick(101.875)
        self.assertEqual((self.boy.x, self.boy.face_dir), (150, 1))
        self.tick(104.375)
        self.assertEqual((self.boy.x, self.boy.face_dir), (150, 1))

    def test_start_near_edge_and_face_left(self):
        self.boy.x = 50
        self.boy.face_dir = -1
        self.key(p.SDLK_a)
        self.assertEqual(self.boy.x, 150)
        self.tick(100.25)
        self.assertEqual((self.boy.x, self.boy.face_dir), (250, 1))

    def test_timeout_and_idle_timer_restart(self):
        self.key(p.SDLK_a)
        self.tick(104.999)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.tick(105.0)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.idle_started_at, 105.0)
        self.boy.draw()
        # Normal clip_draw defaults to the 100 x 100 source frame dimensions.
        self.assertEqual(self.boy.image.clip_draw.call_args.args[2:4], (100, 100))
        self.assertEqual(len(self.boy.image.clip_draw.call_args.args), 6)
        self.tick(109.999)
        self.assertEqual(self.boy.state, 'IDLE')
        self.tick(110.0)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_cancel_with_either_arrow_and_restore_run(self):
        for arrow, direction in [(p.SDLK_LEFT, -1), (p.SDLK_RIGHT, 1)]:
            with self.subTest(arrow=arrow):
                self.key(p.SDLK_a)
                self.key(arrow)
                self.assertEqual(self.boy.state, 'RUN')
                self.assertEqual(self.boy.face_dir, direction)
                start_x = self.boy.x
                self.tick(self.now + .25)
                self.assertAlmostEqual(self.boy.x, start_x + direction * 50)
                self.boy.draw()
                self.assertEqual(len(self.boy.image.clip_draw.call_args.args), 6)
                self.key(arrow, p.SDL_KEYUP)
                self.assertEqual(self.boy.state, 'IDLE')

    def test_unrelated_inputs_do_not_cancel_or_restart(self):
        self.key(p.SDLK_a)
        self.tick(102.0)
        self.key(p.SDLK_a)
        self.key(p.SDLK_SPACE)
        self.key(p.SDLK_LEFT, p.SDL_KEYUP)
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.assertEqual(self.boy.auto_run.started_at, 100.0)
        self.tick(105.0)
        self.key(p.SDLK_a, repeat=1)
        self.assertEqual(self.boy.state, 'IDLE')

    def test_existing_run_sleep_and_key_priority(self):
        self.key(p.SDLK_RIGHT)
        self.key(p.SDLK_LEFT)
        self.key(p.SDLK_RIGHT, repeat=1)
        self.assertEqual(self.boy.face_dir, -1)
        self.key(p.SDLK_LEFT, p.SDL_KEYUP)
        self.assertEqual(self.boy.face_dir, 1)
        self.tick(104.0)
        self.assertEqual(self.boy.x, 750)
        self.key(p.SDLK_RIGHT, p.SDL_KEYUP)
        self.tick(109.0)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.key(p.SDLK_a)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.key(p.SDLK_SPACE)
        self.assertEqual(self.boy.state, 'IDLE')
        self.tick(114.0)
        self.key(p.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'RUN')
        self.tick(120.0)
        self.assertEqual(self.boy.x, 50)


if __name__ == '__main__':
    unittest.main()
