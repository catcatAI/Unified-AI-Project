# Design Proposal: Alpha-Deep-Model (ɑ深層模型) - V3

## 1. Overview

This document outlines the design for a new, specialized model temporarily named the **Alpha-Deep-Model (ɑ深層模型)**. This proposal is in response to the request to create a CPU-efficient model for handling "deep parameters" that possess a multi-dimensional structure.

This model is a concrete implementation step towards the conceptual goals of **Deep Mapping** outlined in the existing [Deep Mapping and Personality Simulation](deep-mapping-personality.md) document.

**V3 Update:** This version incorporates the critical finding that the **`HAMMemoryManager` itself serves as the "Deep Mapping Model"**.

## 2. Position in Architecture

The Alpha-Deep-Model functions as a final compression stage in the memory processing pipeline. The refined understanding of this flow is as follows:

1.  **Parameter Extractor (`FactExtractorModule`)**: An existing component that extracts a structured list of "facts" from raw text.
2.  **Deep Mapping Model (`HAMMemoryManager`)**: The `HAMMemoryManager` takes the output from the `FactExtractorModule` (or other raw data) and, within its `store_experience` method, performs the "deep mapping". This is primarily achieved through the `_abstract_text` function, which creates a structured "gist" of the data. This process is "personality-based" as the retention of these memories is governed by the `PersonalityManager`.
3.  **Alpha-Deep-Model (This Proposal)**: This model's role is to take the "gist" or "deep parameter" object produced by HAM and perform a final, advanced **high-compression** step, creating a compact representation for efficient storage or transmission.

## 3. Core Function and Design Philosophy

*   **Core Function**: To perform **multi-modal, high-compression** on the structured "gist" objects produced by the `HAMMemoryManager`. The goal is to create a final, highly compact representation of complex states and relationships.
*   **CPU Efficiency**: CPU optimization is a primary requirement and will be considered from the start of development.
*   **Extending Existing Systems**: The model should be designed to integrate smoothly with the existing `HAMMemoryManager` pipeline.

## 4. Proposed Structure for Input ("Deep Parameters" / HAM "Gist")

The `HAMMemoryManager._abstract_text` method already produces a structured dictionary ("gist"). The `Alpha-Deep-Model` should be designed to work with this format. The user's request for a richer, "three-dimensional" structure can be seen as an *extension* of the existing gist.

**Current HAM Gist Structure:**
```json
{
    "summary": "First sentence of the text.",
    "keywords": ["list", "of", "keywords"],
    "original_length": 123,
    "radicals_placeholder": null,
    "pos_tags_placeholder": [{"keyword1": "NOUN_placeholder"}]
}
```

**Proposed Extended "Deep Parameter" (Input to Alpha-Deep-Model):**
This extended structure could be produced by a new abstraction module or an enhanced `_abstract_text` function. It incorporates the relational context the user described.

```json
{
  "source_memory_id": "mem_000123",
  "timestamp": "2025-08-04T03:30:00Z",
  "base_gist": {
      "summary": "My name is Sarah, and my favorite color is green.",
      "keywords": ["sarah", "favorite", "color", "green"],
      "original_length": 45
  },
  "relational_context": {
      "entities": ["Sarah", "color"],
      "relationships": [
        {"subject": "Sarah", "verb": "has_favorite_color", "object": "green", "confidence": 0.98}
      ]
  },
  "modalities": {
      "text_confidence": 1.0,
      "audio_features": null,
      "image_features": null
  }
}
```

## 5. Status of Questions and Next Steps

This section tracks the questions from the previous proposals and adds new ones based on the latest findings.

### 5.1. Answered Questions

*   **Model's Core Function?**
    *   **Answered:** Multi-modal, high-compression of deep parameters.
*   **Parameter Extractor's Identity?**
    *   **Answered:** The existing `FactExtractorModule`.
*   **Deep Mapping Model's Identity?**
    *   **Answered:** The existing `HAMMemoryManager` and its internal data abstraction processes.
*   **Approach to CPU Optimization?**
    *   **Answered:** Core consideration from the start, using existing tech where possible.

### 5.2. Open Questions for Clarification

1.  **Integration Point**: How should the **Alpha-Deep-Model** be integrated into the `HAMMemoryManager` pipeline?
    *   **Option A:** As a new step *inside* the `store_experience` method, right after `_abstract_text`, before compression and encryption?
    *   **Option B:** As a separate utility that can be called on demand to further compress memories that are already stored in HAM?
    *   **Option C:** As a replacement/upgrade for the existing `zlib` compression?

2.  **Multi-Modal Input**: The `FactExtractorModule` and `_abstract_text` are text-focused. How should we handle other modalities? Is there an existing component that extracts features from images or audio that would feed into this pipeline?

3.  **Compression Target**: What is the desired output format of the Alpha-Deep-Model's compression?
    *   A dense vector (like an embedding)?
    *   A structured binary format (like MessagePack or Protobuf)?
    *   A quantized and pruned set of numerical parameters?

4.  **"Unfinished" Components**: You mentioned both the `FactExtractorModule` and the "Deep Mapping Model" (`HAMMemoryManager`) need to be "perfected and adjusted". What are the highest priority improvements needed for these components to enable the development of the Alpha-Deep-Model?

Thank you for reviewing this V3 proposal. Your feedback on these more targeted questions will allow us to finalize the design and begin planning the implementation.
