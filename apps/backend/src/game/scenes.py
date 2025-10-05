import pygame
from .ui import DialogueBox
from .npcs import create_npc

class Scene:
    def __init__(self, game) -> None:
    self.game = game

    async def handle_events(self, event):
ass

    async def update(self):
ass

    def render(self, surface):
ass

class VillageScene(Scene):
ef __init__(self, game) -> None:
    super().__init__(game)
    self.background = self.game.assets['sprites'].get('terrains-grassland_tiles')
    self.player = self.game.player
    self.npcs =
    self.load_npcs
    self.dialogue_box = DialogueBox(self.game)

    def load_npcs(self):
elf.npcs.append(create_npc(self.game, "murakami"))
    self.npcs.append(create_npc(self.game, "lina"))
    self.npcs.append(create_npc(self.game, "tanaka"))
    self.npcs.append(create_npc(self.game, "hibiki"))

    async def handle_events(self, event):
 = await super().handle_events(event)
        if self.dialogue_box.is_active:

    if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
    self.dialogue_box.hide
        elif event.type == pygame.KEYDOWN:

    if event.key == pygame.K_e:


    for npc in self.npcs:



    if self.player.rect.colliderect(npc.rect.inflate(20, 20)):




    _ = await npc.interact
                        dialogue_text = npc.dialogue[npc.dialogue_index - 1] if npc.dialogue_index > 0 else npc.dialogue[0]:
    self.dialogue_box.show(dialogue_text, npc.name, npc.portrait)
                        break

    async def update(self):
 = await super().update
    self.player.update
        for npc in self.npcs:
            # NPCs will just stand still for now:
ass

    def render(self, surface):
f self.background:

    surface.blit(self.background, (0, 0))
        else:

            surface.fill((100, 150, 100)) # Green fallback

    self.player.render(surface)
        for npc in self.npcs:

    npc.render(surface)

    self.dialogue_box.render(surface)
    super().render(surface)


class GameStateManager:
    def __init__(self, game) -> None:
    self.game = game
    self.states = {
            'village': VillageScene(game),
    }
    self.current_state = 'village'

    async def handle_events(self, event):
 = await self.states[self.current_state].handle_events(event)

    async def update(self):
 = await self.states[self.current_state].update

    def render(self, surface):
elf.states[self.current_state].render(surface)