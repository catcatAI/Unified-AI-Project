# UI: Dialogue Box and User Interface Elements

## Overview

The `ui.py` (`src/game/ui.py`) module is responsible for **rendering and managing user interface (UI) elements** within "Angela's World," with a primary focus on the `DialogueBox`. This component is essential for presenting character conversations to the player in a clear and visually appealing manner.

It handles the display of character portraits, names, and dialogue text, making the narrative interactions engaging and easy to follow.

## Key Responsibilities and Features

1.  **Dialogue Box Management (`DialogueBox`)**: 
    *   Controls the visibility (`is_active`) of the dialogue box.
    *   Stores the `text` of the dialogue, the `character_name` speaking, and their `portrait` image.

2.  **Visual Rendering**: 
    *   Draws the dialogue box background (semi-transparent black) and a white border.
    *   Renders the character's portrait within a designated area, complete with its own border.
    *   Displays the character's name (in yellow) and the dialogue text (in white) using Pygame's font rendering capabilities.

3.  **Display Control (`show`, `hide`)**: 
    *   The `show` method activates the dialogue box and sets its content.
    *   The `hide` method deactivates the dialogue box, making it disappear from the screen.

4.  **Font and Styling**: 
    *   Uses a `pygame.font.Font` object for rendering text, allowing for control over font size and style.
    *   Defines specific colors for the name and text to enhance readability and visual hierarchy.

## How it Works

An instance of `DialogueBox` is created by the game. When a dialogue needs to be displayed (e.g., during an NPC interaction), the `show` method is called with the text, character name, and portrait. In each frame of the game loop, the `DialogueBox`'s `render` method is called. If `is_active` is true, it draws all its components onto the game surface. The player can then hide the dialogue box, typically by pressing an interaction key, which calls the `hide` method.

## Integration with Other Modules

-   **`Game` (main.py)**: The main game loop calls the `DialogueBox`'s `render` method.
-   **`Scenes`**: Game scenes (e.g., `VillageScene`) interact with the `DialogueBox` to display conversations when the player interacts with NPCs.
-   **`NPCs`**: NPCs provide the character name, dialogue text, and portrait images that are displayed by the `DialogueBox`.
-   **`Angela`**: Angela's dialogue would also be displayed through this `DialogueBox`.

## Code Location

`src/game/ui.py`
