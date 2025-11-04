import asyncio
from typing import Any, Dict, List
from unittest.mock import Mock

# Mock pygame for syntax validation
try:
    import pygame
except ImportError:
    pygame = Mock()

# Mock local imports for syntax validation
class DialogueBox:
    def __init__(self, game): self.is_active = False
    def show(self, text, name, portrait): pass
    def hide(self): pass
    def render(self, surface): pass

class NPC:
    def __init__(self, game, data, portrait, sprite): pass
    async def interact(self): pass
    def render(self, surface): pass

def create_npc(game, npc_id): return Mock()

class Scene:
    """Base class for all game scenes."""
    def __init__(self, game: Any):
        self.game = game

    async def handle_events(self, event: Any):
        pass

    async def update(self):
        pass

    def render(self, surface: Any):
        pass

class VillageScene(Scene):
    """Represents the main village area of the game."""
    def __init__(self, game: Any) -> None:
        super().__init__(game)
        self.background = self.game.assets.get('sprites', {}).get('terrains - grassland_tiles')
        self.player = self.game.player
        self.npcs: List[Any] = []
        self.load_npcs()
        self.dialogue_box = DialogueBox(self.game)

    def load_npcs(self):
        """Loads all NPCs for this scene."""
        self.npcs.append(create_npc(self.game, "murakami"))
        self.npcs.append(create_npc(self.game, "lina"))
        self.npcs.append(create_npc(self.game, "tanaka"))
        self.npcs.append(create_npc(self.game, "hibiki"))

    async def handle_events(self, event: Any):
        await super().handle_events(event)
        if self.dialogue_box.is_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.dialogue_box.hide()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                for npc in self.npcs:
                    if self.player.rect.colliderect(npc.rect.inflate(20, 20)):
                        await npc.interact()
                        # The dialogue box is now managed by the NPC's interact method
                        break

    async def update(self):
        await super().update()
        self.player.update()
        for npc in self.npcs:
            # NPCs will just stand still for now
            pass

    def render(self, surface: Any):
        if self.background:
            surface.blit(self.background, (0, 0))
        else:
            surface.fill((100, 150, 100))  # Green fallback

        self.player.render(surface)
        for npc in self.npcs:
            npc.render(surface)

        self.dialogue_box.render(surface)
        super().render(surface)

class GameStateManager:
    """Manages the active game state and scene transitions."""
    def __init__(self, game: Any):
        self.game = game
        self.states: Dict[str, Scene] = {
            'village': VillageScene(game),
        }
        self.current_state_key = 'village'

    @property
    def current_state(self) -> Scene:
        return self.states[self.current_state_key]

    async def handle_events(self, event: Any):
        await self.current_state.handle_events(event)

    async def update(self):
        await self.current_state.update()

    def render(self, surface: Any):
        self.current_state.render(surface)
