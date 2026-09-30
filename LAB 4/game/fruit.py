import math

class Fruit:
    def __init__(self, x, y, vx, vy, gravity, radius=28, kind="fruit"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.gravity = gravity
        self.radius = radius
        self.kind = kind  # "fruit" or "bomb"
        self.sliced = False

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

    def contains_point(self, x, y):
        # Checks a single point against the fruit's circle.
        return math.hypot(self.x - x, self.y - y) <= self.radius

    def intersects_segment(self, x1, y1, x2, y2):
        # Checks whether the line segment from (x1, y1) to (x2, y2)
        # touches the fruit's circle. This catches fast swipes where
        # both endpoints are outside the fruit but the line passes through it.
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy

        # If the mouse didn't move, fall back to the single-point check
        if length_sq == 0:
            return self.contains_point(x1, y1)

        # Find the point on the segment closest to the fruit's center.
        # t = 0 means the start point, t = 1 means the end point.
        t = ((self.x - x1) * dx + (self.y - y1) * dy) / length_sq
        t = max(0, min(1, t))

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return math.hypot(self.x - closest_x, self.y - closest_y) <= self.radius

    def off_screen(self, height):
        return self.y - self.radius > height