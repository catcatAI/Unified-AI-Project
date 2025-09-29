import pygame
import random

class FishingGame:
    def __init__(self, game) -> None:
        self.game = game
        self.is_active = False
        self.timer = 0
        self.catch_time = 0
        self.bar_pos = 0
        self.bar_speed = 5
        self.catch_zone_pos = 0
        self.catch_zone_size = 50

    def start(self):
        self.is_active = True
        self.timer = 0
        self.catch_time = random.randint(60, 180) # 1-3 seconds
        self.bar_pos = 0
        self.catch_zone_pos = random.randint(0, 150)

    def handle_events(self, event):
        if self.is_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.check_catch

    def update(self):
        if self.is_active:
            self.timer += 1
            if self.timer > self.catch_time:
                self.bar_pos += self.bar_speed
                if self.bar_pos > 200 or self.bar_pos < 0:
                    self.bar_speed *= -1

    def render(self, surface):
        if self.is_active:
            # Draw the fishing bar
            pygame.draw.rect(surface, (200, 200, 200), (350, 200, 100, 200))
            # Draw the catch zone
            pygame.draw.rect(surface, (0, 255, 0), (350, 200 + self.catch_zone_pos, 100, self.catch_zone_size))
            # Draw the moving bar
            pygame.draw.rect(surface, (255, 0, 0), (350, 200 + self.bar_pos, 100, 10))

    def check_catch(self):
        if self.catch_zone_pos < self.bar_pos < self.catch_zone_pos + self.catch_zone_size:
            print("Fish caught!")
            self.game.player.inventory.add_item('fish')
        else:
            print("Fish got away!")
        self.is_active = False
