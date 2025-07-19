import pygame
from .inventory import Inventory

class Player:
    def __init__(self, game):
        self.game = game
        self.image = self.game.assets['images']['player']
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 100
        self.speed = 5
        self.inventory = Inventory()
        self.covenant_unlocked = False
        self.uid = None

    def handle_events(self, event):
        pass

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

    def render(self, surface):
        surface.blit(self.image, self.rect)
