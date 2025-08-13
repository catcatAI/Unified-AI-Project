# LogicTool: Evaluating Logical Expressions

## Overview

This document provides an overview of the `LogicTool` module (`src/tools/logic_tool.py`). Its primary function is to provide the AI with the capability to evaluate boolean logical expressions.

This tool is a fundamental component of the AI's reasoning capabilities, essential for tasks that involve decision-making, query filtering, and understanding complex conditional statements.

## Key Responsibilities and Features

*   **Dual Evaluation Strategy**: The `LogicTool` implements a sophisticated, hybrid approach to evaluating logical expressions, ensuring both performance and reliability:
    1.  **Neural Network (`LogicNNModel`)**: The primary evaluation method is a machine learning model trained to predict the outcome of logical expressions. This allows for potentially faster evaluation and the ability to handle variations in expression format.
    2.  **Parser/Evaluator (`LogicParserEval`)**: A traditional, rule-based parser that recursively evaluates the expression string. This serves as a robust fallback mechanism if the neural network model is unavailable or fails to produce a confident prediction.
*   **Lazy Loading**: To optimize startup performance, the `LogicParserEval` and `LogicNNModel` instances are loaded only when they are first needed.
*   **TensorFlow Dependency Management**: The tool intelligently checks for the availability of the TensorFlow library using the `dependency_manager` before attempting to load the `LogicNNModel`. This prevents import errors and allows the tool to function in a fallback mode even if TensorFlow is not installed.
*   **Unified Interface (`evaluate_expression`)**: Provides a single, unified method for evaluating expressions. This method automatically handles the logic of prioritizing the neural network and gracefully falling back to the parser, abstracting this complexity from the caller.

## How it Works

When the `evaluate_expression` method is called, it first attempts to use the `LogicNNModel` for evaluation. If the model is not loaded, is unavailable (due to missing dependencies), or fails during the prediction process, the tool seamlessly falls back to using the `LogicParserEval`. This hybrid strategy combines the potential speed and pattern recognition advantages of a neural network with the deterministic accuracy and reliability of a traditional parser, ensuring that the AI can always evaluate logical expressions effectively.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool is designed to be invoked by the `ToolDispatcher` when the AI's intent is to evaluate a logical expression. The `ToolDispatcher` extracts the expression from the user's query and passes it to this tool.
*   **`LogicNNModel`**: The neural network model used for the primary evaluation strategy. This model is loaded from `data/models/logic_model_nn.keras`.
*   **`LogicParserEval`**: The parser-based logic evaluator that serves as the fallback mechanism.
*   **`dependency_manager`**: Used to safely check for the availability of the TensorFlow library before attempting to load the neural network model.

## Code Location

`src/tools/logic_tool.py`