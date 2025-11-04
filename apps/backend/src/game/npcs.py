import os
import json
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

# Mock pygame for syntax validation
try:
    import pygame
except ImportError:
    pygame = Mock()

_NPC_DATA: Dict[str, Any] = {}

class NPC:
    """Represents a Non-Player Character in the game."""

    def __init__(self, game: Any, npc_data: Dict[str, Any], portrait: Any, sprite: Any):
        self.game = game
        self.id = npc_data['id']
        self.name = npc_data['name']
        self.npc_type = npc_data['type']
        self.image = sprite if sprite else pygame.Surface((48, 48))
        if not sprite:
            self.image.fill((255, 0, 255))  # Magenta for placeholder
        self.portrait = portrait
        self.rect = self.image.get_rect(topleft=(npc_data['x'], npc_data['y']))
        self.dialogue_tree: Dict[str, List[str]] = npc_data.get('dialogue_tree', {})
        self.relationship_level = 0
        self.event_flags: Dict[str, bool] = {}

    async def interact(self):
        """Handles player interaction with the NPC, showing dialogue."""
        # Placeholder for a more complex dialogue system.
        # This could check for relationship levels, completed quests, etc.
        dialogue_node = self.dialogue_tree.get(str(self.relationship_level), self.dialogue_tree.get("default", ["..."]))
        dialogue_text = dialogue_node[0]  # For now, just get the first line
        
        # Assuming the game has a dialogue_box attribute
        if hasattr(self.game, 'dialogue_box'):
            self.game.dialogue_box.show(dialogue_text, self.name, self.portrait)

    def render(self, surface: Any):
        """Renders the NPC on the given surface."""
        surface.blit(self.image, self.rect)

def load_npc_data():
    """Loads NPC data from the JSON file."""
    global _NPC_DATA
    path = os.path.join('data', 'game_data', 'npcs.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            _NPC_DATA = json.load(f)
    except FileNotFoundError:
        print(f"Warning: npcs.json not found at {path}. Initializing with empty data.")
        _NPC_DATA = {}
    except json.JSONDecodeError:
        print(f"Warning: npcs.json at {path} is malformed. Initializing with empty data.")
        _NPC_DATA = {}

def create_npc(game: Any, npc_id: str) -> Optional[NPC]:
    """Factory function to create an NPC instance."""
    if not _NPC_DATA:
        load_npc_data()  # Ensure data is loaded if not already
    
    npc_data = _NPC_DATA.get(npc_id)
    if not npc_data:
        return None

    # Create a mutable copy to add 'id' if it's not already present
    npc_data_copy = npc_data.copy()
    npc_data_copy['id'] = npc_id

    # Safely get assets
    portrait = game.assets.get('images', {}).get('portraits', {}).get(npc_data_copy.get('portrait'))
    sprite = game.assets.get('sprites', {}).get('characters', {}).get(npc_data_copy.get('sprite'))

    return NPC(game, npc_data_copy, portrait, sprite)

# Load data on module import
load_npc_data()