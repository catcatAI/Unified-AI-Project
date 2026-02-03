# TrustManager: Managing Trust Scores for AI Entities

## Overview

This document provides an overview of the `TrustManager` module (`src/core_ai/trust_manager/trust_manager_module.py`). This module is responsible for managing trust scores for other AI entities that interact with the system via the Heterogeneous Service Protocol (HSP).

## Purpose

The `TrustManager` enables the AI to assess the reliability and credibility of information and services received from other AIs on the network. This is crucial for maintaining the integrity of the AI's knowledge base, making informed decisions about which external services to rely on, and adapting its behavior based on the perceived trustworthiness of its peers.

## Key Responsibilities and Features

*   **Trust Score Management**: Stores and manages trust scores for each known AI entity. Scores are normalized to a range from `0.0` (completely untrusted) to `1.0` (fully trusted). A default score of `0.5` is assigned to newly encountered or unknown AIs.
*   **Capability-Specific Trust**: Supports maintaining different trust scores for an AI based on specific capabilities. For example, an AI might be highly trusted for "data_analysis" tasks but less so for "creative_writing" tasks. This allows for fine-grained trust assessment.
*   **Score Retrieval (`get_trust_score`)**: Provides a method to retrieve the trust score for a given AI ID, optionally for a specific capability. If a capability-specific score is not found, it gracefully falls back to a general trust score for that AI.
*   **Score Updates (`update_trust_score`)**: Allows for flexible updating of trust scores. Scores can be updated either by:
    *   **Adjustment**: Incrementing or decrementing the current score by a specified amount.
    *   **Absolute Value**: Setting the score to a new absolute value.
    All updates are automatically clamped within the defined `MIN_TRUST_SCORE` and `MAX_TRUST_SCORE` range to prevent scores from going out of bounds.
*   **Default Trust Score Assignment**: Automatically assigns a default trust score to newly encountered AIs, providing a neutral starting point for trust evaluation.

## How it Works

The `TrustManager` maintains an internal dictionary where keys are AI IDs and values are dictionaries containing trust scores (either a 'general' score or capability-specific scores). When the AI interacts with another AI or receives information from it, modules like the `LearningManager` or `ServiceDiscoveryModule` can use the `TrustManager` to query or update the trust score of the interacting AI. This score can then be used to influence various decisions, such as whether to store a received fact, prioritize a service from a trusted AI, or adjust the confidence in information received.

## Integration with Other Modules

*   **`LearningManager`**: A primary consumer of the `TrustManager`, using it to assess the credibility of incoming facts from other AIs before integrating them into the AI's knowledge base.
*   **`ServiceDiscoveryModule`**: Utilizes the `TrustManager` to filter or prioritize capabilities based on the trust score of the advertising AI, ensuring that the AI prefers services from more trusted sources.
*   **`HSPConnector`**: The communication layer that facilitates interactions between AIs, which then feed into the `TrustManager` for trust evaluation.

## Code Location

`src/core_ai/trust_manager/trust_manager_module.py`