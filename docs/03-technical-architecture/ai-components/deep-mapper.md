# Deep Mapper: Data Transformation Engine

## Overview

The `DeepMapper` (`src/core_ai/deep_mapper/mapper.py`) is a crucial component within the Unified-AI-Project responsible for **transforming data between different internal representations**. In a complex AI system that processes information from various sources and maintains diverse internal models, the ability to seamlessly map data from one structure to another is paramount.

This module enables the AI to:

-   **Standardize Data**: Convert incoming data into a consistent internal format.
-   **Adapt to Different Models**: Transform data to suit the input requirements of various AI models or modules.
-   **Maintain Flexibility**: Allow for changes in data schemas without requiring extensive refactoring across the entire codebase.

## Key Responsibilities and Features

1.  **Data Mapping (`map`)**:
    *   Takes a `MappableDataObject` (which contains the data and its metadata) and applies a set of predefined mapping rules to transform its internal structure.
    *   Performs a recursive mapping, traversing through nested dictionaries and lists to apply rules at all levels.

2.  **Reverse Mapping (`reverse_map`)**:
    *   Allows for the inverse transformation, converting data from a mapped representation back to its original structure.
    *   This is crucial for maintaining data integrity and for debugging or auditing purposes.

3.  **Loading Mapping Rules (`load_mapping_rules`)**:
    *   Enables the `DeepMapper` to load its transformation rules from an external JSON file.
    *   This external configuration makes the mapping process flexible and easily updatable without code changes.

4.  **Recursive Transformation Logic (`_recursive_map`, `_invert_mapping_rules`)**:
    *   The core of the mapping functionality lies in its recursive methods that can handle complex, nested data structures.
    *   `_invert_mapping_rules` dynamically generates the reverse mapping rules from the forward rules, ensuring consistency.

## How it Works

The `DeepMapper` operates based on a set of configurable mapping rules. These rules define how keys and values in a source data structure should be transformed into a target structure. When the `map` method is called, it recursively applies these rules to the input data. The `reverse_map` method leverages an inverted set of these rules to perform the transformation in the opposite direction.

## Integration and Importance

The `DeepMapper` is a utility that can be integrated with various parts of the AI system where data format consistency or transformation is required. Its importance lies in:

-   **Interoperability**: Facilitating seamless data exchange between modules that might operate on different data representations.
-   **Data Normalization**: Ensuring that data conforms to expected standards before being processed by specific AI models or algorithms.
-   **Flexibility in Data Evolution**: Allowing the project to evolve its internal data schemas more easily, as transformations can be managed centrally through mapping rules.

## Code Location

`src/core_ai/deep_mapper/mapper.py`
