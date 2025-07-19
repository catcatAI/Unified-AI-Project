import pygame

class DialogueBox:
    def __init__(self, game):
        self.game = game
        self.is_active = False
        self.text = ""
        self.font = pygame.font.Font(None, 24)
        self.rect = pygame.Rect(50, 450, 700, 100)
        self.border_rect = pygame.Rect(48, 448, 704, 104)

    def show(self, text):
        self.is_active = True
        self.text = text

    def hide(self):
        self.is_active = False

    def render(self, surface):
        if self.is_active:
            pygame.draw.rect(surface, (255, 255, 255), self.border_rect)
            pygame.draw.rect(surface, (0, 0, 0), self.rect)
            text_surface = self.font.render(self.text, True, (255, 255, 255))
            surface.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))
