# Tiles: Game Map and Terrain Management

## Overview

The `tiles.py` (`src/game/tiles.py`) module is a foundational component within "Angela's World" responsible for **defining and managing the game's map and terrain**. It provides the building blocks for creating the game world, including individual tiles, their properties, and the overall tilemap structure.

This module is crucial for rendering the game environment, enabling player movement, and supporting interactions with the terrain (e.g., farming, mining).

## Key Responsibilities and Features

1.  **Tile Definition (`Tile`)**: 
    *   Represents a single unit of the game map.
    *   Each tile has `x` and `y` coordinates, a `tile_type` (e.g., 'grass', 'tilled', 'planted', 'rock'), and can optionally hold a `crop` or a `rock` entity.

2.  **Rock Entity (`Rock`)**: 
    *   A simple class representing a rock object on a tile, with a `health` attribute (suggesting it can be mined or destroyed).

3.  **Tile Map Generation (`TileMap`)**: 
    *   Manages the entire game map as a 2D grid of `Tile` objects.
    *   Randomly generates the initial map, including the placement of `rock` tiles.

4.  **Tile Rendering**: 
    *   The `TileMap`'s `render` method draws each tile on the game surface.
    *   Currently, it uses simple colored squares to represent different tile types, providing a visual representation of the terrain.

## How it Works

The `TileMap` is initialized with a specified width and height, creating a grid of `Tile` objects. Each `Tile` is assigned a type, with some randomly designated as 'rock' tiles. In the game loop, the `TileMap`'s `render` method is called, which iterates through all tiles and draws a colored rectangle corresponding to each tile's type. This creates the visual background and interactive elements of the game world.

## Integration with Other Modules

-   **`Game` (main.py)**: The main game loop creates and renders the `TileMap`.
-   **`Player`**: The player character moves across the `TileMap`, and their interactions might change tile properties (e.g., tilling grass).
-   **`Scenes`**: Game scenes would utilize the `TileMap` to define their playable areas and visual backgrounds.
-   **`Items`**: Crops (defined in `items.py`) would be associated with `planted` tiles.

## Code Location

`src/game/tiles.py`
