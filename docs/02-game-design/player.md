# Player Character

## Overview

This document provides an overview of the `Player` class, defined in `src/game/player.py`. This class represents the player's character within the world of "Angela's World."

## Purpose

The `Player` class is responsible for managing all aspects of the player's state and their direct interactions with the game world. This includes their position, movement, appearance, and their inventory of items.

## Key Responsibilities and Features

*   **State Management**: The class holds all the essential data for the player, such as their `name`, `appearance` details (hair style, color, etc.), on-screen position (`rect`), and `inventory`.
*   **Movement**: The `update()` method contains the logic for player movement. It checks for keyboard input (arrow keys) and updates the player's position accordingly.
*   **Inventory**: Each `Player` instance has its own `Inventory` object, which is used to store and manage the items they collect throughout the game.
*   **Customizable Appearance**: The player's appearance is stored as a dictionary, with a `default_appearance()` method to provide a fallback look. This is designed to allow for player customization in the future.
*   **Action Handling**: Includes a placeholder for a `current_action` system, which will be used to manage states where the player is busy with an activity like fishing or mining and cannot move.

## How it Works

The `Player` object is created and managed by the main `Game` class. Its `update()` and `render()` methods are called once per frame in the main game loop. The `update()` method handles movement input, while the `render()` method draws the player's sprite at its current position on the screen.

## Integration with Other Modules

*   **`Game` Class**: The main `Game` object is responsible for creating and holding the `Player` instance.
*   **`Inventory` Class**: The `Player` class instantiates and uses the `Inventory` class to manage its collection of items.
*   **Pygame**: The `Player` class relies heavily on Pygame for handling keyboard input for movement and for managing the player's sprite and on-screen rectangle.

## Code Location

`apps/backend/src/game/player.py`