# Unified Model Loader

## Overview

This document provides an overview of the `UnifiedModelLoader` module (`src/data/models/unified_model_loader.py`). This module serves as a centralized, robust loader for various machine learning models used within the AI system, such as the arithmetic and logic models.

## Purpose

The primary purpose of this module is to provide a single, reliable interface for loading ML models. It abstracts away the complexities of file paths, dependency checking, and error handling. By ensuring that models are loaded only once (lazy loading) and that failures are handled gracefully, it improves the overall stability and efficiency of the application.

## Key Responsibilities and Features

*   **Centralized Loading**: Provides specific functions (`load_math_model`, `load_logic_nn_model`) to load different neural network models from the `data/models/` directory.
*   **Lazy Loading and Caching**: Models are loaded only on the first request. Once loaded, the instance is cached in a global dictionary (`_loaded_models`), and subsequent calls return the cached instance, preventing redundant and time-consuming loading operations.
*   **Robust Error Handling**: Each model loading function is wrapped in a comprehensive `try...except` block to handle potential failures:
    *   **`ImportError`**: Catches errors if a required library (e.g., TensorFlow) is not installed, preventing the entire application from crashing.
    *   **`FileNotFoundError`**: Handles cases where the model's weights or configuration files are missing.
    *   **Other Exceptions**: Catches any other unexpected errors during model instantiation.
*   **Error Reporting**: When a model fails to load, the error is logged, and the exception message is stored in a global `_model_load_errors` dictionary. Other parts of the system can then query this dictionary using `get_model_load_error()` to check the status of a model and respond accordingly (e.g., by disabling the feature that requires the model).

## How it Works

The module maintains two global dictionaries: `_loaded_models` to store successfully loaded model instances and `_model_load_errors` to record any errors that occurred during loading. When a function like `load_math_model()` is called, it first checks these dictionaries. If the model is already in `_loaded_models`, it's returned immediately. If it's in `_model_load_errors`, it returns `None`. If the model is not in either dictionary, the function proceeds to load the model from its specified file path. If the load is successful, the instance is stored in `_loaded_models`. If it fails, the error is stored in `_model_load_errors`.

## Integration with Other Modules

*   **Model Classes (`ArithmeticSeq2Seq`, `LogicNNModel`)**: The loader imports and instantiates these specific model classes.
*   **Tool Modules (`math_tool.py`, `logic_tool.py`)**: These are the primary consumers of the loader. They call the loading functions to get the model instances they need to operate.

## Code Location

`apps/backend/src/data/models/unified_model_loader.py`