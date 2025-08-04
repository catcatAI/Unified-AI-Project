# Player: The Protagonist of Angela's World

## Overview

The `Player` class (`src/game/player.py`) represents the **player character** in "Angela's World." It encapsulates all the essential attributes and behaviors of the protagonist, including their visual representation, movement mechanics, inventory management, and interaction capabilities within the game environment.

This module is central to the player's experience, allowing them to navigate the world, collect items, and engage with other game entities.

## Key Responsibilities and Features

1.  **Player Representation**: 
    *   Manages the player's visual appearance, including their sprite and a customizable `appearance` dictionary (e.g., hair style, eye color, outfit).
    *   Handles the player's position and dimensions within the game world (`self.rect`).

2.  **Movement Mechanics**: 
    *   Processes keyboard input (arrow keys) to control the player's movement across the game screen.
    *   Defines a `PLAYER_SPEED` constant for consistent movement speed.

3.  **Inventory Management**: 
    *   Holds an instance of the `Inventory` class (`src/game/inventory.py`), allowing the player to collect, store, and manage items found or acquired in the game.

4.  **Action Handling (Placeholder)**: 
    *   Includes a `current_action` attribute and a placeholder logic within the `update` method for handling specific player actions like mining, fishing, or interacting with objects.

5.  **Game State Integration**: 
    *   Provides `handle_events`, `update`, and `render` methods that are called by the main game loop, ensuring the player character is responsive and visually represented.

## How it Works

The `Player` object is instantiated by the `Game` class. In each frame of the game loop, its `update` method checks for keyboard input to move the player. The `render` method draws the player's sprite on the screen. The `Inventory` instance allows for seamless item management. The `current_action` mechanism is designed to pause normal movement and allow for specialized mini-game or interaction logic to take over.

## Integration with Other Modules

-   **`Game` (main.py)**: The main game loop creates, updates, and renders the `Player` instance.
-   **`Inventory`**: The `Player` class directly uses the `Inventory` class to manage items.
-   **`Angela`**: The `Angela` game entity can interact with the player, potentially influencing their inventory or other attributes.
-   **Game Assets**: Relies on the game's asset management system to load player sprites.
-   **`Minigames`**: Player actions within minigames (e.g., fishing) can be initiated and managed through the `Player`'s `current_action`.

## Code Location

`src/game/player.py`
