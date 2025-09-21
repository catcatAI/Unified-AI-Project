# MetaFormulasErrX: Semantic Error Variables for Meta-Formulas

## Overview

This document provides an overview of the `errx.py` module (`src/core_ai/meta_formulas/errx.py`). This module defines the `ErrX` class, which represents a semantic error variable specifically designed for handling and propagating errors within the meta-formula evaluation and processing system.

## Purpose

The primary purpose of `ErrX` is to provide a structured and standardized way to represent and manage errors that occur during the evaluation or processing of meta-formulas. This allows the system to gracefully handle unexpected conditions, provide detailed error information, and potentially trigger sophisticated error recovery or fallback mechanisms. By encapsulating error details, it facilitates more robust and intelligent error management within the AI's reasoning processes.

## Key Responsibilities and Features

*   **Structured Error Representation**: The `ErrX` class encapsulates two key pieces of information:
    *   `error_type` (str): A string that broadly categorizes the type of semantic error (e.g., "TYPE_MISMATCH", "UNDEFINED_VARIABLE", "INVALID_OPERATION").
    *   `details` (dict): A dictionary that provides additional, context-specific information about the error. This can include the specific values involved, the location of the error in the formula, or any other relevant diagnostic data.
*   **Readability and Debugging**: The `__repr__` method is implemented to provide a clear and informative string representation of the `ErrX` instance. This is highly valuable for debugging purposes, allowing developers to quickly understand the nature and context of an error when it is logged or printed.

## How it Works

Instances of `ErrX` are created and returned or raised when a semantic error is detected during the operations of the meta-formula system. Instead of simply raising generic exceptions, the system can return an `ErrX` object, which can then be inspected by upstream components. This allows different parts of the AI to programmatically check the `error_type` and `details` of a failure, enabling more precise and intelligent reactions, such as attempting alternative strategies, logging specific warnings, or informing the user about the exact nature of a problem.

## Integration with Other Modules

*   **`MetaFormula` (Conceptual)**: The broader `MetaFormula` engine or framework would be the primary consumer and producer of `ErrX` instances. It would use `ErrX` to signal semantic issues encountered during formula construction, validation, or execution.
*   **`MetaFormulaEvaluator` (Conceptual)**: A component responsible for evaluating meta-formulas would interpret and handle `ErrX` instances. It might use the `error_type` and `details` to decide on the next course of action, such as retrying with different parameters or escalating the error.
*   **Error Handling Logic**: Any part of the AI system that processes the results of meta-formula evaluations would need to be aware of `ErrX` objects and implement logic to handle them appropriately.

## Code Location

`src/core_ai/meta_formulas/errx.py`