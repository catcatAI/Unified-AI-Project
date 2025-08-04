# Inventory System

## Overview

The `Inventory` class (`src/game/inventory.py`) is a fundamental game component within "Angela's World" responsible for **managing a collection of items** for a game entity (typically the player). It provides core functionalities for adding, removing, and querying the quantity of various items.

This module is crucial for implementing game mechanics related to item collection, usage, and resource management, directly impacting player progression and interaction with the game world.

## Key Responsibilities and Features

1.  **Item Storage**: 
    *   Maintains an internal dictionary (`self.items`) to store item names as keys and their quantities as values.

2.  **Adding Items (`add_item`)**: 
    *   Increases the quantity of an existing item or adds a new item to the inventory if it doesn't already exist.

3.  **Removing Items (`remove_item`)**: 
    *   Decreases the quantity of an item.
    *   If the quantity drops to zero or below, the item is completely removed from the inventory.
    *   Returns `True` if the item was successfully removed (or its quantity reduced), `False` otherwise (e.g., if the item was not found).

4.  **Getting Item Count (`get_item_count`)**: 
    *   Retrieves the current quantity of a specific item in the inventory.
    *   Returns `0` if the item is not present in the inventory.

## How it Works

The `Inventory` class provides a simple, dictionary-based system for managing items. When an item is added, its quantity is incremented; if it's new, it's added with a quantity. When an item is removed, its quantity is decremented, and if it reaches zero, the item entry is removed. This straightforward approach makes it easy to track consumable items, quest items, or any other collectible in the game.

## Integration with Other Modules

-   **`Player`**: The `Player` class would typically hold an instance of `Inventory` to manage the player's collected items.
-   **`Angela`**: The `Angela` game entity interacts with the player's inventory (e.g., via `give_gift`) to influence favorability based on items given.
-   **`Items`**: Relies on the `items.py` module (or similar) to define the properties and types of items that can be stored in the inventory.
-   **Game Mechanics**: Directly supports game mechanics such as crafting, trading, quest completion, and resource consumption.

## Code Location

`src/game/inventory.py`
