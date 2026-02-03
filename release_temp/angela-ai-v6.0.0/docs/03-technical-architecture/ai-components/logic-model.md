# Logic Model: Boolean Expression Evaluation

## Overview

The `logic_model` directory (`src/tools/logic_model/`) contains components that provide the Unified-AI-Project with a **lightweight system for evaluating simple logical propositions** (e.g., "true AND (NOT false OR true)"). This capability is crucial for enabling the AI to perform basic reasoning and decision-making based on Boolean logic.

The system offers two primary evaluation methods: a deterministic, rule-based parser and a neural network-based evaluator, allowing for flexibility in how logical expressions are processed.

## Key Components

1.  **`logic_data_generator.py`**:
    *   Generates datasets of logical propositions and their corresponding boolean answers.
    *   Outputs data in JSON format, suitable for training the neural network model or for testing either evaluator.
    *   Supports generating expressions with `AND`, `OR`, `NOT`, `true`, `false`, and parentheses, with configurable nesting depth.

2.  **`lightweight_logic_model.py`** (and `logic_parser_eval.py`):
    *   Implements the `LightweightLogicModel` class, which provides a deterministic, rule-based parser and evaluator for logical propositions.
    *   It tokenizes input strings, normalizes them to a Python-evaluable format, and uses a safe evaluation mechanism.
    *   `logic_parser_eval.py` might contain an older or alternative parser implementation, but `lightweight_logic_model.py` is the primary rule-based evaluator.
    *   **Recommended for reliable and accurate evaluation of well-formed simple expressions.**

3.  **`logic_model_nn.py`**:
    *   Implements the `LogicNNModel` class, a sequence-to-sequence (specifically, sequence-to-category) neural network using TensorFlow/Keras.
    *   Architecture: Embedding layer -> LSTM layer -> Dense output layer (softmax for True/False classification).
    *   Learns to evaluate expressions from examples; its performance depends on training data and hyperparameters.

4.  **`train_logic_model.py`**:
    *   A script to train the `LogicNNModel`.
    *   Loads training data, preprocesses it, builds the model, and runs the training loop.
    *   Saves the trained model weights and character maps.

5.  **`evaluate_logic_model.py`**:
    *   A script to evaluate a trained `LogicNNModel`.
    *   Loads a test dataset, the trained model, and character maps, then reports accuracy and other classification metrics.

6.  **`logic_tool.py`** (located in the parent `src/tools` directory):
    *   Provides a unified interface function `evaluate_expression(expression_string, method='parser')`.
    *   This function can call either the `LogicParserEval` or the trained `LogicNNModel` based on the `method` argument.
    *   It is intended to be used by the main `ToolDispatcher`.

## Setup and Usage Workflow

1.  **Data Generation**: Run `python src/tools/logic_model/logic_data_generator.py` to create training and test datasets.
2.  **NN Model Training (Optional)**: If using the neural network evaluator, run `python src/tools/logic_model/train_logic_model.py`.
3.  **NN Model Evaluation (Optional)**: After training, run `python src/tools/logic_model/evaluate_logic_model.py` to assess performance.
4.  **Using the Logic Tool**: The primary way to use this capability is through `logic_tool.py`, which can be invoked by the `ToolDispatcher` or used directly for testing.

## Parser vs. Neural Network Model

-   **Parser-based (`LogicParserEval`)**:
    *   **Pros**: Deterministic, 100% accurate for well-defined grammar, fast, no training required.
    *   **Cons**: Less flexible to input variations, does not handle ambiguity.
    *   **Recommended for**: Reliable evaluation of standard logical propositions (default method).

-   **Neural Network-based (`LogicNNModel`)**:
    *   **Pros**: Can potentially handle more varied or slightly malformed inputs (if trained on such data), can learn complex patterns.
    *   **Cons**: Requires training data, time, and resources. Performance is not guaranteed to be 100%.
    *   **Recommended for**: Experimental purposes, or if the scope of "logic" expands beyond simple Boolean expressions.

For the current scope of simple Boolean expressions, the **parser-based evaluator is generally preferred for its accuracy and simplicity.**

## Future Enhancements

-   More robust parsing in `LogicParserEval`.
-   Training the `LogicNNModel` on larger and more diverse datasets.
-   Extending supported logical operators and functions.
-   Improving error reporting for invalid expressions.

## Current Status

Tests currently show failures indicating instability in core model components. Work is ongoing to improve reliability and functionality.

## Code Location

`src/tools/logic_model/`
