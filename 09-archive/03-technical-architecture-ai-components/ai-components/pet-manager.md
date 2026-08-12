# PetManager: Dynamic Desktop Pet Management

## Overview

This document provides an overview of the `PetManager` module, located at `apps/backend/src/pet/pet_manager.py`. This module is responsible for managing the state, behavior, and interactions of the desktop pet.

## Purpose

The `PetManager` is designed to create a dynamic and engaging desktop pet experience. Crucially, it allows the core AI to dynamically adjust the pet's personality and behavior rules, making the pet a living, evolving entity that can adapt to user interactions and contribute to the AI's learning and self-evolutionary goals.

## Key Responsibilities and Features

*   **State Management**: Tracks the pet's internal state, including `happiness`, `hunger`, and `energy` levels.
*   **Dynamic Personality**: Initializes with a `personality` profile (e.g., `curiosity`, `playfulness`) that can influence its reactions and learning.
*   **Behavior Rules**: Manages a set of `behavior_rules` that dictate how the pet responds to various interactions. These rules can be updated dynamically by the core AI via the `update_behavior` method.
*   **Interaction Handling (`handle_interaction`)**: Processes user inputs and updates the pet's state based on the defined behavior rules. This method serves as the primary interface for user engagement.
*   **Dynamic Behavior Adaptation (`update_behavior`)**: Allows the core AI to dynamically modify the pet's behavior rules. This is a critical feature for enabling the AI to learn and adapt the pet's responses over time, based on user feedback or observed outcomes.

## How it Works

The `PetManager` maintains the pet's internal state and applies behavior rules when interactions occur. The core AI can observe user interactions and the pet's resulting state changes. Based on this feedback, the AI can then call the `update_behavior` method to refine the pet's responses, making it more engaging or aligned with specific learning objectives. This creates a continuous feedback loop for the pet's evolution.

## Integration with Other Modules

*   **Core AI (Learning/Decision-making modules)**: The core AI will interact with `PetManager` to retrieve the pet's state, send interaction data, and most importantly, to dynamically `update_behavior` based on its learning and strategic goals.
*   **`EconomyManager`**: The pet's needs (e.g., hunger) might be linked to the in-game economy, requiring currency for food or accessories.
*   **User Interface (UI)**: The UI will interact with `PetManager` to display the pet's state and send user interaction commands.

## Code Location

`apps/backend/src/pet/pet_manager.py`
