import pygame

class NPC:
    def __init__(self, game, name, x, y, dialogue):
        self.game = game
        self.name = name
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 0, 255)) # Magenta for placeholder
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.dialogue = dialogue
        self.dialogue_index = 0

    async def interact(self):
        if self.dialogue_index < len(self.dialogue):
            print(f"[{self.name}]: {self.dialogue[self.dialogue_index]}")
            self.dialogue_index += 1
        else:
            self.dialogue_index = 0

    def render(self, surface):
        surface.blit(self.image, self.rect)

class Villager(NPC):
    def __init__(self, game, name, x, y, dialogue):
        super().__init__(game, name, x, y, dialogue)

class UnemployedUncle(NPC):
    def __init__(self, game, name, x, y, dialogue):
        super().__init__(game, name, x, y, dialogue)

class HomelessPerson(NPC):
    def __init__(self, game, name, x, y, dialogue):
        super().__init__(game, name, x, y, dialogue)
