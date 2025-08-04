# Scenes and Game State Management

## Overview

The `scenes.py` (`src/game/scenes.py`) module is fundamental to the structure and flow of "Angela's World." It defines the concept of **game scenes** (different areas or states of the game) and implements a **Game State Manager** to control transitions between these scenes. This modular approach allows for organized development of distinct game environments and their associated logic.

This module is crucial for creating a dynamic and engaging player experience, where the game world can change and evolve based on player actions and narrative progression.

## Key Responsibilities and Features

1.  **Base Scene Class (`Scene`)**: 
    *   Serves as an abstract base class for all game scenes.
    *   Defines the common interface for `handle_events`, `update`, and `render` methods that all scenes must implement.

2.  **Specific Scene Implementation (`VillageScene`)**: 
    *   A concrete example of a game scene, representing the village area.
    *   Loads scene-specific assets (backgrounds, NPCs).
    *   Manages player interaction with NPCs, triggering dialogue boxes.
    *   Integrates the `Player` and `NPC` entities within its context.

3.  **Game State Manager (`GameStateManager`)**: 
    *   The central component for controlling the overall flow of the game.
    *   Maintains a dictionary of available game states (scenes).
    *   Manages the `current_state`, delegating event handling, updates, and rendering to the active scene.
    *   Enables seamless transitions between different game scenes.

4.  **Player-NPC Interaction**: 
    *   Within `VillageScene`, it detects when the player is near an NPC and presses the interaction key (e.g., 'E').
    *   Triggers the NPC's `interact` method and displays a `DialogueBox` with the NPC's response.

5.  **Resource Loading**: 
    *   Scenes are responsible for loading their specific assets (e.g., background images, NPC sprites) from the game's asset manager.

## How it Works

The `GameStateManager` is initialized with all available game scenes. In the main game loop, the `GameStateManager`'s `handle_events`, `update`, and `render` methods are called. These methods, in turn, call the corresponding methods of the `current_state` (the active scene). Each scene then manages its own logic, including player and NPC updates, and rendering its specific elements. When a condition for a scene change is met (e.g., player enters a new area, quest completed), the `GameStateManager` can switch the `current_state` to a new scene.

## Integration with Other Modules

-   **`Game` (main.py)**: The main game loop drives the `GameStateManager`.
-   **`Player`**: The `Player` instance is updated and rendered by the active scene.
-   **`NPCs`**: NPCs are loaded and managed within specific scenes, and their interaction logic is handled here.
-   **`UI` (DialogueBox)**: The `DialogueBox` is used by scenes to display conversational elements.
-   **Game Assets**: Scenes rely on the game's asset management to load their visual components.

## Code Location

`src/game/scenes.py`
