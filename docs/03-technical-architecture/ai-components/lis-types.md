# LIS_Types: Core Data Structures for the Linguistic Immune System

## Overview

This document provides an overview of the `types.py` module (`src/core_ai/lis/types.py`). This module is dedicated to defining the core data structures and literal types used throughout the Linguistic Immune System (LIS).

## Purpose

The primary purpose of this module is to establish a clear, consistent, and type-hinted schema for representing various concepts and data flows within the LIS. This standardization is crucial for ensuring data integrity, improving code readability, and facilitating static analysis across all components that interact with the LIS. It acts as the foundational vocabulary for the entire LIS framework.

## Key Responsibilities and Features

*   **Literal Types for Controlled Vocabularies**: Defines specific string literal types to enforce controlled vocabularies for key LIS concepts:
    *   **`LIS_AnomalyType`**: A `Literal` type defining the various categories of semantic anomalies that the LIS can detect (e.g., "RHYTHM_BREAK", "LOW_DIVERSITY", "UNEXPECTED_TONE_SHIFT").
    *   **`LIS_InterventionOutcome`**: A `Literal` type specifying the possible outcomes of LIS interventions (e.g., "SUCCESS", "FAILURE").
*   **`LIS_SeverityScore`**: A type alias for `float`, used to represent the severity level of a detected anomaly, typically on a scale (e.g., 0.0 to 1.0).
*   **`LIS_SemanticAnomalyDetectedEvent`**: A `TypedDict` that structures the information related to a detected semantic anomaly event. It includes:
    *   `anomaly_type` (Required): The type of anomaly detected, using `LIS_AnomalyType`.
    *   `severity` (Required): The severity score of the anomaly, using `LIS_SeverityScore`.
    *   (Additional fields can be added as needed to provide more context about the detected anomaly).
*   **`LIS_InterventionReport`**: A `TypedDict` designed for reporting the details and outcome of an LIS intervention. It includes:
    *   `outcome` (Required): The result of the intervention, using `LIS_InterventionOutcome`.
    *   (Additional fields can be added to describe the intervention steps, reasons for success/failure, etc.).
*   **`LIS_IncidentRecord`**: A `TypedDict` representing a complete, comprehensive record of an LIS incident. It encapsulates all relevant information about a specific anomaly event and any subsequent interventions. It includes:
    *   `incident_id` (Required): A unique identifier for the incident.
    *   `anomaly_event` (Required): The `LIS_SemanticAnomalyDetectedEvent` that triggered this incident.
    *   `intervention_reports` (Optional[List[LIS_InterventionReport]]): A list of reports detailing any interventions attempted for this incident.
*   **`NarrativeAntibodyObject`**: A `TypedDict` representing a "narrative antibody," which is a learned successful response pattern or strategy developed by the LIS to address specific types of anomalies. It includes:
    *   `antibody_id` (Required): A unique identifier for the antibody.
    *   (Additional fields would define the antibody's content, target anomaly types, effectiveness score, etc.).

## How it Works

This module serves purely as a definition layer for LIS-related data structures. It does not contain any executable logic or functional implementations. Instead, other LIS components (such as the `LISCacheInterface`, `LIS_TonalRepairEngine`, or anomaly detection modules) import and utilize these `TypedDict` and `Literal` types. This ensures that all data exchanged within the LIS framework adheres to a consistent and well-defined structure, which is critical for interoperability, debugging, and future extensibility.

## Integration with Other Modules

*   **`LISCacheInterface`**: This interface (and its concrete implementations like `HAMLISCache`) heavily relies on these types for storing, retrieving, and querying `LIS_IncidentRecord`s and `NarrativeAntibodyObject`s.
*   **`LIS_TonalRepairEngine`**: Would use `LIS_AnomalyType` to understand the nature of linguistic issues it needs to repair.
*   **Anomaly Detection Modules**: Any module responsible for detecting semantic anomalies would produce `LIS_SemanticAnomalyDetectedEvent` objects.
*   **`typing`**: The standard Python library that provides the foundational `TypedDict`, `Optional`, `List`, and `Literal` constructs used for defining these types.

## Code Location

`src/core_ai/lis/types.py`