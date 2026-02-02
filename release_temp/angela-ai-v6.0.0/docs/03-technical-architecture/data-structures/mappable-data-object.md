# Mappable Data Object: Flexible Data Container

## Overview

The `MappableDataObject` (`src/shared/types/mappable_data_object.py`) is a versatile and generic data container designed to hold, compress, and layer various forms of data within the Unified-AI-Project. Its primary purpose is to provide a standardized and flexible wrapper for data that needs to be processed, transformed, or stored across different AI components.

This object is crucial for managing the diverse data types encountered in a complex AI system, from raw input to processed insights, ensuring consistency and efficiency in data handling.

## Key Responsibilities and Features

1.  **Generic Data Container**: 
    *   Can encapsulate any type of `data` (e.g., strings, dictionaries, lists, custom objects).
    *   Includes an optional `metadata` dictionary for storing additional contextual information about the data.

2.  **Data Compression (`compress`, `decompress`)**: 
    *   Utilizes the `zlib` library to perform lossless compression and decompression of the encapsulated data.
    *   This is vital for optimizing storage space and reducing network bandwidth when transmitting large data objects within or between AI instances.

3.  **Layered Data Management (`add_layer`, `get_layer`)**: 
    *   Supports the concept of "layers," allowing different aspects or transformations of the data to be stored and accessed within the same `MappableDataObject`.
    *   Each layer is identified by a `layer_name` (string) and can hold any type of `layer_data`.
    *   This enables a modular approach to data processing, where different AI modules can add their processed outputs as new layers to the original data object.

## How it Works

An instance of `MappableDataObject` is created with initial `data` and optional `metadata`. The `compress` method serializes the `data` to a JSON string, encodes it to bytes, and then compresses it using `zlib`, storing the result in `compressed_data`. The `decompress` method reverses this process. The `add_layer` and `get_layer` methods provide a simple dictionary-like interface for managing named data layers, allowing for progressive enrichment or transformation of the data within a single object.

## Integration and Importance

-   **`DeepMapper`**: The `DeepMapper` is designed to operate on `MappableDataObject` instances, transforming their internal `data` structure based on predefined rules.
-   **`HAMMemoryManager`**: Could potentially store `MappableDataObject` instances, leveraging their compression capabilities and layered structure for efficient memory management.
-   **Inter-Module Communication**: Provides a standardized format for passing complex data between different AI modules, ensuring that each module can access the relevant information and contribute its processing results as new layers.
-   **Data Pipeline Management**: Facilitates the creation of data processing pipelines where each stage adds a new layer of information or transformation to the `MappableDataObject`.

## Code Location

`src/shared/types/mappable_data_object.py`
