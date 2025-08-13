# Item Definitions

## Overview

This document provides an overview of the item definition system, defined in `src/game/items.py`. This module is responsible for defining all the items that can exist within the "Angela's World" game.

## Purpose

The primary purpose of this module is to provide a centralized and easily extensible system for defining in-game items. It holds the master data for every item, including its name, description, and visual representation (icon). This centralized approach ensures consistency and makes it simple to add new items or modify existing ones.

## Key Responsibilities and Features

*   **`Item` Class**: A simple data class that encapsulates the properties of a single item, including its `name`, `description`, and `icon` (a Pygame Surface).
*   **`ITEM_DATA` Dictionary**: A dictionary that serves as the master database for all items in the game. Each item is defined by a unique ID (e.g., "shizuku", "wood") and contains its name, description, and type (e.g., `currency`, `material`, `seed`).
*   **`create_item(item_id)` Factory Function**: A function that takes an `item_id` and returns a fully instantiated `Item` object using the data from the `ITEM_DATA` dictionary. It currently uses a placeholder for the item icons.

## How it Works

All possible items in the game are defined as entries in the `ITEM_DATA` dictionary. When the game needs to create an instance of an item (e.g., when a player picks something up), it calls the `create_item()` function with the appropriate `item_id`. This function looks up the item's data in the `ITEM_DATA` dictionary and uses it to create and return a new `Item` object. This design pattern makes the item system highly data-driven and easy to manage.

## Integration with Other Modules

*   **`Inventory` Class**: The player's inventory will hold instances of the `Item` class created by this module.
*   **Game Logic**: The main game loop and various game systems (e.g., crafting, farming, quests) will call `create_item()` to generate items that are then given to the player or used in other game mechanics.

## Code Location

`apps/backend/src/game/items.py`