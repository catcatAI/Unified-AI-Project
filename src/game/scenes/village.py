import pygame
from .base import Scene
from ..npcs import create_npc

class VillageScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.background = self.game.assets['sprites']['terrains-grassland_tiles']
        self.player = self.game.player
        self.npcs = []
        self.load_npcs()

    def load_npcs(self):
        self.npcs.append(create_npc(self.game, "murakami"))
        self.npcs.append(create_npc(self.game, "lina"))

    async def handle_events(self, event):
        await super().handle_events(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                for npc in self.npcs:
                    if self.player.rect.colliderect(npc.rect.inflate(20, 20)) and not self.game.dialogue_box.is_active:
                        await npc.interact()
                        self.game.dialogue_box.show(npc.dialogue[npc.dialogue_index-1], npc.name, npc.portrait)
                        break

    async def update(self):
        await super().update()
        self.player.update()
        for npc in self.npcs:
            # NPCs will just stand still for now
            pass

    def render(self, surface):
        surface.blit(self.background, (0, 0))
        self.player.render(surface)
        for npc in self.npcs:
            npc.render(surface)
        super().render(surface)
