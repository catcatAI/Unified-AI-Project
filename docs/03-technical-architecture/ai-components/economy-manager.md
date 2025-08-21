# EconomyManager: Dynamic In-Game Economic System

## Overview

This document provides an overview of the `EconomyManager` module, located at `apps/backend/src/economy/economy_manager.py`. This module is responsible for managing the in-game currency, transactions, and overall economic dynamics.

## Purpose

The `EconomyManager` is designed to be a flexible and adaptable economic system that can be dynamically influenced and updated by the core AI. Its primary purpose is to facilitate a living, evolving in-game economy that supports the desktop pet's needs and user interactions, while also serving as a testbed for AGI's ability to manage complex, self-regulating systems.

## Key Responsibilities and Features

*   **Dynamic Rule Management**: The manager initializes with a set of economic `rules` (e.g., `transaction_tax_rate`, `daily_coin_allowance`). These rules can be updated dynamically by the core AI via the `update_rules` method, allowing for real-time economic adjustments based on observed in-game behavior or AI learning.
*   **Transaction Processing (`process_transaction`)**: Handles the processing of in-game transactions, including updating balances and applying rules like tax rates. It logs transaction details for future analysis and learning.
*   **Balance Retrieval (`get_balance`)**: Provides the current currency balance for any given user.
*   **Adaptability for AGI**: The design emphasizes adaptability, allowing the core AI to experiment with different economic policies and observe their outcomes, thus contributing to the AI's self-evolutionary learning process.

## How it Works

The `EconomyManager` operates by maintaining a set of active economic rules. When a transaction occurs, these rules are applied. The core AI can monitor the state of the economy (e.g., through transaction logs or overall balance trends) and, based on its learning, call the `update_rules` method to adjust parameters like tax rates or daily allowances. This creates a feedback loop where the AI learns to manage and optimize the in-game economy.

## Integration with Other Modules

*   **Core AI (Learning/Decision-making modules)**: The core AI will interact with `EconomyManager` to retrieve economic data, process transactions, and most importantly, to dynamically `update_rules` based on its learning and strategic goals.
*   **`PetManager`**: The desktop pet will likely interact with the economy for actions like feeding (consuming currency) or purchasing items (e.g., pet accessories).
*   **Database/Persistence Layer**: (TODO) Future integration with a database (e.g., SQLite) will be needed to persist user balances and transaction logs.

## Code Location

`apps/backend/src/economy/economy_manager.py`
