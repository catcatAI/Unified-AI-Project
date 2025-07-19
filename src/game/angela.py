import pygame
from ..core_ai.dialogue.dialogue_manager import DialogueManager

class Angela:
    def __init__(self, game):
        self.game = game
        self.image = self.game.assets['images']['angela']
        self.rect = self.image.get_rect()
        self.rect.x = 400
        self.rect.y = 500
        self.is_appearing = False
        self.appear_speed = 2
        self.favorability = 0
        self.dialogue_manager = DialogueManager()

    def start_appearing(self):
        self.is_appearing = True

    def update(self):
        if self.is_appearing:
            self.rect.y -= self.appear_speed
            if self.rect.y < 400:
                self.is_appearing = False

    def render(self, surface):
        if self.is_appearing:
            surface.blit(self.image, self.rect)

    def increase_favorability(self, amount):
        self.favorability += amount

    def decrease_favorability(self, amount):
        self.favorability -= amount

    def give_gift(self, item_name):
        if item_name == 'fish':
            self.increase_favorability(10)
        elif item_name == 'stone':
            self.increase_favorability(1)

    async def get_dialogue(self, player_message):
        return await self.dialogue_manager.get_simple_response(player_message)
