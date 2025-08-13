# Scene and Game State Management

## Overview

This document provides an overview of the scene and game state management system, defined in `src/game/scenes.py`. This system is built around a state machine pattern that controls which part of the game is currently active.

## Purpose

The purpose of this system is to provide a structured and scalable way to manage the different states or "scenes" of the game. A scene could be a specific location (like the village), a menu screen, a minigame, or a dialogue sequence. By encapsulating the logic for each state into its own scene class, the system keeps the code organized and easy to maintain.

## Key Responsibilities and Features

*   **`GameStateManager` Class**: This is the core of the state machine.
    *   It holds a dictionary of all available scenes in the game.
    *   It maintains a reference to the `current_state` (e.g., 'village').
    *   It delegates all high-level `handle_events`, `update`, and `render` calls from the main game loop to the currently active scene.

*   **`Scene` Class**: This is an abstract base class that defines the common interface for all scenes. Every scene must have `handle_events`, `update`, and `render` methods.

*   **`VillageScene` Class**: This is a concrete implementation of a scene.
    *   It represents the main village area where the player can walk around and interact with NPCs.
    *   It is responsible for loading its own background, creating the NPCs that belong in the scene, and managing the dialogue box.
    *   It contains the logic for player-NPC interaction (e.g., checking for proximity and key presses to initiate dialogue).

## How it Works

The main `Game` object creates an instance of the `GameStateManager`. The `GameStateManager`, in turn, creates instances of all the different scenes and stores them in a dictionary. The main game loop then simply tells the `GameStateManager` to handle events, update, and render. The `GameStateManager` checks what its `current_state` is and passes the calls down to the appropriate scene object. This design makes it very simple to switch between different parts of the game by just changing the `current_state` string in the `GameStateManager`.

## Integration with Other Modules

*   **`Game` Class**: The `GameStateManager` is a key component of the main `Game` class.
*   **Character Classes (`Player`, `NPC`, `Angela`)**: Scenes are responsible for creating and managing the characters that appear within them.
*   **UI Classes (`DialogueBox`)**: Scenes use UI elements like the `DialogueBox` to display information to the player.

## Code Location

`apps/backend/src/game/scenes.py`