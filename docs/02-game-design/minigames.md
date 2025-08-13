# Minigames

## Overview

This document provides an overview of the minigame systems, defined in `src/game/minigames.py`. This module contains the logic and implementation for various interactive minigames within "Angela's World."

## Purpose

The purpose of the minigames module is to provide engaging, skill-based activities for the player to participate in. These minigames offer a break from the core dialogue and exploration loops and provide a way for the player to acquire resources and items.

## Key Responsibilities and Features

### `FishingGame` Class

The `FishingGame` is a simple, timing-based minigame where the player can catch fish.

*   **Starting the Game (`start`)**: Initializes the minigame by setting a random time for the catch to become available and a random position for the "catch zone."
*   **Event Handling (`handle_events`)**: Manages player input during the minigame. It specifically listens for the `SPACE` key, which triggers a catch attempt.
*   **Game Logic (`update`)**: Updates the state of the minigame, primarily by moving the fishing bar up and down after a certain amount of time has passed.
*   **Rendering (`render`)**: Draws the minigame's user interface, which includes the fishing bar background, the green "catch zone," and the red moving bar.
*   **Catching Mechanism (`check_catch`)**: Determines if the player was successful. If the moving bar is within the catch zone when the player attempts to catch, a "fish" item is added to the player's inventory.

## How it Works

The `FishingGame` is a self-contained class that manages its own state (`is_active`, `timer`, etc.). When a player initiates the fishing action in the main game, a `FishingGame` instance is created and its `start()` method is called. The game then enters a state where it continuously calls the `update()` and `render()` methods of the `FishingGame` instance. The player must watch the moving bar and press the spacebar at the correct time to succeed.

## Integration with Other Modules

*   **`Game` Object**: The `FishingGame` holds a reference to the main `Game` object, which gives it access to global game systems.
*   **`Player` Object**: Upon a successful catch, the `FishingGame` directly interacts with the `player.inventory` to add the caught fish.
*   **`GameStateManager`**: A dedicated game state or scene (e.g., a `FishingScene`) would be responsible for creating, running, and tearing down the `FishingGame` instance.

## Code Location

`apps/backend/src/game/minigames.py`