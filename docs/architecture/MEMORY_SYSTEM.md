# MikoAI Memory System: Hierarchical Abstractive Memory (HAM)

## Overview

MikoAI employs a sophisticated memory architecture known as the **Hierarchical Abstractive Memory (HAM)** system. This system is designed to allow MikoAI to learn from a vast range of experiences, store them efficiently, and retrieve relevant information in a flexible manner.

The core idea behind HAM is to process and store memories at different levels of abstraction, moving from raw sensory input to compact, conceptual representations.

## Key Concepts

*   **Layered Architecture**: HAM consists of at least two main layers:
    *   **Surface Layer (SL)**: Handles raw data input (e.g., dialogue, events), performs initial processing like keyword extraction and summarization, and manages the "rehydration" of abstract memories back into usable forms.
    *   **Core Layer (CL)**: Stores highly abstracted, compressed, and (eventually) encrypted representations of experiences. This layer is optimized for long-term storage, efficient querying, and deeper pattern recognition.

*   **Abstraction & Rehydration**: Raw experiences are "abstracted" into essential "gists" before being stored in the Core Layer. When recalled, these gists are "rehydrated" by the Surface Layer to reconstruct meaningful information.

*   **Efficiency and Scalability**: By storing compact abstract representations, HAM aims to manage large volumes of memory efficiently, enabling MikoAI to learn and grow over extended periods without being overwhelmed by raw data.

*   **Foundation for Advanced Reasoning**: The abstracted representations in the Core Layer are intended to provide a basis for more complex reasoning, pattern matching, and potentially emergent understanding.

## Implementation

The HAM system is primarily implemented in the `HAMMemoryManager` class, located at `src/core_ai/memory/ham_memory_manager.py`.

## Detailed Design

For a comprehensive technical explanation of the HAM model, including data flow, API specifications, and future development plans, please refer to the detailed design document:

*   **[Hierarchical Abstractive Memory (HAM) - Design Specification](./HAM_design_spec.md)**

## Integration

The HAMMemoryManager is designed to be a central component of MikoAI's cognitive architecture. It will be used by various modules, including:

*   Dialogue engine (to remember conversations)
*   Learning and adaptation modules (to store learned behaviors and insights)
*   Tool dispatcher (to recall past tool usage or outcomes)
*   Personality and emotion modules (to link experiences with emotional states)

The prototype script `scripts/prototypes/miko_core_ham_prototype.py` demonstrates a basic integration of the HAM system.

---

This document provides a high-level overview. For technical details, please consult the linked design specification.
