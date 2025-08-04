# Game Utilities

## Overview

The `utils.py` (`src/game/utils.py`) module provides a collection of **general-purpose utility functions** for the "Angela's World" game. Its primary function is to offer common helper methods that can be reused across various game components, promoting code reusability and reducing redundancy.

This module is essential for tasks that are not specific to any single game entity or system but are broadly useful throughout the game's development.

## Key Responsibilities and Features

1.  **Unique ID Generation (`generate_uid`)**:
    *   Generates a random, alphanumeric unique identifier of a specified `length`.
    *   This function is useful for assigning unique IDs to game entities, items, or any other element that requires a distinct identifier.

## How it Works

The `generate_uid` function uses Python's `random` and `string` modules to create a random sequence of uppercase letters and digits. This simple approach provides a quick and easy way to generate unique identifiers for in-game objects.

## Integration with Other Modules

-   **`Player`**: Could use `generate_uid` to assign a unique ID to the player character.
-   **`NPCs`**: NPCs could be assigned unique IDs using this utility.
-   **`Items`**: Individual item instances might use unique IDs for tracking.
-   **Game State Management**: Any part of the game that needs to uniquely identify an object or event can leverage this utility.

## Code Location

`src/game/utils.py`
