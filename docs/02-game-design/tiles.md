# Tile Map System

## Overview

This document provides an overview of the tile map system, defined in `src/game/tiles.py`. This system is responsible for creating and managing the grid-based game world of "Angela's World."

## Purpose

The purpose of the tile map system is to provide a flexible and efficient way to build and render the game's environments. By dividing the world into a grid of tiles, it becomes easy to define different types of terrain, place objects, and manage interactions with the game world.

## Key Responsibilities and Features

*   **`TileMap` Class**: This class represents the entire game map.
    *   It holds a 2D array of `Tile` objects, which forms the grid-based world.
    *   Its `render()` method is responsible for drawing the entire tilemap to the screen.

*   **`Tile` Class**: This class represents a single tile in the map.
    *   Each tile has a `tile_type`, which can be `grass`, `tilled`, `planted`, or `rock`.
    *   A tile can contain other objects, such as a `crop` or a `rock`.

*   **`Rock` Class**: A simple class representing a rock object that can be placed on a tile.

*   **Procedural Generation**: The `TileMap` constructor includes simple procedural generation logic to randomly place `rock` tiles on the map.

## How it Works

When a `TileMap` is created, it generates a 2D list of `Tile` objects. Each tile is initialized with a default type of `grass`, but some are randomly changed to `rock`. The `render()` method of the `TileMap` then iterates through this 2D list and draws each tile as a colored rectangle on the screen, with the color determined by the tile's type. This provides a simple visual representation of the game world.

## Integration with Other Modules

*   **`Game` Class**: The main `Game` object is responsible for creating and holding the `TileMap` for the current area.
*   **Scene Classes (`VillageScene`, etc.)**: Each scene that represents a physical location in the game world will have its own `TileMap` instance to define its environment.

## Code Location

`apps/backend/src/game/tiles.py`