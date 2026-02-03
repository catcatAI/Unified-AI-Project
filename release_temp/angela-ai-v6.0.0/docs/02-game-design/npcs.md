# NPC System

## Overview

This document provides an overview of the Non-Player Character (NPC) system, defined in `src/game/npcs.py`. This module is responsible for loading, creating, and managing the NPCs that populate the world of "Angela's World."

## Purpose

The purpose of the NPC system is to create a living, interactive world for the player. NPCs provide quests, information, and dialogue, making the world feel more dynamic and engaging. This system is designed to be data-driven, allowing for easy creation and modification of characters.

## Key Responsibilities and Features

*   **`NPC` Class**: Represents a single NPC in the game. Each instance holds all the data relevant to that character, including:
    *   Basic properties: `id`, `name`, `type`.
    *   Visuals: `image` (their in-game sprite) and `portrait` (for dialogues).
    *   Position: A `rect` for their location in the game world.
    *   Dialogue: A `dialogue_tree` that contains their conversational responses.
    *   State: `relationship_level` with the player and `event_flags` to track story progression.
*   **Data-Driven Design**: NPC data (name, position, dialogue, etc.) is loaded from an external JSON file (`data/game_data/npcs.json`). This allows for easy editing and expansion of the game's cast of characters without needing to change the source code.
*   **NPC Factory (`create_npc`)**: A factory function that takes an `npc_id` and instantiates a corresponding `NPC` object, loading its data from the JSON file and its graphics from the game's asset manager.
*   **Basic Dialogue System (`interact`)**: The `NPC` class includes a simple interaction method that can display dialogue from its `dialogue_tree`. The dialogue shown can be dependent on the `relationship_level` with the player, allowing for conversations that evolve over time.

## How it Works

At startup, the `load_npc_data()` function is called to read the `npcs.json` file and store the data in memory. When a game scene is loaded, it calls the `create_npc()` function for each NPC that should appear in that scene. This creates `NPC` objects with the appropriate data and graphics. When the player interacts with an NPC, the `interact()` method of that NPC is called, which then uses the game's dialogue system to display the appropriate line of text.

## Integration with Other Modules

*   **`Game` Object**: The `NPC` class holds a reference to the main `Game` object, giving it access to global systems like the asset manager and the dialogue box.
*   **Game Scenes**: Scenes are responsible for creating the specific NPCs they contain by calling the `create_npc` factory function.
*   **`DialogueBox`**: NPCs use the game's dialogue box UI element to present their conversations to the player.

## Code Location

`apps/backend/src/game/npcs.py`