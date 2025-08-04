# Game Main Module: Core Game Loop and Initialization

## Overview

The `main.py` (`src/game/main.py`) module serves as the **entry point and orchestrator for the "Angela's World" game**. It encapsulates the core game loop, handles the initialization of the Pygame environment, loads essential game assets, and manages the overall game state. This module brings together all the disparate game components to create a cohesive and interactive experience.

It is the central hub from which the entire game application is launched and controlled.

## Key Responsibilities and Features

1.  **Pygame Initialization**: 
    *   Initializes the Pygame library, setting up the display surface (`screen`), window caption, and game clock.
    *   Includes `os.environ` settings for `SDL_VIDEODRIVER` and `SDL_AUDIODRIVER` to `'dummy'`, which can be useful for running the game in headless environments or for specific testing setups.

2.  **Asset Loading (`load_assets`)**: 
    *   Recursively scans the `assets/` directory (e.g., `images/`, `sprites/`) for `.png` files.
    *   Loads these image assets into `pygame.Surface` objects and stores them in a structured `self.assets` dictionary, making them readily available throughout the game.
    *   Includes error handling for missing asset directories or failed image loads.

3.  **Game Loop (`run`)**: 
    *   Contains the main game loop, which continuously processes events, updates game logic, and renders the game state.
    *   Manages the game's `is_running` state, allowing for graceful exit.
    *   Controls the frame rate using `self.clock.tick(60)`.

4.  **Game State Management**: 
    *   Utilizes a `GameStateManager` (`src/game/scenes.py`) to handle transitions and logic for different game states (e.g., title screen, gameplay, menus).
    *   Delegates event handling, updates, and rendering to the current game state.

5.  **Character Instantiation**: 
    *   Creates instances of the main game characters: `Player` (`src/game/player.py`) and `Angela` (`src/game/angela.py`).

## How it Works

Upon execution, the `main.py` script initializes the `Game` class. The `Game` constructor sets up Pygame, loads all necessary visual assets, and creates instances of the `Player`, `Angela`, and `GameStateManager`. The `run` method then enters the infinite game loop, where it continuously calls `handle_events`, `update`, and `render` methods, which in turn delegate to the `GameStateManager` to process the current game state. This modular design ensures that different aspects of the game are managed by their respective components.

## Integration with Other Modules

-   **`scenes.py` (GameStateManager)**: The `main.py` orchestrates the game flow by interacting with the `GameStateManager`.
-   **`player.py`**: The `Player` instance is created and managed by the `Game` class.
-   **`angela.py`**: The `Angela` game entity is created and integrated into the game loop, allowing her to update and render.
-   **`assets/` directory**: The `load_assets` method directly interacts with the game's asset structure.

## Code Location

`src/game/main.py`
