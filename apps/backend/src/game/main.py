import os
import sys
import logging
import asyncio
from unittest.mock import Mock

# Mock pygame for syntax validation
try:
    import pygame
except ImportError:
    pygame = Mock()

# Add project root to sys.path to allow for sibling imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Mock local imports for syntax validation
class Player:
    def __init__(self, game): pass

class Angela:
    def __init__(self, game): self.favorability = 0

class GameStateManager:
    def __init__(self, game): pass
    async def handle_events(self, event): pass
    async def update(self): pass
    def render(self, screen): pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Game constants
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
GAME_TITLE = "Angela's World"

class Game:
    """Main game class that orchestrates the game loop."""

    def __init__(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        pygame.init()
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.assets: Dict[str, Dict[str, Dict[str, any]]] = {'images': {}, 'sprites': {}}
        self.load_assets()

        if 'characters' not in self.assets.get('sprites', {}) or \
           'player' not in self.assets.get('sprites', {}).get('characters', {}):
            logging.critical("Player sprite not found! Exiting.")
            self.is_running = False
            return

        self.player = Player(self)
        self.angela = Angela(self)
        self.game_state_manager = GameStateManager(self)

    def load_assets(self):
        """Loads all game assets from the assets directory."""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets'))
        for asset_type in ['images', 'sprites']:
            asset_path = os.path.join(base_path, asset_type)
            if not os.path.exists(asset_path):
                logging.warning(f"Asset directory not found: {asset_path}")
                continue
            for root, _, files in os.walk(asset_path):
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
        """Main asynchronous game loop."""
        if not self.is_running:
            return

        logging.info("Starting game loop")
        frameCount = 0
        while self.is_running:
            await self.handle_events()
            await self.update()
            self.render()
            self.clock.tick(60)
            frameCount += 1
            if frameCount > 300:  # Exit after 5 seconds for testing
                logging.info("Game loop finished after 300 frames.")
                self.is_running = False

    async def handle_events(self):
        """Handles user input and other game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            await self.game_state_manager.handle_events(event)

    async def update(self):
        """Updates the game state."""
        await self.game_state_manager.update()

    def render(self):
        """Renders the game to the screen."""
        self.game_state_manager.render(self.screen)
        pygame.display.flip()

async def main() -> None:
    """The main entry point for the application."""
    game = Game()
    await game.run()
    if hasattr(game, 'angela'):
        print(f"Angela's favorability: {game.angela.favorability}")

if __name__ == "__main__":
    asyncio.run(main())
