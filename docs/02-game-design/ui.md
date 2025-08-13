# UI System

## Overview

This document provides an overview of the UI (User Interface) system, defined in `src/game/ui.py`. This module contains the classes for various UI elements used in "Angela's World," starting with the `DialogueBox`.

## Purpose

The purpose of the UI system is to provide the visual components through which the player interacts with the game and receives information. This includes displaying conversations, managing menus, and showing other game-related data.

## Key Responsibilities and Features

### `DialogueBox` Class

The `DialogueBox` is the primary UI element for displaying conversations between the player and other characters.

*   **State Management**: The `DialogueBox` has an `is_active` flag to control whether it is currently visible.
*   **Content Management**: It stores the `text` of the dialogue, the `character_name` of the speaker, and their `portrait`.
*   **`show(text, character_name, portrait)`**: This method activates the dialogue box and populates it with the content of a specific line of dialogue.
*   **`hide()`**: This method deactivates and hides the dialogue box.
*   **Rendering (`render`)**: This method draws all the components of the dialogue box to the screen, including:
    *   A semi-transparent background panel.
    *   A border around the panel and the character portrait.
    *   The speaking character's portrait.
    *   The speaking character's name.
    *   The dialogue text itself.

## How it Works

The `DialogueBox` is a self-contained UI component. When a game event that triggers a conversation occurs (e.g., the player interacting with an NPC), the `show()` method of the `DialogueBox` is called with the appropriate text and character information. The active game scene is then responsible for calling the `render()` method of the `DialogueBox` in its own `render()` method, which draws the box on top of the game world. When the conversation is over, the `hide()` method is called to remove the box from the screen.

## Integration with Other Modules

*   **`Game` Class**: The main `Game` object will likely hold a single instance of the `DialogueBox` to be shared across all scenes.
*   **Scene Classes**: Any scene that can have dialogue (e.g., `VillageScene`) will need to call the `show()`, `hide()`, and `render()` methods of the `DialogueBox`.
*   **Character Classes (`NPC`, `Angela`)**: These classes provide the content (text, name, portrait) that is displayed in the `DialogueBox` when the player interacts with them.

## Code Location

`apps/backend/src/game/ui.py`