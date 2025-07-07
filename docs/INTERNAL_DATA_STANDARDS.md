# Internal Data Standards for Unified-AI-Project

## 1. Introduction

This document outlines the conventions and standards for defining and using data structures for information exchanged *internally* between modules, classes, and major functions within the Unified-AI-Project. Adherence to these standards aims to improve:

*   **Clarity:** Making it easier to understand what data is expected and returned by different parts of the system.
*   **Predictability:** Reducing ambiguity in data handling.
*   **Maintainability:** Ensuring that changes in one module have a well-defined impact on others through clear data contracts.
*   **Testability:** Simplifying the creation of mock data and assertions in unit and integration tests.
*   **Developer Onboarding:** Helping new developers grasp inter-module interactions more quickly.

These standards apply to data passed within a single AI instance's modules. They are distinct from the Heterogeneous Synchronization Protocol (HSP), which defines data structures and protocols for communication *between different AI instances*.

## 2. Primary Mechanism: `TypedDict`

The primary mechanism for defining structured data objects for internal exchange shall be Python's `typing.TypedDict`.

*   **Usage:** `TypedDict` should be used whenever a dictionary with a known set of string keys and value types is passed as a parameter, returned from a function, or used as a significant internal data structure that flows between components.
*   **Benefits:**
    *   Provides static type checking capabilities, helping to catch errors related to incorrect dictionary keys or value types during development (with tools like MyPy).
    *   Serves as clear documentation for the expected shape of data.
    *   Offers better readability compared to using generic `Dict[str, Any]`.

## 3. Naming Conventions

*   **`TypedDict` Names:** Use PascalCase (e.g., `UserProfileData`, `HSPTaskResultInternal`).
*   **Field Names (Keys):** Use snake_case (e.g., `user_id`, `confidence_score`).

## 4. Location of Type Definitions

*   **Shared Types:** `TypedDict` definitions that are used by more than one primary module or subsystem (e.g., across `core_ai`, `services`, `tools`) should be defined in `src/shared/types/common_types.py`. This promotes reusability and provides a central place for common data structures.
*   **Module-Specific Types:** If a `TypedDict` is highly specific to a single module and not expected to be used externally, it can be defined within that module's `.py` file or a dedicated `types.py` file within that module's directory (e.g., `src/core_ai/dialogue/dialogue_types.py`). Prefer adding to `common_types.py` if there's a reasonable chance of broader future use.

## 5. Clarity, Documentation, and Examples

*   **Docstrings:** Complex `TypedDicts` or those whose fields are not self-explanatory should have a docstring explaining their purpose and the meaning of their fields.
    ```python
    from typing import TypedDict, Optional

    class ProcessedTextOutput(TypedDict):
        """
        Represents the output after text has been processed
        by the ContentAnalyzerModule.
        """
        original_text: str
        cleaned_text: str
        entities: list[dict] # Consider defining a KGEntity TypedDict too
        sentiment_score: Optional[float]
    ```
*   **Examples:** For very complex structures, providing an example instantiation in a docstring or in this standards document can be beneficial.

## 6. Usage in Type Hinting

*   All methods and functions that accept or return structured dictionary-like data should use the relevant `TypedDict` definitions in their type hints for parameters and return values.
    ```python
    from .types import UserProfileData # Assuming types.py in the same module

    def get_user_greeting(profile: UserProfileData) -> str:
        if profile.get("display_name"):
            return f"Hello, {profile['display_name']}!"
        return "Hello there!"
    ```

## 7. Alternatives (Future Considerations)

*   **Pydantic:** For scenarios requiring runtime data validation, coercion, serialization/deserialization features, or more complex data model definitions (e.g., with custom validators, computed fields), Pydantic is a strong candidate.
*   **Current Standard:** While Pydantic offers more features, `TypedDict` is the current standard for its lightweight nature, static analysis benefits, and sufficiency for many internal data exchange needs. A transition to Pydantic can be considered on a case-by-case basis if the benefits outweigh the added dependency and complexity for a specific component.
*   **Pydantic for API Models:** It is noted that Pydantic is used in `src/services/api_models.py` for defining data structures for external API request/response validation. This is a common and appropriate use of Pydantic for data validation and serialization at API boundaries, and is distinct from the `TypedDict` standard for internal data exchange between Python modules.

## 8. Scope and Distinction from HSP

*   **Internal Focus:** These standards are for data objects passed *within* the Unified-AI-Project's codebase for a single AI instance.
*   **HSP:** The Heterogeneous Synchronization Protocol (`src/hsp/types.py` and `docs/HSP_SPECIFICATION.md`) defines data structures and protocols for communication *between separate AI instances* over a network. While some HSP payload structures might inform or be used internally, their primary definition is for inter-AI interoperability. Internal representations may sometimes be simpler or more tailored to the AI's internal logic.

By adhering to these standards, we aim to create a more robust, understandable, and maintainable codebase.

## 9. Ongoing Diligence

These standards should be applied to all new Python code involving structured data exchange between modules. Existing code should be refactored to adhere to these standards opportunistically or during planned refactoring efforts for specific components. Regular review of `src/shared/types/common_types.py` for consolidation and clarity is also encouraged.
