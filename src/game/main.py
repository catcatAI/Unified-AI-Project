import pygame
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.game.scenes import GameStateManager
from src.game.player import Player
from src.game.angela import Angela

class Game:
    def __init__(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        pygame.init()
        self.screen_width = 960
        self.screen_height = 540
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Angela's World")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.assets = {}
        self.load_assets()
        self.player = Player(self)
        self.angela = Angela(self)
        self.game_state_manager = GameStateManager(self)

    def load_assets(self):
        self.assets['images'] = {}
        self.assets['sprites'] = {}
        for root, dirs, files in os.walk(os.path.join('src', 'game', 'assets')):
            for file in files:
                if file.endswith('.png'):
                    path = os.path.join(root, file)
                    asset_type = os.path.basename(os.path.dirname(path))
                    asset_name = os.path.splitext(file)[0]
                    image = pygame.image.load(path).convert_alpha()
                    if 'images' in root:
                        if asset_type not in self.assets['images']:
                            self.assets['images'][asset_type] = {}
                        self.assets['images'][asset_type][asset_name] = image
                    elif 'sprites' in root:
                        if asset_type not in self.assets['sprites']:
                            self.assets['sprites'][asset_type] = {}
                        self.assets['sprites'][asset_type][asset_name] = image

    async def run(self):
        print("Starting game loop")
        frameCount = 0
        while self.is_running:
            await self.handle_events()
            await self.update()
            self.render()
            self.clock.tick(60)
            frameCount += 1
            if frameCount > 300: # 5 seconds
                self.is_running = False

    async def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            await self.game_state_manager.handle_events(event)

    async def update(self):
        await self.game_state_manager.update()

    def render(self):
        self.game_state_manager.render(self.screen)
        pygame.display.flip()

import asyncio

if __name__ == "__main__":
    async def main():
        game = Game()
        await game.run()
        print(f"Angela's favorability: {game.angela.favorability}")
    asyncio.run(main())
