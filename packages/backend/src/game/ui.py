import pygame

class DialogueBox:
    def __init__(self, game):
        self.game = game
        self.is_active = False
        self.text = ""
        self.character_name = ""
        self.portrait = None
        self.font = pygame.font.Font(None, 32) # Larger font

        # Based on 960x540 resolution
        self.rect = pygame.Rect(50, 400, 860, 120)
        self.border_rect = self.rect.inflate(4, 4)
        self.portrait_rect = pygame.Rect(70, 290, 96, 96) # 96x96 portrait

    def show(self, text, character_name, portrait):
        self.is_active = True
        self.text = text
        self.character_name = character_name
        self.portrait = portrait

    def hide(self):
        self.is_active = False

    def render(self, surface):
        if self.is_active:
            # Dialogue box background
            pygame.draw.rect(surface, (0, 0, 0, 180), self.rect) # Semi-transparent black
            pygame.draw.rect(surface, (255, 255, 255), self.border_rect, 2) # White border

            # Character portrait
            if self.portrait:
                pygame.draw.rect(surface, (255, 255, 255), self.portrait_rect.inflate(4,4), 2) # Portrait border
                surface.blit(self.portrait, self.portrait_rect)

            # Character name
            name_surface = self.font.render(self.character_name, True, (255, 255, 0)) # Yellow name
            surface.blit(name_surface, (self.rect.x + 120, self.rect.y + 10))

            # Dialogue text
            text_surface = self.font.render(self.text, True, (255, 255, 255))
            surface.blit(text_surface, (self.rect.x + 120, self.rect.y + 50))
