# NPCs: Non-Player Characters

## Overview

The `npcs.py` (`src/game/npcs.py`) module defines the **Non-Player Characters (NPCs)** within "Angela's World." It provides the foundational `NPC` class and utilities for loading and instantiating various NPCs, each with their unique data, visual representation, and interaction capabilities.

This module is crucial for populating the game world with interactive entities that can engage with the player, provide quests, offer services, or simply add to the game's ambiance.

## Key Responsibilities and Features

1.  **NPC Class Definition (`NPC`)**: 
    *   The base class for all non-player characters.
    *   Each NPC has an `id`, `name`, `npc_type`, visual assets (sprite and portrait), position (`x`, `y`), a `dialogue_tree`, a `relationship_level` with the player, and `event_flags`.

2.  **Centralized NPC Data (`_NPC_DATA`)**: 
    *   A global dictionary (`_NPC_DATA`) stores the static definitions for all NPCs, loaded from `data/game_data/npcs.json`.
    *   Each NPC definition includes its visual assets, starting position, and dialogue structure.

3.  **NPC Instantiation (`create_npc`)**: 
    *   A utility function that takes an `npc_id` and returns a new `NPC` instance, populating it with data from `_NPC_DATA` and loading its visual assets from the game's asset manager.

4.  **Dialogue System Integration (`interact`)**: 
    *   Includes a placeholder `interact` method that, when called, would initiate a dialogue with the NPC.
    *   The dialogue content is retrieved from the NPC's `dialogue_tree`, potentially based on the player's `relationship_level` or `event_flags`.

5.  **Visual Representation**: 
    *   Handles the rendering of the NPC's sprite on the game surface.

## How it Works

Upon module import, `npcs.py` attempts to load all NPC definitions from `npcs.json`. When `create_npc` is called, it retrieves the relevant data and creates an `NPC` object. This object is then responsible for rendering itself in the game world and handling interactions. The `interact` method is designed to be extended for more complex dialogue flows, potentially involving the `DialogueManager` for AI-driven conversations.

## Integration with Other Modules

-   **`Game` (main.py)**: The main game loop would create and manage `NPC` instances.
-   **`Player`**: Players interact with NPCs, triggering their `interact` method.
-   **`DialogueManager`**: While currently a placeholder, the `interact` method is designed to integrate with the `DialogueManager` for dynamic and AI-driven conversations.
-   **Game Assets**: Relies on the game's asset management system to load NPC sprites and portraits.
-   **`items.py`**: NPCs might give or receive items, interacting with the item system.

## Code Location

`src/game/npcs.py`
