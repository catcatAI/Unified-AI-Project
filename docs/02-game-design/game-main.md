# Game Main Module

## Overview

This document provides an overview of the main game module, defined in `src/game/main.py`. This module serves as the primary entry point and contains the main `Game` class that orchestrates the entire "Angela's World" application.

## Purpose

The purpose of this module is to initialize all necessary game systems, manage the main game loop, and coordinate the high-level interactions between different game components, such as the player, the AI character (Angela), and the various game states (e.g., main menu, gameplay, dialogue).

## Key Responsibilities and Features

*   **Game Initialization (`__init__`)**: The constructor is responsible for:
    *   Initializing the Pygame library.
    *   Setting up the game window, screen dimensions, and title.
    *   Loading all necessary game assets (images, sprites) into a central `self.assets` dictionary.
    *   Instantiating the core game objects: `Player`, `Angela`, and `GameStateManager`.
*   **Asset Loading (`load_assets`)**: A dedicated method that recursively scans the `assets` directory, loads all `.png` files, and organizes them into a structured dictionary for easy access throughout the game.
*   **Main Game Loop (`run`)**: The heart of the game. This asynchronous loop runs continuously and performs the following actions in order:
    1.  Handles user input and system events (`handle_events`).
    2.  Updates the state of all active game objects (`update`).
    3.  Renders the current scene to the screen (`render`).
    4.  Uses a clock to maintain a consistent frame rate.
*   **State Management Delegation**: The `Game` class does not handle game logic directly. Instead, it delegates all event handling, updates, and rendering calls to the `GameStateManager`, which acts as a state machine for the game.

## How it Works

When the `main.py` script is executed, it creates an instance of the `Game` class and calls its `run()` method. This begins the main game loop. The `Game` class acts as a high-level orchestrator. The actual game logic, rendering, and event handling for any given moment are determined by the current scene (e.g., `VillageScene`, `DialogueScene`) being managed by the `GameStateManager`. This design keeps the main game loop clean and separates the concerns of different game states into their own respective classes.

## Integration with Other Modules

*   **`GameStateManager`**: The `Game` class is tightly coupled with the `GameStateManager`, to which it delegates all core game loop operations.
*   **`Player` and `Angela`**: The `Game` class creates and holds the central instances of the player and the main AI character, making them accessible to other game systems.
*   **Pygame**: The entire application is built on top of the Pygame framework for graphics, sound, and input.

## Code Location

`apps/backend/src/game/main.py`