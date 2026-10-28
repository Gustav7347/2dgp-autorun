from pico2d import (
    load_image, get_time, get_canvas_width,
    SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a,
)
from math import pi
from pathlib import Path
from transitions import Machine
from auto_run import AutoRun


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.idle_started_at = get_time()
        self.last_updated_at = self.idle_started_at
        self.pressed_directions = []
        self.run_speed = 200.0  # Pixels per second.
        self.auto_run = AutoRun()
        self.image = load_image(str(Path(__file__).with_name('animation_sheet.png')))
        self.machine = Machine(
            model=self,
            states=[
                {'name': 'IDLE', 'on_enter': '_enter_idle'},
                {'name': 'SLEEP', 'on_enter': '_enter_sleep'},
                {'name': 'RUN', 'on_enter': '_enter_run'},
                {'name': 'AUTORUN', 'on_enter': '_enter_auto_run'},
            ],
            initial='IDLE',
            auto_transitions=False,
        )
        # Internal transitions advance animation without re-entering the state.
        self.machine.add_transition(
            trigger='animate', source=['IDLE', 'RUN', 'AUTORUN'], dest=None,
            after='_advance_frame',
        )
        self.machine.add_transition('fall_asleep', 'IDLE', 'SLEEP')
        self.machine.add_transition('wake_up', 'SLEEP', 'IDLE')
        self.machine.add_transition('start_running', ['IDLE', 'SLEEP', 'AUTORUN'], 'RUN')
        self.machine.add_transition('stop_running', 'RUN', 'IDLE')
        self.machine.add_transition('start_auto_run', 'IDLE', 'AUTORUN')
        self.machine.add_transition('finish_auto_run', 'AUTORUN', 'IDLE')

    def update(self):
        now = get_time()
        elapsed = max(0.0, now - self.last_updated_at)
        self.last_updated_at = now
        if self.is_IDLE():
            if now - self.idle_started_at >= 5.0:
                self.fall_asleep()
            else:
                self.animate()
        elif self.is_RUN():
            self.x += self.face_dir * self.run_speed * elapsed
            self.x = max(50, min(get_canvas_width() - 50, self.x))
            self.animate()
        elif self.is_AUTORUN():
            if self.auto_run.update(self, now, elapsed):
                self.finish_auto_run()
            else:
                self.animate()

    def _enter_auto_run(self):
        self.auto_run.enter(self)

    def _enter_run(self):
        self.frame = 0
        self.last_updated_at = get_time()

    def _enter_idle(self):
        self.frame = 0
        self.idle_started_at = get_time()

    def _enter_sleep(self):
        self.frame = 0
        self.pressed_directions.clear()

    def handle_event(self, event):
        if (event.type == SDL_KEYDOWN and event.key == SDLK_a
                and not getattr(event, 'repeat', 0) and self.is_IDLE()):
            self.start_auto_run()
        elif (event.type == SDL_KEYDOWN and event.key == SDLK_SPACE
                and self.is_SLEEP()):
            self.wake_up()
        elif (event.type in (SDL_KEYDOWN, SDL_KEYUP)
              and event.key in (SDLK_LEFT, SDLK_RIGHT)):
            if event.type == SDL_KEYDOWN:
                # Ignore key repeats; the most recently pressed key wins.
                if event.key not in self.pressed_directions:
                    self.pressed_directions.append(event.key)
            elif event.key in self.pressed_directions:
                self.pressed_directions.remove(event.key)

            if self.pressed_directions:
                self.face_dir = (1 if self.pressed_directions[-1] == SDLK_RIGHT else -1)
                if self.is_IDLE() or self.is_SLEEP() or self.is_AUTORUN():
                    self.start_running()
            elif self.is_RUN():
                self.stop_running()

    def _advance_frame(self):
        self.frame = (self.frame + 1) % 8

    def draw(self):
        if self.is_AUTORUN():
            self.auto_run.draw(self)
        elif self.is_SLEEP():
            # Keep the idle frame size when rotating the sprite.
            row = 300 if self.face_dir == 1 else 200
            self.image.clip_composite_draw(
                0, row, 100, 100, -pi / 2, '', self.x, self.y - 25, 100, 100,
            )
        elif self.face_dir == 1:
            row = 100 if self.is_RUN() else 300
            self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
        else:
            row = 0 if self.is_RUN() else 200
            self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
