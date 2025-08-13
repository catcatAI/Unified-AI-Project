# MetaFormulaBase: Base Class for Executable AI Logic

## Overview

This document provides an overview of the `meta_formula.py` module (`src/core_ai/meta_formulas/meta_formula.py`). This module defines the `MetaFormula` class, which serves as the abstract base class for all executable AI logic or "meta-formulas" within the system.

## Purpose

The primary purpose of `MetaFormula` is to establish a standardized and consistent foundation for creating, managing, and executing diverse pieces of AI logic. This abstraction promotes modularity, reusability, and maintainability across different AI functionalities. By enforcing a common interface, it allows higher-level components to interact with various meta-formulas uniformly, regardless of their underlying implementation details.

## Key Responsibilities and Features

*   **Abstract Base Class**: `MetaFormula` is designed to be inherited by all specific meta-formula implementations. It defines the fundamental structure and expected behavior for any meta-formula.
*   **Initialization**: During initialization, each `MetaFormula` instance requires a `name` (string) and a `description` (string). These attributes provide basic identification and human-readable documentation for the purpose and functionality of each meta-formula.
*   **`execute` Method**: Defines an abstract `execute` method. This method is the designated entry point for running the meta-formula's specific logic. Subclasses are required to override this method with their concrete implementation. If `execute` is called directly on the `MetaFormula` base class, it will raise a `NotImplementedError`, signaling that the method must be implemented by a subclass.

## How it Works

`MetaFormula` itself does not contain any executable AI logic. Its role is purely structural and definitional. It acts as a contract that all concrete meta-formula implementations must adhere to. This ensures that any component designed to work with meta-formulas can expect a consistent interface (`name`, `description`, `execute` method), simplifying the overall architecture and promoting interoperability. When a specific meta-formula is needed, a subclass of `MetaFormula` is instantiated, and its overridden `execute` method is called to perform the desired AI operation.

## Integration with Other Modules

*   **`MetaFormulaEngine` (Conceptual)**: A higher-level component (not defined in this module) would be responsible for discovering, loading, and executing instances of `MetaFormula` subclasses. This engine would rely on the consistent interface provided by `MetaFormula`.
*   **Specific MetaFormula Implementations**: Other modules throughout the AI system would inherit from `MetaFormula` to create concrete, specialized pieces of AI logic (e.g., `MetaFormulaForPlanning`, `MetaFormulaForReasoning`, `MetaFormulaForDecisionMaking`).
*   **`ErrX` (Conceptual)**: While not directly imported here, concrete `MetaFormula` implementations might interact with `ErrX` (from `src/core_ai/meta_formulas/errx.py`) to signal semantic errors during their execution.

## Code Location

`src/core_ai/meta_formulas/meta_formula.py`