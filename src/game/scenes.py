import pygame
import random
from .player import Player
from .items import Schoolbag
from .angela import Angela
from .ui import DialogueBox

class Scene:
    def __init__(self, game):
        self.game = game

    def handle_events(self, event):
        pass

    def update(self):
        pass

    def render(self, surface):
        pass

class OpeningScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        print("Initializing OpeningScene")
        self.background = self.game.assets['images']['station']
        self.schoolbag = Schoolbag(self.game, self.game.player.rect.x + 20, self.game.player.rect.y + 30)
        self.timer = 0
        self.angela_appeared = False
        self.dialogue_box = DialogueBox(self.game)
        self.dialogue_active = False
        self.player_message = ""
        self.interaction_attempted = False
        print("OpeningScene initialized")

    async def handle_events(self, event):
        if self.dialogue_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    response = await self.angela.get_dialogue(self.player_message)
                    self.dialogue_box.show(response)
                    self.player_message = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.player_message = self.player_message[:-1]
                else:
                    self.player_message += event.unicode

    async def update(self):
        self.timer += 1
        if self.timer == 61:
            self.schoolbag.start_falling()
        self.schoolbag.update()
        if not self.schoolbag.is_falling and self.timer > 120 and not self.angela_appeared:
            self.angela.start_appearing()
        self.angela.update()
        if not self.angela.is_appearing and self.angela_appeared == False and self.timer > 120:
            self.angela_appeared = True
            self.dialogue_active = True
            self.dialogue_box.show("What did you drop?")


    def render(self, surface):
        surface.blit(self.background, (0, 0))
        # Draw the player
        self.game.player.render(surface)
        self.schoolbag.render(surface)
        self.angela.render(surface)
        self.dialogue_box.render(surface)

from .tiles import TileMap
from .minigames import FishingGame
from .npcs import Villager, UnemployedUncle, HomelessPerson
from .utils import generate_uid

class CovenantScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.game.player.covenant_unlocked = True
        self.game.player.uid = generate_uid()
        self.text = f"Our Covenant is sealed. Your UID is: {self.game.player.uid}"
        self.font = pygame.font.Font(None, 32)

    def render(self, surface):
        surface.fill((0, 0, 0))
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(text_surface, (100, 250))

class PlayScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.tile_map = TileMap(self.game, 25, 19)
        self.fishing_game = FishingGame(self.game)
        self.npcs = [
            Villager(self.game, "Farmer", 100, 200, ["I'm a farmer.", "It's a tough life, but it's an honest one.", "The soil is rich here."]),
            UnemployedUncle(self.game, "Uncle", 200, 300, ["I'm looking for a job.", "I used to work at the factory in the city.", "Times are tough."]),
            HomelessPerson(self.game, "Wanderer", 300, 400, ["...", "Sometimes, a kind word is worth more than money."])
        ]

    async def handle_events(self, event):
        if self.fishing_game.is_active:
            self.fishing_game.handle_events(event)
        else:
            self.game.player.handle_events(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f and self.game.player.rect.y > 300:
                    self.fishing_game.start()
                elif event.key == pygame.K_SPACE:
                    # Till the tile in front of the player
                    player_x = self.game.player.rect.x // 32
                    player_y = self.game.player.rect.y // 32
                    self.tile_map.tiles[player_x][player_y].tile_type = 'tilled'
                elif event.key == pygame.K_m:
                    # Mine the rock in front of the player
                    player_x = self.game.player.rect.x // 32
                    player_y = self.game.player.rect.y // 32
                    if self.tile_map.tiles[player_x + 1][player_y].tile_type == 'rock':
                        await self.mine_rock(player_x + 1, player_y)
                elif event.key == pygame.K_e:
                    await self.interact_with_npc()

    async def update(self):
        if self.fishing_game.is_active:
            self.fishing_game.update()
        else:
            self.game.player.update()
        if self.angela.favorability >= 250 and not self.game.player.covenant_unlocked:
            self.game.game_state_manager.current_state = 'covenant'

    async def mine_rock(self, x, y):
        rock = self.tile_map.tiles[x][y].rock
        if rock:
            rock.health -= 25
            if rock.health <= 0:
                self.tile_map.tiles[x][y].tile_type = 'grass'
                self.tile_map.tiles[x][y].rock = None
                self.game.player.inventory.add_item('stone', random.randint(1, 3))
                self.game.player.inventory.add_item('coal', random.randint(0, 1))


    def render(self, surface):
        self.tile_map.render(surface)
        self.game.player.render(surface)
        for npc in self.npcs:
            npc.render(surface)
        if self.fishing_game.is_active:
            self.fishing_game.render(surface)

class GameStateManager:
    def __init__(self, game):
        self.game = game
        self.states = {
            'opening': OpeningScene(game),
            'play': PlayScene(game),
            'covenant': CovenantScene(game)
        }
        self.current_state = 'opening'
        self.states['opening'].angela = game.angela
        self.states['play'].angela = game.angela
        self.states['covenant'].angela = game.angela


    async def handle_events(self, event):
        await self.states[self.current_state].handle_events(event)

    async def update(self):
        await self.states[self.current_state].update()

    def render(self, surface):
        print(f"Rendering state: {self.current_state}")
        self.states[self.current_state].render(surface)
