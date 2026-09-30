import array
import math
import random
import pygame
from .fruit import Fruit

# Game Engine

WHITE = (255, 255, 255)
RED = (220, 60, 60)
BOMB_BLACK = (30, 30, 30)
BUTTON_COLOR = (60, 70, 110)
BUTTON_HOVER = (90, 105, 160)
EXIT_COLOR = (130, 50, 50)
EXIT_HOVER = (180, 70, 70)
FRUIT_COLORS = [(220, 60, 60), (230, 140, 40), (230, 200, 40), (90, 180, 90)]

# Difficulty settings: (frames between spawns, bomb chance)
# A smaller spawn interval means fruit appears faster.
DIFFICULTIES = {
    "Easy":   {"spawn_interval": 70, "bomb_chance": 0.08},
    "Medium": {"spawn_interval": 55, "bomb_chance": 0.15},
    "Hard":   {"spawn_interval": 38, "bomb_chance": 0.25},
}


def make_tone(notes, duration, volume=0.4, sample_rate=22050):
    """Build a simple beep. `notes` is a list of frequencies (Hz) played
    one after another, so [880] is one beep and [400, 300, 200] steps down."""
    samples = array.array("h")  # 16-bit sound samples
    total = int(sample_rate * duration)
    for i in range(total):
        freq = notes[i * len(notes) // total]
        wave = math.sin(2 * math.pi * freq * i / sample_rate)
        fade = 1 - i / total  # fades out so it doesn't click at the end
        samples.append(int(wave * fade * volume * 32767))
    return pygame.mixer.Sound(buffer=samples.tobytes())


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.speed_scale = 1.0

        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 64, bold=True)

        # Buttons shown on the game-over screen (label, rectangle)
        self.buttons = []
        button_w, button_h, gap = 130, 50, 20
        start_x = (self.width - (4 * button_w + 3 * gap)) // 2
        for i, label in enumerate(["Easy", "Medium", "Hard", "Exit"]):
            rect = pygame.Rect(start_x + i * (button_w + gap), 360, button_w, button_h)
            self.buttons.append((label, rect))

        self.sounds = {}
        self._load_sounds()

        self.reset("Medium")

    def _load_sounds(self):
        # If there is no audio device, the game still works without sound.
        try:
            pygame.mixer.quit()
            pygame.mixer.init(22050, -16, 1)  # 22050 Hz, 16-bit, mono
            self.sounds = {
                "slice": make_tone([880], 0.10),
                "bomb": make_tone([180, 140, 100], 0.35, volume=0.6),
                "game_over": make_tone([400, 330, 260, 200], 0.80),
            }
        except pygame.error:
            self.sounds = {}
            print("Sound is not available, continuing without it.")

    def _play(self, name):
        # Returns the channel the sound plays on (or None if no sound).
        if name in self.sounds:
            return self.sounds[name].play()
        return None

    def reset(self, difficulty):
        """Start a fresh game with the chosen difficulty."""
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.spawn_interval = settings["spawn_interval"]
        self.bomb_chance = settings["bomb_chance"]

        self.fruits = []
        self.trail = []
        self.last_pos = None  # so the old swipe doesn't connect to the new game
        self._spawn_timer = 0

        self.lives = 3
        self.score = 0
        self.game_over = False
        self.game_over_reason = ""

    def spawn_fruit(self):
        x = random.randint(60, self.width - 60)
        vy = -random.uniform(13, 16) * self.speed_scale
        vx = random.uniform(-2, 2)
        gravity = 0.35
        kind = "bomb" if random.random() < self.bomb_chance else "fruit"

        fruit = Fruit(x, self.height + 30, vx, vy, gravity, kind=kind)
        fruit.color = BOMB_BLACK if kind == "bomb" else random.choice(FRUIT_COLORS)
        self.fruits.append(fruit)

    def handle_event(self, event):
        if self.game_over:
            # Game is over: ignore mouse movement (score stays frozen)
            # and only react to clicks on the buttons.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_button_click(event.pos)
            return

        if event.type == pygame.MOUSEMOTION:
            self._handle_motion(event.pos)

    def _handle_button_click(self, pos):
        for label, rect in self.buttons:
            if rect.collidepoint(pos):
                if label == "Exit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                else:
                    self.reset(label)
                return

    def _handle_motion(self, pos):
        x, y = pos

        # On the very first movement there is no previous position,
        # so use the current one (this becomes a single-point check).
        if self.last_pos is None:
            self.last_pos = pos
        last_x, last_y = self.last_pos

        for fruit in self.fruits:
            if self.game_over:
                break  # a bomb was already sliced in this swipe
            if not fruit.sliced and fruit.intersects_segment(last_x, last_y, x, y):
                self._slice(fruit)

        self.last_pos = pos

        self.trail.append(pos)
        if len(self.trail) > 15:
            self.trail.pop(0)

    def _slice(self, fruit):
        fruit.sliced = True
        if fruit.kind == "bomb":
            self._end_game("You sliced a bomb!", hit_bomb=True)
        else:
            self.score += 1
            self._play("slice")

    def _end_game(self, reason, hit_bomb=False):
        self.game_over = True
        self.game_over_reason = reason
        if hit_bomb:
            # Play the bomb sound, then queue the game-over sound after it
            channel = self._play("bomb")
            if channel is not None and "game_over" in self.sounds:
                channel.queue(self.sounds["game_over"])
        else:
            self._play("game_over")

    def handle_input(self):
        # Reserved for continuously-held-key input; this game is
        # entirely mouse-driven, so there's nothing to poll here.
        pass

    def update(self):
        if self.game_over:
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.spawn_fruit()

        still_alive = []
        for fruit in self.fruits:
            fruit.update()
            if fruit.sliced:
                continue
            if fruit.off_screen(self.height):
                if fruit.kind == "fruit":
                    self.lives = max(0, self.lives - 1)  # never below 0
                continue
            still_alive.append(fruit)
        self.fruits = still_alive

        if self.lives <= 0:
            self._end_game("You ran out of lives!")

    def render(self, screen):
        for fruit in self.fruits:
            color = getattr(fruit, "color", WHITE)
            pygame.draw.circle(screen, color, (int(fruit.x), int(fruit.y)), fruit.radius)

        if len(self.trail) >= 2 and not self.game_over:
            pygame.draw.lines(screen, WHITE, False, self.trail, 3)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))
        level_text = self.font.render(self.difficulty, True, WHITE)
        screen.blit(level_text, level_text.get_rect(midtop=(self.width // 2, 10)))

        if self.game_over:
            self.draw_game_over(screen)

    def draw_game_over(self, screen):
        # Semi-transparent dark layer over the frozen game
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        cx = self.width // 2

        title = self.big_font.render("GAME OVER", True, RED)
        screen.blit(title, title.get_rect(center=(cx, 150)))

        reason = self.font.render(self.game_over_reason, True, WHITE)
        screen.blit(reason, reason.get_rect(center=(cx, 230)))

        final = self.font.render(f"Final Score: {self.score}", True, WHITE)
        screen.blit(final, final.get_rect(center=(cx, 280)))

        prompt = self.font.render("Play again? Choose a difficulty:", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(cx, 330)))

        # Buttons (they change color when the mouse is over them)
        mouse_pos = pygame.mouse.get_pos()
        for label, rect in self.buttons:
            hovered = rect.collidepoint(mouse_pos)
            if label == "Exit":
                color = EXIT_HOVER if hovered else EXIT_COLOR
            else:
                color = BUTTON_HOVER if hovered else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
            text = self.font.render(label, True, WHITE)
            screen.blit(text, text.get_rect(center=rect.center))