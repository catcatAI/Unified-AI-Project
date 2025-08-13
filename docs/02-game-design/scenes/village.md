# Village Scene

## Overview

This document provides an overview of the `VillageScene` class, defined in `src/game/scenes/village.py`. This class is a specific implementation of a `Scene` and represents the main village area in "Angela's World."

## Purpose

The purpose of the `VillageScene` is to manage all the assets, characters, and interactions that are specific to the village environment. It serves as the primary hub for the player, where they can interact with NPCs and access other parts of the game.

## Key Responsibilities and Features

*   **Scene Initialization**: When the scene is created, it:
    *   Loads the background image for the village.
    *   Gets a reference to the main `Player` object.
    *   Loads all the NPCs that reside in the village by calling the `create_npc` factory function for each one.
    *   Gets a reference to the game's shared `DialogueBox`.
*   **Interaction Handling**: The `handle_events` method manages player interactions within the scene. It specifically checks for the 'E' key press to:
    *   Initiate dialogue with an NPC if the player is close enough.
    *   (Placeholder) Interact with resource nodes (e.g., trees, rocks).
*   **Scene Updates**: The `update` method is responsible for updating the state of the objects within the scene, primarily the player's movement.
*   **Rendering**: The `render` method draws all the visual elements of the scene in the correct order: the background, the NPCs, the player, and finally the dialogue box (if it is active).

## How it Works

The `VillageScene` is a self-contained environment that is managed by the `GameStateManager`. When the `GameStateManager` sets the `village` as the current state, the main game loop begins calling the `handle_events`, `update`, and `render` methods of the `VillageScene` instance. This is how the village is displayed on the screen and how the player is able to interact with it.

## Integration with Other Modules

*   **`Scene` (Base Class)**: The `VillageScene` inherits from the base `Scene` class and implements its required methods.
*   **`Game` Object**: It relies on the main `Game` object to get access to shared resources like the asset manager, the player object, and the dialogue box.
*   **`npcs.py`**: It uses the `create_npc` function from the NPC module to populate the scene with characters.
*   **`DialogueBox`**: It uses the shared `DialogueBox` instance to display conversations between the player and NPCs.

## Code Location

`apps/backend/src/game/scenes/village.py`
