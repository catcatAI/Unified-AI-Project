import random
from unittest.mock import Mock

# Mock pygame for syntax validation
try:
    import pygame
except ImportError:
    pygame = Mock()

class FishingGame:
    """Encapsulates the logic for a fishing minigame."""

    def __init__(self, game: any):
        """Initializes the fishing minigame state."""
        self.game = game
        self.is_active = False
        self.timer = 0
        self.catch_time = 0
        self.bar_pos = 0
        self.bar_speed = 5
        self.catch_zone_pos = 0
        self.catch_zone_size = 50

    def start(self):
        """Resets and starts the minigame."""
        self.is_active = True
        self.timer = 0
        self.catch_time = random.randint(60, 180)  # 1-3 seconds at 60 FPS
        self.bar_pos = 0
        self.catch_zone_pos = random.randint(0, 150)

    def handle_events(self, event: any):
        """Handles player input for the minigame."""
        if self.is_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.check_catch()

    def update(self):
        """Updates the state of the moving bar."""
        if self.is_active:
            self.timer += 1
            if self.timer > self.catch_time:
                self.bar_pos += self.bar_speed
                if self.bar_pos > 200 or self.bar_pos < 0:
                    self.bar_speed *= -1

    def render(self, surface: any):
        """Renders the minigame UI."""
        if self.is_active:
            # Draw the fishing bar background
            pygame.draw.rect(surface, (200, 200, 200), (350, 200, 100, 200))
            # Draw the catch zone
            pygame.draw.rect(surface, (0, 255, 0), (350, 200 + self.catch_zone_pos, 100, self.catch_zone_size))
            # Draw the moving bar
            pygame.draw.rect(surface, (255, 0, 0), (350, 200 + self.bar_pos, 100, 10))

    def check_catch(self):
        """Checks if the player successfully caught a fish."""
        if self.catch_zone_pos < self.bar_pos < self.catch_zone_pos + self.catch_zone_size:
            print("Fish caught!")
            # This assumes player and inventory objects exist on the game object
            if hasattr(self.game, 'player') and hasattr(self.game.player, 'inventory'):
                self.game.player.inventory.add_item('fish')
        else:
            print("Fish got away!")
        self.is_active = False