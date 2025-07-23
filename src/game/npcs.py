import pygame
import json
import os

class NPC:
    def __init__(self, game, npc_data, portrait=None, sprite=None):
        self.game = game
        self.id = npc_data['id']
        self.name = npc_data['name']
        self.npc_type = npc_data['type']
        self.image = sprite if sprite else pygame.Surface((48, 48))
        if not sprite:
            self.image.fill((255, 0, 255)) # Magenta for placeholder
        self.portrait = portrait
        self.rect = self.image.get_rect(topleft=(npc_data['x'], npc_data['y']))
        self.dialogue_tree = npc_data.get('dialogue_tree', {})
        self.relationship_level = 0
        self.event_flags = {}

    async def interact(self):
        # Placeholder for a more complex dialogue system
        # This could check for relationship levels, completed quests, etc.
        dialogue_node = self.dialogue_tree.get(str(self.relationship_level), self.dialogue_tree.get("default", ["..."]))
        dialogue_text = dialogue_node[0] # For now, just get the first line
        self.game.dialogue_box.show(dialogue_text, self.name, self.portrait)


    def render(self, surface):
        surface.blit(self.image, self.rect)

def load_npc_data():
    path = os.path.join('data', 'game_data', 'npcs.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

NPC_DATA = load_npc_data()

def create_npc(game, npc_id):
    npc_data = NPC_DATA.get(npc_id)
    if not npc_data:
        return None

    npc_data['id'] = npc_id
    portrait = game.assets['images']['portraits'].get(npc_data['portrait'])
    sprite = game.assets['sprites']['characters'].get(npc_data['sprite'])

    return NPC(game, npc_data, portrait, sprite)
