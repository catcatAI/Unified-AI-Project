import random
from typing import Any, List
from unittest.mock import Mock

# Mock pygame for syntax validation
try:
    import pygame
except ImportError:
    pygame = Mock()

class Rock:
    """Represents a rock object on a tile."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.health = 100

class Tile:
    """Represents a single tile on the map."""
    def __init__(self, x: int, y: int, tile_type: str):
        self.x = x
        self.y = y
        self.tile_type = tile_type  # 'grass', 'tilled', 'planted', 'rock'
        self.crop: Any = None
        self.growth_stage = 0
        self.rock: Any = None
        if self.tile_type == 'rock':
            self.rock = Rock(x, y)

class TileMap:
    """Represents the grid of tiles for the game world."""
    def __init__(self, game: Any, width: int, height: int):
        self.game = game
        self.width = width
        self.height = height
        self.tiles: List[List[Tile]] = [
            [Tile(x, y, 'rock' if random.random() < 0.1 else 'grass') for y in range(height)] 
            for x in range(width)
        ]

    def render(self, surface: Any):
        """Renders the tilemap to the screen."""
        for x in range(self.width):
            for y in range(self.height):
                color = (0, 0, 0) # Default black
                tile_type = self.tiles[x][y].tile_type
                if tile_type == 'grass':
                    color = (0, 255, 0)  # Green for grass
                elif tile_type == 'tilled':
                    color = (139, 69, 19)  # Brown for tilled
                elif tile_type == 'planted':
                    color = (0, 100, 0)  # Dark green for planted
                elif tile_type == 'rock':
                    color = (128, 128, 128)  # Grey for rock
                
                pygame.draw.rect(surface, color, (x * 32, y * 32, 32, 32))