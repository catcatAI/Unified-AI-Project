# FormulaEngineTypes: Formula Configuration Type Definitions

## Overview

This document provides an overview of the `types.py` module (`src/core_ai/formula_engine/types.py`), specifically focusing on the `FormulaConfigEntry` TypedDict. This module defines the structured schema for configuration entries used by the Formula Engine.

## Purpose

The primary purpose of `FormulaConfigEntry` is to provide a clear, type-hinted schema for defining rules or "formulas" that the Formula Engine will execute. This ensures consistency and facilitates validation of the configuration data, making it easier to manage, extend, and maintain the engine's behavior. By using `TypedDict`, it enhances code readability and allows for static analysis of configuration structures.

## Key Responsibilities and Features

*   **Typed Dictionary (`TypedDict`)**: `FormulaConfigEntry` is defined as a `TypedDict`, which means it enforces a specific structure and type hints for its keys. This significantly improves code readability, maintainability, and enables better tooling support (e.g., IDE autocompletion, static type checking).
*   **Required Fields**: Specifies essential fields that must be present in every formula configuration entry:
    *   `name` (Required[str]): A unique identifier for the formula.
    *   `conditions` (Required[List[str]]): A list of conditions that must be met for the formula's action to be triggered.
    *   `action` (Required[str]): The name of the action to be performed when conditions are met.
*   **Optional Fields**: Includes several optional fields to provide flexibility and additional metadata for each formula:
    *   `description` (Optional[str]): A human-readable explanation of what the formula does.
    *   `parameters` (Optional[Dict[str, Any]]): A dictionary of parameters to be passed to the `action`.
    *   `priority` (Optional[int]): An integer indicating the execution priority of the formula.
    *   `enabled` (Optional[bool]): A boolean flag to enable or disable the formula.
    *   `version` (Optional[str]): A version string for the formula, useful for tracking changes.

## How it Works

This module primarily serves as a data structure definition and does not contain executable logic itself. It is utilized by the `FormulaEngine` (and potentially other related components) to parse and validate its configuration files. By adhering to the `FormulaConfigEntry` schema, each formula entry ensures that it provides all necessary information in the correct format, preventing runtime errors due to malformed configurations.

## Integration with Other Modules

*   **`FormulaEngine`**: This is the primary consumer of the `FormulaConfigEntry` type definition. The `FormulaEngine` will load configuration files and expect each entry to conform to this schema for proper interpretation and execution of rules.
*   **`typing`**: The standard Python library that provides the `TypedDict` class and other type-hinting utilities, which are fundamental to the definition of `FormulaConfigEntry`.

## Code Location

`src/core_ai/formula_engine/types.py`