# Inventory System

## Overview

This document provides an overview of the `Inventory` class, defined in `src/game/inventory.py`. This class provides a simple, yet effective, system for managing a collection of items, such as a player's inventory in the game.

## Purpose

The primary purpose of the `Inventory` class is to track the items that a player possesses. It provides the fundamental operations required for managing an inventory: adding items, removing items, and checking the quantity of a specific item.

## Key Responsibilities and Features

*   **Item Storage**: Uses a dictionary to store items, where the key is the item's name (a string) and the value is its quantity (an integer).
*   **`add_item(item_name, quantity)`**: Adds a specified quantity of an item to the inventory. If the item already exists, its quantity is increased; otherwise, it is added as a new entry.
*   **`remove_item(item_name, quantity)`**: Removes a specified quantity of an item. If the quantity of an item drops to zero or below, the item is completely removed from the inventory dictionary.
*   **`get_item_count(item_name)`**: Safely retrieves the current quantity of a given item, returning 0 if the item is not in the inventory.

## How it Works

The `Inventory` class is a straightforward implementation of an inventory system using a Python dictionary for data storage. This approach is efficient for looking up, adding, and removing items. The logic is self-contained within the class, making it easy to integrate into other parts of the game.

## Integration with Other Modules

*   **`Player` Class**: The `Player` class will be the primary owner of an `Inventory` instance, representing the items carried by the player.
*   **Game Logic**: Various game systems will interact with the player's inventory. For example, a crafting system might remove items, while a quest system might add reward items.

## Code Location

`apps/backend/src/game/inventory.py`