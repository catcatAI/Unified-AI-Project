# Learning Manager

## Overview

The `LearningManager` (`src/core_ai/learning/learning_manager.py`) is a pivotal component within the Unified-AI-Project's cognitive architecture. It is responsible for enabling the AI (Angela) to acquire, process, and integrate new knowledge and strategies from various sources, including user interactions and the Heterogeneous Service Protocol (HSP) network.

Its core function is to manage the AI's continuous learning loop, ensuring that new information is not only stored but also evaluated for quality, relevance, and potential conflicts before being integrated into Angela's long-term memory.

## Key Responsibilities and Features

1.  **Fact Extraction and Storage (`process_and_store_learnables`)**:
    *   Extracts structured "facts" from raw text inputs (e.g., user utterances) using the `FactExtractorModule`.
    *   Evaluates the confidence score of extracted facts against a configurable `min_fact_confidence_to_store` threshold.
    *   Stores validated facts into the `HAMMemoryManager` (Hierarchical Abstractive Memory) for long-term retention.
    *   Optionally publishes high-confidence, user-derived facts to the HSP network for sharing with other AI instances.

2.  **Quality-Based Fact Integration from HSP (`process_and_store_hsp_fact`)**:
    *   This is a critical mechanism designed to prevent "idiot resonance" – the propagation and storage of low-quality or conflicting information from external sources.
    *   **Duplicate Checking**: Identifies and handles duplicate facts to avoid redundancy and reinforce existing knowledge.
    *   **Source Credibility Assessment**: Incorporates trust scores from the `TrustManager` to weigh the confidence of incoming facts based on the sender AI's historical reliability.
    *   **Novelty & Evidence Assessment (Simplified)**: Performs basic checks for novelty and supporting evidence to prioritize valuable information.
    *   **Conflict Resolution**: Implements logic to resolve conflicts between new and existing facts, potentially superseding older, less confident information or logging contradictions for further analysis.
    *   Only facts that pass a `min_hsp_fact_confidence_to_store` threshold (derived from effective confidence, novelty, and evidence) are stored in HAM.

3.  **Learning from Project Cases (`learn_from_project_case`)**:
    *   Analyzes completed project execution cases (e.g., from `ProjectCoordinator`'s successful task completions).
    *   Stores the raw project case in HAM for auditing and future analysis.
    *   **Strategy Distillation**: Utilizes an LLM (via `FactExtractor.llm`) to distill reusable collaboration strategies from successful project cases. These distilled strategies are then stored in HAM, allowing Angela to learn and generalize from her experiences.

4.  **Personality Adjustment (`analyze_for_personality_adjustment`)**:
    *   Provides a simplified interface for analyzing text to identify potential personality adjustments. This allows Angela's personality to subtly evolve based on interactions.

## Integration with Other Modules

-   **`HAMMemoryManager`**: The primary storage for all learned facts and strategies.
-   **`FactExtractorModule`**: Used to extract structured facts from raw text.
-   **`TrustManager`**: Provides trust scores for assessing the credibility of information sources, particularly for HSP-derived facts.
-   **`ContentAnalyzerModule`**: (Optional) Can be used for deeper analysis of fact content, contributing to novelty and evidence scores.
-   **`HSPConnector`**: Facilitates the exchange of facts and knowledge with other AI instances over the HSP network.
-   **`PersonalityManager`**: Receives personality adjustment suggestions from the `LearningManager`.

## Configuration

Key learning thresholds and default HSP topics are configurable via the `operational_config` passed during initialization:

```yaml
operational_configs:
  learning_thresholds:
    min_fact_confidence_to_store: 0.7
    min_fact_confidence_to_share_via_hsp: 0.8
    min_hsp_fact_conflict_confidence_delta: 0.05
  default_hsp_fact_topic: "hsp/knowledge/facts/general"
```

## Future Considerations

-   **Advanced Novelty and Evidence Assessment**: Implementing more sophisticated algorithms for determining the novelty and evidential support of incoming information.
-   **Complex Conflict Resolution**: Developing more nuanced strategies for handling contradictions and inconsistencies in the knowledge base.
-   **Active Learning**: Enabling the `LearningManager` to actively seek out information or perform experiments to resolve uncertainties or fill knowledge gaps.

## Code Location

`src/core_ai/learning/learning_manager.py`
