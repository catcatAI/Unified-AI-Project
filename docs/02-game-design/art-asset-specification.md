# Art Asset Specification

## Overview

The `metadata.md` (`src/game/assets/metadata.md`) document defines the **specifications for all art assets** used within the "Angela's World" game. It outlines crucial guidelines regarding dimensions, formats, and naming conventions for various visual resources, ensuring consistency and facilitating collaborative development.

This document is essential for artists, designers, and developers to maintain a unified visual style and efficient asset pipeline throughout the game's production.

## Key Specifications

### I. General Guidelines

-   **Format**: All image resources are recommended to use the `.png` format to support transparent backgrounds.
-   **Naming**: Filenames should use lowercase letters and underscores, clearly describing the asset's content (e.g., `player_walk_cycle.png`, `item_shizuku.png`).

### II. Third-Party Asset Licensing

-   Details licenses for any third-party assets used, ensuring legal compliance. An example is provided for a 16x16 grassland tileset licensed under CC-BY 4.0.

### III. Resolution

-   **Game Base Resolution**: `960x540` pixels (16:9 aspect ratio).
    *   This resolution is chosen to preserve the pixel art style while providing sufficient display space for UI and character portraits, and better adapting to modern displays.

### IV. Size Specifications

Detailed size and directory guidelines are provided for different categories of art assets:

1.  **Key Visuals** (`images/`):
    *   Used for game title screens, important story cutscenes, and promotional materials.
    *   Recommended size: `1920x1080` pixels.

2.  **HD Portraits** (`images/portraits/`):
    *   Full-size character portraits for the main interface (e.g., Electron app) or special in-game story moments.
    *   Recommended size: `400x600` pixels.

3.  **Backgrounds** (`images/backgrounds/`):
    *   Background images for various in-game scenes.
    *   Recommended size: `960x540` pixels.

4.  **Pixel Portraits** (`sprites/portraits/`):
    *   Used in daily in-game dialogue boxes, showing character busts and expression changes.
    *   Recommended size: `96x96` pixels.

5.  **Pixel Sprites** (`sprites/characters/`):
    *   Pixel art for in-game characters (player and NPCs) for movement and interaction.
    *   Recommended single frame size: `48x48` pixels.

6.  **Item and UI Icons** (`sprites/icons/`):
    *   Icons for items, tools, and UI elements displayed in inventory, shops, etc.
    *   Recommended size: `24x24` pixels.

## Importance and Usage

This specification is vital for:

-   **Consistency**: Ensures all art assets adhere to a unified style and technical requirements.
-   **Collaboration**: Provides clear guidelines for artists and developers working on the project.
-   **Asset Pipeline**: Streamlines the process of creating, integrating, and managing game assets.
-   **Performance**: Guides asset creation to optimize for game performance and visual quality.

## Code Location

`src/game/assets/metadata.md`
