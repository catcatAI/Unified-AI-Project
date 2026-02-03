# MetaFormulas: The Rules Governing the Rules

## Overview

MetaFormulas represent a highly advanced and conceptual layer within the Unified-AI-Project's architecture, as outlined in the `PHILOSOPHY_AND_VISION.md`. They are not merely static rules but **dynamic principles or schemata that define how semantic modules (like Angela or Fragmenta) learn, adapt, and reorganize their own structures and narrative generation capabilities.** In essence, MetaFormulas are the "rules that govern the changing of rules," enabling the AI's self-modifying and evolving nature.

This module (`src/ai/meta_formulas/`) provides the foundational structures for implementing these high-level principles, particularly in how the AI perceives and reacts to semantic anomalies or undefined knowledge domains.

## Key Concepts and Components

1.  **`MetaFormula` (`meta_formula.py`)**:
    *   The base class for all specific MetaFormulas. It defines a common interface with a `name`, `description`, and an `execute` method.
    *   Subclasses of `MetaFormula` would implement the specific logic for how a particular meta-rule influences the AI's behavior or internal structure.

2.  **`ErrX` (`errx.py`)**:
    *   Represents a **semantic error variable**. Unlike traditional programming errors, `ErrX` signifies a conceptual or logical inconsistency, a contradiction, or a deviation from expected semantic patterns within the AI's understanding or generated narratives.
    *   The presence or detection of an `ErrX` would trigger specific MetaFormulas to initiate self-correction, re-evaluation, or learning processes.

3.  **`UndefinedField` (`undefined_field.py`)**:
    *   Represents an **unknown semantic space** or a conceptual void within the AI's knowledge graph. It signifies areas where the AI's current understanding is incomplete, ambiguous, or non-existent.
    *   The `probe` method (currently a placeholder) suggests a mechanism for the AI to actively explore and gather information about these undefined fields, potentially leading to new knowledge acquisition or the generation of novel concepts.
    *   This concept is directly tied to the AI's ability to expand its understanding and venture into new cognitive territories.

## Role in the Unified-AI-Project

MetaFormulas are crucial for the AI's long-term evolution and resilience:

-   **Self-Correction and Adaptation**: By defining how the AI reacts to `ErrX` (semantic errors), MetaFormulas enable the system to identify and resolve internal inconsistencies, leading to more robust and reliable AI behavior.
-   **Knowledge Expansion**: The concept of `UndefinedField` allows the AI to actively seek out and integrate new information, pushing the boundaries of its knowledge and understanding.
-   **Dynamic Behavior**: MetaFormulas provide a mechanism for the AI to dynamically adjust its own operational parameters, learning strategies, or even its personality based on high-level principles.
-   **Emergent Intelligence**: They are a foundational element for the emergence of more sophisticated, self-aware, and self-improving AI capabilities, as they allow the AI to modify its own learning and reasoning processes.

## Code Location

`src/ai/meta_formulas/`

-   `meta_formula.py`: Base class for MetaFormulas.
-   `errx.py`: Definition of semantic error variables.
-   `undefined_field.py`: Representation of unknown semantic spaces.
