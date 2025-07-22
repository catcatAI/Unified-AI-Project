import pygame
import json
import os

class NPC:
    def __init__(self, game, name, x, y, portrait=None, sprite=None):
        self.game = game
        self.name = name
        self.image = sprite if sprite else pygame.Surface((48, 48))
        if not sprite:
            self.image.fill((255, 0, 255)) # Magenta for placeholder
        self.portrait = portrait
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.dialogue = []
        self.dialogue_index = 0

    async def interact(self):
        if self.dialogue_index < len(self.dialogue):
            # This should be handled by the UI, but for now, we'll print to console
            print(f"[{self.name}]: {self.dialogue[self.dialogue_index]}")
            self.dialogue_index += 1
        else:
            self.dialogue_index = 0 # Loop dialogue for now

    def render(self, surface):
        surface.blit(self.image, self.rect)

class Villager(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

class UnemployedUncle(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

class HomelessPerson(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

class Blacksmith(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

def load_npc_data():
    path = os.path.join('data', 'game_data', 'npcs.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

NPC_DATA = load_npc_data()

def create_npc(game, npc_id):
    npc_data = NPC_DATA.get(npc_id)
    if not npc_data:
        return None

    npc_type = npc_data["type"]
    portrait = game.assets['sprites']['portraits'].get(npc_data['portrait'])
    sprite = game.assets['sprites']['characters'].get(npc_data['sprite'])

    if npc_type == "villager":
        return Villager(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    elif npc_type == "unemployed_uncle":
        return UnemployedUncle(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    elif npc_type == "homeless_person":
        return HomelessPerson(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    elif npc_type == "blacksmith":
        return Blacksmith(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    return None
