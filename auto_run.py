from pico2d import get_canvas_width, get_time


class AutoRun:
    """Expanded, fast running with automatic turns and a five-second limit."""

    SIZE = 300
    SPEED_MULTIPLIER = 2.0
    DURATION = 5.0

    def __init__(self):
        self.started_at = 0.0

    def enter(self, boy):
        self.started_at = get_time()
        boy.last_updated_at = self.started_at
        boy.frame = 0
        boy.pressed_directions.clear()
        left, right = self._bounds()
        boy.x = max(left, min(right, boy.x))

    def _bounds(self):
        half_size = self.SIZE / 2
        return half_size, get_canvas_width() - half_size

    def update(self, boy, now, elapsed):
        """Return True on timeout; otherwise move and reflect at each edge."""
        if now - self.started_at >= self.DURATION:
            return True

        left, right = self._bounds()
        if right <= left:
            boy.x = get_canvas_width() / 2
            return False

        boy.x += boy.face_dir * boy.run_speed * self.SPEED_MULTIPLIER * elapsed
        # Preserve the remaining travel distance, even across several bounces.
        while boy.x < left or boy.x > right:
            if boy.x > right:
                boy.x = 2 * right - boy.x
                boy.face_dir = -1
            elif boy.x < left:
                boy.x = 2 * left - boy.x
                boy.face_dir = 1
        if boy.x == right:
            boy.face_dir = -1
        elif boy.x == left:
            boy.face_dir = 1
        return False

    def draw(self, boy):
        row = 100 if boy.face_dir == 1 else 0
        # Keep the bottom of the enlarged frame at the normal frame's bottom.
        draw_y = boy.y + (self.SIZE - 100) / 2
        boy.image.clip_draw(
            boy.frame * 100, row, 100, 100,
            boy.x, draw_y, self.SIZE, self.SIZE,
        )
