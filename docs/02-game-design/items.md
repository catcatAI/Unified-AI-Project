# Items: Game Item Definitions and Management

## Overview

The `items.py` (`src/game/items.py`) module is a core component within the "Angela's World" game that defines and manages **all in-game items**. It provides a structured way to represent items, their properties, and a utility for creating item instances based on predefined data.

This module is crucial for populating the game world with interactive objects, supporting inventory systems, crafting mechanics, and player-NPC interactions involving items.

## Key Responsibilities and Features

1.  **Item Class Definition (`Item`)**: 
    *   Defines the basic structure for all items in the game.
    *   Each item has a `name`, `description`, and an `icon` (a Pygame Surface for visual representation).

2.  **Centralized Item Data (`ITEM_DATA`)**: 
    *   A dictionary (`ITEM_DATA`) holds the static definitions for all items, mapped by a unique item ID.
    *   Each item definition includes its `name`, `description`, and `type` (e.g., "currency", "material", "seed", "crop").
    *   This data could be loaded from external JSON or YAML files in future iterations for easier content management.

3.  **Item Instantiation (`create_item`)**: 
    *   A utility function that takes an `item_id` and returns a new `Item` instance populated with data from `ITEM_DATA`.
    *   Includes a placeholder for the item icon (a yellow square) that would be replaced with actual loaded assets in a full game.

## How it Works

The `ITEM_DATA` dictionary serves as the single source of truth for all item properties. When `create_item` is called with an item's ID, it retrieves the corresponding data from `ITEM_DATA` and uses it to construct a new `Item` object. This object can then be added to a player's inventory, placed in the game world, or used in other game mechanics.

## Integration with Other Modules

-   **`Inventory`**: The `Inventory` class (`src/game/inventory.py`) relies on the `Item` class and the `create_item` function to manage collections of items for players or NPCs.
-   **`Angela`**: The `Angela` game entity interacts with items (e.g., `give_gift` method) to influence her favorability, demonstrating how items can be part of character interaction mechanics.
-   **`Player`**: Players would acquire and use items, interacting with the `Inventory` system which, in turn, uses this `items.py` module.
-   **Crafting/Trading Systems**: Future game systems would heavily depend on the definitions and properties provided by this module.

## Code Location

`src/game/items.py`
