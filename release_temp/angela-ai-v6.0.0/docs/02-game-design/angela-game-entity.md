# Angela Game Entity

## Overview

The `Angela` class (`src/game/angela.py`) represents Angela as a playable or interactive character within the "Angela's World" game. This implementation bridges the core AI functionalities (managed by the `DialogueManager`) with the game's visual and interactive elements. It defines Angela's in-game appearance, her movement, and her ability to engage with the player through dialogue and a favorability system.

This module is crucial for bringing Angela to life within the game environment, allowing players to interact with her as a dynamic and responsive AI character.

## Key Responsibilities and Features

1.  **Visual Representation and Animation**: 
    *   Manages Angela's visual assets (images/sprites) and her on-screen position.
    *   Includes basic animation logic, such as her `appear_speed` when entering a scene.

2.  **In-Game Interaction and Favorability**: 
    *   Tracks Angela's `favorability` score, which can be increased or decreased based on player actions (e.g., giving gifts).
    *   The `give_gift` method demonstrates how specific items can influence her favorability.

3.  **Proactive Interaction (Placeholder)**: 
    *   The `check_for_proactive_interaction` method is a placeholder for future logic that would allow Angela to initiate interactions with the player based on game state or player status (e.g., if the player is tired).

4.  **Dialogue Integration (`get_dialogue`)**: 
    *   Serves as the primary interface for player-initiated dialogue with Angela.
    *   Delegates the actual dialogue generation to the core AI's `DialogueManager`, ensuring that Angela's responses are consistent with her AI personality and knowledge.

## How it Works

The `Angela` object is instantiated within the game loop. Its `update` method handles visual changes and triggers proactive interaction checks. The `render` method draws Angela on the game surface. Player interactions, such as giving gifts, directly modify her `favorability`. When the player initiates dialogue, the `get_dialogue` method passes the player's message to the `DialogueManager` and returns Angela's AI-generated response.

## Integration with Other Modules

-   **`DialogueManager`**: The most critical integration, as it provides Angela's conversational intelligence. The `Angela` game entity acts as a proxy, passing player input to the `DialogueManager` and rendering its responses.
-   **Game Assets**: Relies on the game's asset management system to load Angela's images and other visual elements.
-   **Player State**: Future implementations of proactive interaction will likely depend on accessing the player's current state (e.g., health, inventory, location).
-   **Inventory/Items**: The `give_gift` method directly interacts with the concept of in-game items.

## Code Location

`src/game/angela.py`
