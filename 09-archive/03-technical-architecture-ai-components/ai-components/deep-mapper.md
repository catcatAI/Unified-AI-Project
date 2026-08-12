# DeepMapper: Flexible Data Transformation Engine

## Overview

This document provides an overview of the `DeepMapper` module (`src/core_ai/deep_mapper/mapper.py`). This module implements a deep mapping engine capable of transforming data between different representations.

## Purpose

The `DeepMapper` provides a flexible and extensible mechanism for transforming complex data structures. This is crucial for ensuring interoperability between different AI components or external systems that may use varying data formats. It allows the AI to understand and process data regardless of its original representation, facilitating seamless data flow across the ecosystem.

## Key Responsibilities and Features

*   **Data Transformation (`map`)**: Takes a `MappableDataObject` as input and transforms its internal data structure based on a set of predefined `mapping_rules`. It performs a recursive mapping, applying rules to nested dictionaries and lists, ensuring comprehensive transformation.
*   **Reverse Mapping (`reverse_map`)**: Provides the capability to reverse the mapping process, converting data back to its original representation. This is achieved by automatically generating and applying inverted mapping rules.
*   **Rule Loading (`load_mapping_rules`)**: Allows for dynamic configuration of transformations by loading mapping rules from a JSON file. This enables easy updates and extensions to the mapping logic without code changes.
*   **Recursive Mapping Logic (`_recursive_map`)**: Implements the core logic for traversing complex data structures (dictionaries and lists) and applying the specified mapping rules at each level.
*   **Rule Inversion (`_invert_mapping_rules`)**: A utility method that automatically generates the inverse of a given set of mapping rules, which is essential for the `reverse_map` functionality.

## How it Works

The `DeepMapper` is initialized with a set of `mapping_rules`. When the `map` method is invoked, it recursively traverses the `data` attribute of the input `MappableDataObject`. For each key-value pair encountered, it checks if a corresponding rule exists in the `mapping_rules`. If a rule is found, it applies the transformation, which might involve renaming the key or recursively mapping the value. The `reverse_map` method functions similarly but uses an automatically generated inverted set of rules to revert the data to its original structure.

## Integration with Other Modules

*   **`MappableDataObject`**: The `DeepMapper` operates directly on instances of `MappableDataObject`, which serves as the standardized data container for the transformations.
*   **`json`**: Used for loading mapping rules from external JSON files.
*   **Data Ingestion/Output Modules**: Any module responsible for ingesting data from external sources or outputting data to external systems would use the `DeepMapper` to ensure data conforms to the required formats.

## Code Location

`src/core_ai/deep_mapper/mapper.py`