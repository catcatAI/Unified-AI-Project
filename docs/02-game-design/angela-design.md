# Angela - AI Character Design

## Overview

This document provides an overview of the `Angela` class, defined in `src/game/angela.py`. This class represents the primary AI character, Angela, within the "Angela's World" game. It serves as the bridge between the game's visual representation and the backend AI's complex decision-making and dialogue systems.

## Purpose

The `Angela` class is responsible for managing all aspects of Angela's presence and behavior within the game world. This includes her on-screen appearance, her relationship with the player, and her conversational interactions. It is the primary object through which the player interacts with the AI.

## Key Responsibilities and Features

*   **In-Game Representation**: Manages Angela's visual sprite, her position on the screen, and handles simple animations, such as her appearing on screen.
*   **Favorability System**: A core mechanic for tracking the player's relationship with Angela.
    *   `increase_favorability()` / `decrease_favorability()`: Methods to modify the favorability score based on player actions.
    *   `give_gift()`: A specific interaction where the player can give items to Angela, which affects her favorability based on the item.
*   **Dialogue Integration**: Contains an instance of the `DialogueManager`, which links Angela's character to the core conversational AI.
    *   `get_dialogue()`: An async method that takes the player's message, passes it to the `DialogueManager`, and returns the AI's response.
*   **Proactive Behavior**: Includes a placeholder for a `check_for_proactive_interaction()` method. This is intended to allow Angela to initiate conversations or actions based on the game state (e.g., noticing the player is low on health), making her feel more alive and aware.

## How it Works

The `Angela` object is a central component of the main game state. During the game loop, its `update()` and `render()` methods are called continuously to update her state and draw her on the screen. When the player interacts with Angela (e.g., by speaking to her or giving her an item), the game calls the relevant methods on the `Angela` instance (e.g., `get_dialogue()` or `give_gift()`). These methods then modify Angela's internal state (like `favorability`) or communicate with backend AI systems (like the `DialogueManager`) to generate a response.

## Integration with Other Modules

*   **`DialogueManager`**: This is the most critical integration point. The `Angela` class uses the `DialogueManager` as its "brain" for generating conversational responses, effectively connecting the in-game character to the powerful backend language models.
*   **Game Asset Manager**: Loads Angela's portrait and other visual assets from the central asset management system.
*   **Player and Game State**: The `Angela` class will interact with the `Player` object and the main `Game` object to get context for her proactive behaviors.

## Code Location

`apps/backend/src/game/angela.py`
