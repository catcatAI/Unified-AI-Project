# Minigames: Adding Interactivity and Variety

## Overview

The `minigames.py` (`src/game/minigames.py`) module introduces **interactive mini-games** into "Angela's World." These mini-games provide diversions from the main gameplay loop, offering players unique challenges and opportunities to earn rewards or advance specific in-game objectives.

This module is crucial for enhancing player engagement, adding replayability, and diversifying the gameplay experience beyond core narrative or exploration elements.

## Key Responsibilities and Features

1.  **Mini-Game Implementation (`FishingGame`)**: 
    *   Defines the `FishingGame` class, a simple example of a mini-game.
    *   Manages the mini-game's internal state, including its active status, timers, and game-specific elements (e.g., fishing bar position, catch zone).

2.  **Player Interaction**: 
    *   Handles player input specific to the mini-game (e.g., pressing the spacebar to attempt a catch in the `FishingGame`).
    *   Determines the outcome of player actions within the mini-game's rules.

3.  **Game State Integration**: 
    *   Integrates with the main game loop by providing `handle_events`, `update`, and `render` methods that can be called by the `GameStateManager`.

4.  **Reward System Integration**: 
    *   Upon successful completion of a mini-game, it can interact with the player's `Inventory` to add rewards (e.g., adding a 'fish' item).

## How it Works

When a mini-game is activated (e.g., the player interacts with a fishing spot), an instance of `FishingGame` is created and its `start` method is called. The mini-game then takes over the event handling, update, and rendering within the main game loop. Player input is processed by the mini-game's `handle_events` method. The `update` method progresses the mini-game's internal state (e.g., moving the fishing bar). The `render` method draws the mini-game's visual elements on the screen. Upon completion (success or failure), the mini-game deactivates itself, and control returns to the main game state.

## Integration with Other Modules

-   **`GameStateManager`**: The `GameStateManager` is responsible for transitioning into and out of mini-game states, and for calling the mini-game's update and render methods.
-   **`Player`**: The player's actions directly influence the mini-game, and rewards are added to the player's `Inventory`.
-   **`Inventory`**: The `Inventory` module is used to manage items obtained as rewards from mini-games.
-   **`Angela`**: While not directly integrated in this example, Angela could potentially offer mini-game challenges or provide commentary during mini-game play.

## Code Location

`src/game/minigames.py`
