# Game Utilities

## Overview

This document provides an overview of the game utility functions defined in `src/game/utils.py`. This module contains general-purpose helper functions that are useful across various parts of the game.

## Purpose

The purpose of this module is to centralize common, reusable utility functions that are not specific to any single game object or system. This promotes code reusability and keeps the codebase clean and organized.

## Key Responsibilities and Features

*   **Unique ID Generation (`generate_uid`)**: This function generates a unique alphanumeric identifier of a specified length (defaulting to 16 characters). It uses a combination of uppercase letters and digits.

## How it Works

The `generate_uid` function leverages Python's built-in `random` and `string` modules. It randomly selects characters from a predefined set (uppercase letters and digits) and joins them together to form a string of the desired length.

## Integration with Other Modules

*   **Any Game Component**: Any part of the game that requires a unique identifier for an object or entity can import and use the `generate_uid` function. For example, the `Player` class might use it to assign a unique ID to a new player instance.

## Code Location

`apps/backend/src/game/utils.py`