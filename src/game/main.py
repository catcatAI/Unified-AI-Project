import pygame
import os
import sys
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.game.scenes import GameStateManager
from src.game.player import Player
from src.game.angela import Angela

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.assets = {'images': {}, 'sprites': {}}
        self.load_assets()
        self.player = Player(self)
        self.angela = Angela(self)
        self.game_state_manager = GameStateManager(self)

    def load_assets(self):
        base_path = os.path.join('src', 'game', 'assets')
        for asset_type in ['images', 'sprites']:
            asset_path = os.path.join(base_path, asset_type)
            if not os.path.exists(asset_path):
                logging.warning(f"Asset directory not found: {asset_path}")
                continue
            for root, dirs, files in os.walk(asset_path):
                for file in files:
                    if file.endswith('.png'):
                        try:
                            path = os.path.join(root, file)
                            category = os.path.basename(root)
                            asset_name = os.path.splitext(file)[0]
                            image = pygame.image.load(path).convert_alpha()

                            if category not in self.assets[asset_type]:
                                self.assets[asset_type][category] = {}
                            self.assets[asset_type][category][asset_name] = image
                            logging.info(f"Loaded asset: {path}")
                        except pygame.error as e:
                            logging.error(f"Failed to load asset: {path} - {e}")

    async def run(self):
        logging.info("Starting game loop")
        frameCount = 0
        while self.is_running:
            await self.handle_events()
            await self.update()
            self.render()
            self.clock.tick(60)
            frameCount += 1
            if frameCount > 300: # 5 seconds
                logging.info("Game loop finished")
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
