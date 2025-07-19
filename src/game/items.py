import pygame

class Schoolbag:
    def __init__(self, game, x, y):
        self.game = game
        self.image = self.game.assets['images']['schoolbag']
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.is_falling = False
        self.fall_speed = 5

    def start_falling(self):
        self.is_falling = True

    def update(self):
        if self.is_falling:
            self.rect.y += self.fall_speed
            if self.rect.y > 450: # Rice paddy level
                self.is_falling = False

    def render(self, surface):
        surface.blit(self.image, self.rect)
