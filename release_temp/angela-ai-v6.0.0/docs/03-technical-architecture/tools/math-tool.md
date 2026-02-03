# MathTool: Arithmetic Calculation from Natural Language

## Overview

This document provides an overview of the `math_tool.py` module (`src/tools/math_tool.py`). Its primary function is to provide the AI with the capability to perform arithmetic calculations based on natural language queries.

This tool is a fundamental component of the AI's quantitative reasoning abilities, enabling it to answer user questions that involve mathematical operations.

## Key Responsibilities and Features

*   **Natural Language Understanding**: Utilizes the `extract_arithmetic_problem` helper function to parse natural language queries (e.g., "what is 10 plus 5?") and extract the core arithmetic expression (e.g., "10 + 5"). This allows the tool to handle a variety of user inputs.
*   **Neural Network-Based Calculation**: Relies on a pre-trained sequence-to-sequence model (`ArithmeticSeq2Seq`) to predict the answer to the extracted arithmetic problem. This approach allows the tool to potentially handle more complex or varied problem formats in the future as the model is improved.
*   **Lazy Loading**: The `ArithmeticSeq2Seq` model is loaded only when the `calculate` function is first called. This lazy loading strategy improves the application's startup performance by deferring the loading of model weights until they are actually needed.
*   **Robust Dependency Management**: Gracefully handles the absence of the TensorFlow library by catching `ImportError`. If TensorFlow is not installed or the model files are missing, the tool will return an informative error message instead of crashing the application.
*   **Standardized Response Format**: Returns a `ToolDispatcherResponse` object, which provides a consistent and structured format for both successful results and error states. This simplifies the process of handling the tool's output for the calling component (e.g., the `ToolDispatcher`).

## How it Works

When the `calculate` function is invoked with a natural language query, it first calls `extract_arithmetic_problem` to identify and normalize the arithmetic expression within the text. If a valid problem is found, the function proceeds to load the pre-trained `ArithmeticSeq2Seq` model (if it hasn't been loaded already). This model then takes the extracted problem string as input and predicts the numerical answer. Finally, the result is packaged into a `ToolDispatcherResponse` object and returned.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool is designed to be invoked by the `ToolDispatcher` when the AI's intent is to perform a calculation. The `ToolDispatcher` passes the user's query to this tool for processing.
*   **`ArithmeticSeq2Seq`**: The underlying sequence-to-sequence model, located in `src.tools.math_model.model`, that performs the actual calculation.
*   **`ToolDispatcherResponse`**: The standardized response format defined in `src.shared.types.common_types` that is used to return the result of the calculation.

## Code Location

`src/tools/math_tool.py`