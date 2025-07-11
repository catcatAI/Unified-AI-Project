# Actuarion Module: Implementation Plan

**Version:** 0.1
**Date:** July 11, 2024
**Authors:** Jules (AI Agent)

## 1. Objective

This document outlines the implementation plan for the **Actuarion Module**. The primary objective is to develop a dedicated component within the Unified-AI-Project responsible for the systematic evaluation of AI-generated or processed content. The Actuarion Module will assess semantic risk, logical integrity, factual accuracy (where feasible), and overall coherence, aiming to significantly enhance the reliability, trustworthiness, and safety of the AI's outputs. This plan expands upon the concepts introduced in `docs/architecture/blueprints/Actuarion_Module_concept.md`.

## 2. Core Functionalities

The Actuarion Module will provide the following core functionalities:

1.  **Semantic Risk Assessment:**
    *   Identify potentially harmful content (e.g., hate speech, toxicity, unsafe advice) based on predefined policies and/or learned models.
    *   Detect ambiguities or statements prone to misinterpretation.
    *   Assess the evidential support or confidence level for factual claims made in the content.
2.  **Logical Coherence & Fallacy Detection:**
    *   Analyze text for internal contradictions or inconsistencies in reasoning.
    *   Identify common logical fallacies (e.g., ad hominem, straw man, false dichotomy) using rule-based and potentially model-based approaches.
3.  **Factual Accuracy Verification (Conceptual & Iterative):**
    *   Interface with `ContextCore` or other trusted knowledge sources (e.g., curated databases, specific APIs) to verify verifiable factual claims.
    *   *Note: Full, open-domain fact-checking is an extremely complex AI problem. Initial versions will focus on claims verifiable against internal knowledge or specific, reliable external sources.*
4.  **Narrative Consistency Analysis:**
    *   For narrative content, assess consistency with established lore, character profiles (if available in `ContextCore`), and plot plausibility based on defined rules or contextual history.
5.  **Code & Structured Data Validation (Basic):**
    *   For AI-generated code snippets: Basic validation via linters or syntax checkers. (Deep semantic code correctness is out of initial scope).
    *   For structured data outputs (e.g., JSON): Validate against predefined JSON Schemas.
6.  **Confidence Scoring & Explainable Reporting:**
    *   Generate a comprehensive `ValidationReport` detailing findings.
    *   Assign severity levels and confidence scores to detected issues.
    *   Provide explanations or justifications for flagged issues where possible, to aid developers or other AI modules in understanding the assessment.
7.  **Policy-Based Validation:**
    *   Allow different validation policies (sets of rules and active assessors) to be applied based on content type, user context, or specific task requirements.

## 3. Proposed New Modules/Classes

Target location: `src/core_ai/validation/actuarion/` (or `src/services/actuarion_service/` if designed as a more independent service).

*   `manager.py`:
    *   `ActuarionManager`: Main public interface. Receives validation requests, orchestrates assessors, and compiles reports.
*   `assessors/`: Directory for different assessment components.
    *   `base_assessor.py`: `BaseAssessor` (ABC for all assessors).
    *   `risk_assessors.py`:
        *   `HarmfulContentAssessor(BaseAssessor)`: Uses models/rules for toxicity, etc.
        *   `MisinformationPatternAssessor(BaseAssessor)`: Looks for common misinformation patterns.
    *   `logic_validators.py`:
        *   `LogicalCoherenceValidator(BaseAssessor)`: Checks for internal contradictions.
        *   `FallacyDetector(BaseAssessor)`: Uses rule-based patterns for common fallacies.
    *   `fact_checker.py`:
        *   `FactVerificationAgent(BaseAssessor)`: (Initially simple) Queries `ContextCore` or predefined trusted sources.
    *   `narrative_analyzers.py`:
        *   `NarrativeConsistencyAnalyzer(BaseAssessor)`: Checks against lore/character data from `ContextCore`.
    *   `structured_data_validators.py`:
        *   `SchemaValidator(BaseAssessor)`: Validates JSON against a schema.
        *   `CodeLinterAssessor(BaseAssessor)`: Interfaces with a linter.
*   `rules_engine.py`:
    *   `ValidationRuleEngine`: Loads and applies configurable validation rules.
*   `models.py` (for data structures):
    *   Defines `ValidationInput`, `ValidationIssue`, `ValidationReport`, `ValidationPolicy`, `ValidationRule` (`TypedDict`s or Pydantic models).
*   `report_builder.py`:
    *   `ValidationReportBuilder`: Aggregates issues from assessors and formats the final report.

## 4. Data Structures (`TypedDict` Examples)

```python
from typing import TypedDict, List, Dict, Any, Optional, Literal

class ValidationContent(TypedDict):
    text_content: Optional[str]
    structured_data: Optional[Dict] # For JSON
    code_snippet: Optional[str]
    # Potentially other modalities in the future

class ValidationContext(TypedDict):
    user_id: Optional[str]
    session_id: Optional[str]
    task_type: Optional[str] # e.g., "dialogue_response", "code_generation"
    source_module: Optional[str] # Module that generated the content

class ValidationInput(TypedDict):
    content_id: str # ID for the content being validated
    content_data: ValidationContent
    content_type: Literal["text", "json", "python_code", "narrative"]
    context: ValidationContext
    policy_ids: Optional[List[str]] # Specific validation policies to apply

class ValidationIssue(TypedDict):
    issue_id: str
    assessor_id: str # Which assessor raised this
    rule_id: Optional[str] # If rule-based
    issue_type: str # e.g., "LogicalFallacy", "HarmfulContent", "FactualError"
    severity: Literal["info", "warning", "error", "critical"]
    confidence: float # Assessor's confidence in this issue (0.0-1.0)
    location_start: Optional[int] # Character offset or line number
    location_end: Optional[int]
    description: str # Human-readable description
    explanation: Optional[str] # Why this was flagged
    suggested_fix: Optional[str]

class ValidationReport(TypedDict):
    report_id: str
    content_id: str
    overall_assessment: Literal["pass", "pass_with_warnings", "fail"]
    overall_confidence: float
    risk_score: Optional[float] # Aggregate risk score
    issues: List[ValidationIssue]
    summary: str
    timestamp: float

class ValidationRule(TypedDict):
    rule_id: str
    description: str
    conditions: List[Dict] # e.g., regex patterns, keyword lists, logical conditions
    issue_type_to_raise: str
    default_severity: Literal["info", "warning", "error", "critical"]

class ValidationPolicy(TypedDict):
    policy_id: str
    description: str
    active_assessors: List[str] # IDs of assessors to run
    active_rule_sets: List[str] # IDs of rule sets to apply
    thresholds: Optional[Dict[str, float]] # e.g., risk_score_threshold
```

## 5. API Definitions (Conceptual Methods for `ActuarionManager`)

*   `async def validate_content(self, validation_input: ValidationInput) -> ValidationReport:`
    *   The primary method. Selects assessors based on `policy_ids` or defaults.
    *   Runs selected assessors on the `content_data`.
    *   Aggregates results into a `ValidationReport`.
*   `async def load_policy(self, policy_id: str) -> Optional[ValidationPolicy]:`
*   `async def load_ruleset(self, ruleset_id: str) -> Optional[List[ValidationRule]]:`

## 6. Core Logic/Algorithms

*   **Policy-Driven Assessment:** `ActuarionManager` loads the specified (or default) `ValidationPolicy`. This policy dictates which assessors and rule sets are active for a given request.
*   **Assessor Execution:** Each active assessor processes the `ValidationContent`.
    *   **Rule-Based Assessors:** Use the `ValidationRuleEngine` to match rules against the content.
    *   **Model-Based Assessors:** Make calls to internal/external ML models (e.g., a toxicity classifier LLM via `LLMInterface` or a specific Tech Block). Results are interpreted to identify issues.
    *   **Knowledge-Based Assessors (e.g., `FactVerificationAgent`):** Formulate queries to `ContextCoreManager` based on claims in the content. Compare results to assess accuracy.
*   **Issue Aggregation (`ValidationReportBuilder`):**
    *   Collects all `ValidationIssue`s from all assessors.
    *   Calculates an `overall_assessment` based on the severity and number of issues, and configured thresholds.
    *   May compute an aggregate `risk_score`.
*   **Explainability:** Assessors should be designed to provide evidence or reasoning for their findings where possible (e.g., which rule was triggered, which part of the text matched a harmful pattern).

## 7. Integration Points & Refactoring Plan

*   **`DialogueManager` (`src/core_ai/dialogue/dialogue_manager.py`):**
    *   **Pre-Response Validation:** Before finalizing a response to the user, `DialogueManager` can send the draft response to `ActuarionManager.validate_content()`.
    *   **Handling Reports:** If `ValidationReport.overall_assessment` is "fail" or "pass_with_warnings", `DialogueManager` might:
        *   Attempt to regenerate/revise the response.
        *   Add a disclaimer to the response.
        *   Log the issue for review.
        *   Consult `ContextCore` for user preferences on content sensitivity.
*   **`LearningManager` (`src/core_ai/learning/`):**
    *   Validation reports from Actuarion can be fed into the `SelfCritiqueModule` to improve its evaluation of AI performance.
    *   Persistent issues flagged by Actuarion can inform `LearningManager` about areas needing targeted learning or model refinement.
*   **`FragmentaOrchestrator` / Future Bus System:**
    *   Actuarion validation can be a standard step in complex task pipelines managed by Fragmenta.
    *   If the Bus System is implemented, Actuarion itself could be a high-level Module, and its individual assessors (`HarmfulContentAssessor`, etc.) could be Tech Blocks. This would allow dynamic assembly of validation pipelines.
*   **Content Generation Capabilities (e.g., Tool-generated content, Summarizers):**
    *   Any module or tool that generates substantial textual or structured output should have a hook to send its output to Actuarion for validation, especially if the content is user-facing or will be stored long-term.
*   **`ContextCoreManager` (`src/core_ai/memory/context_core/manager.py`):**
    *   Actuarion will be a major consumer of information from ContextCore, using it to:
        *   Retrieve factual knowledge for verification.
        *   Access established lore or character profiles for narrative consistency checks.
        *   Load user-specific or global safety/content policies.
*   **`LLMInterface` (or equivalent Tech Blocks):**
    *   Some assessors within Actuarion (e.g., for detecting nuanced harmful content or scoring coherence) might themselves use LLMs. They would call the standard `LLMInterface`.

## 8. Configuration (`configs/`)

*   `configs/validation/actuarion_config.yaml`:
    *   `default_policy_id: str`
    *   `log_level: str`
    *   `enable_expensive_checks_default: bool`
*   `configs/validation/policies/`: Directory for `ValidationPolicy` YAML/JSON files.
    *   Example: `default_dialogue_policy.yaml`, `strict_safety_policy.yaml`.
*   `configs/validation/rules/`: Directory for `ValidationRule` set YAML/JSON files.
    *   Example: `common_logical_fallacies.yaml`, `harmful_content_keywords.yaml`.
*   `configs/validation/model_config/`: If Actuarion uses its own ML models (not just via `LLMInterface`).
    *   Endpoints, model paths, specific API keys for validation services.

## 9. Basic Test Cases

*   Test `HarmfulContentAssessor` correctly flags toxic text and passes safe text.
*   Test `FallacyDetector` identifies specific fallacies in example arguments.
*   Test `LogicalCoherenceValidator` detects contradictions in a simple story.
*   Test `FactVerificationAgent` correctly verifies/denies facts against a mock `ContextCore`.
*   Test `SchemaValidator` for JSON content.
*   Test `ActuarionManager` applying different policies and producing correct `ValidationReport`s.
*   Test integration with `DialogueManager`: ensure a response flagged as "critical" by Actuarion is not sent to the user directly.

## 10. Potential Challenges & Mitigation

*   **Defining "Truth," "Risk," "Harm":** These are complex and often subjective.
    *   **Mitigation:** Start with clear, narrowly defined rules and patterns. Rely on configurable policies that can be adapted. Use multiple assessors for consensus. Allow human oversight for edge cases.
*   **False Positives/Negatives:** Overly strict validation can stifle creativity; overly lax validation misses issues.
    *   **Mitigation:** Iterative development and tuning of rules and models. Use confidence scores from assessors. Implement a feedback loop for human correction of Actuarion's mistakes.
*   **Performance Overhead:** Deep validation can be slow.
    *   **Mitigation:** Make validation steps configurable per policy (e.g., full validation for critical outputs, lighter checks for internal logs). Asynchronous validation where possible. Optimize critical assessors. Cache validation results for identical content if appropriate.
*   **Explainability of Judgments:** Understanding *why* Actuarion flagged something.
    *   **Mitigation:** Design assessors to return not just a flag but also evidence (e.g., the rule triggered, the problematic keywords). For model-based assessors, explore techniques like LIME/SHAP if feasible, or use LLMs to generate explanations for their own judgments.
*   **Maintaining Rules & Models:** Rulesets and ML models for detection can become outdated.
    *   **Mitigation:** Establish a process for regularly reviewing and updating rules. Plan for retraining/fine-tuning ML models as new data and threat patterns emerge.
*   **Contextual Nuance:** The risk/appropriateness of content heavily depends on context.
    *   **Mitigation:** Ensure `ValidationInput` includes rich `ValidationContext`. Design assessors to leverage this context (e.g., user history from `ContextCore`, task type).

## 11. Phased Implementation (High-Level)

1.  **Phase 1: Core Framework & Rule-Based Assessors.**
    *   Implement `ActuarionManager`, data models (`ValidationInput`, `Report`, etc.), `ValidationRuleEngine`.
    *   Develop initial rule-based assessors for basic harmful content (keyword-based) and simple logical fallacies.
    *   Basic integration with `DialogueManager` for optional pre-response checks.
2.  **Phase 2: Model-Based Assessors & ContextCore Integration (Read).**
    *   Integrate an LLM-based assessor for more nuanced harmful content or coherence scoring (via `LLMInterface`).
    *   Begin integrating `FactVerificationAgent` to query a (potentially mock initially) `ContextCore`.
3.  **Phase 3: Policy Management & Advanced Assessors.**
    *   Implement full `ValidationPolicy` loading and application.
    *   Develop more sophisticated assessors (e.g., narrative consistency, advanced fact-checking).
    *   Refine reporting and explainability.
4.  **Phase 4: Feedback Loops & Optimization.**
    *   Integrate Actuarion's outputs more deeply with `LearningManager` and `SelfCritiqueModule`.
    *   Focus on performance optimization and reducing false positives/negatives.
5.  **Phase 5: Broader System Integration.**
    *   Ensure all relevant content-generating parts of the Unified-AI-Project can utilize Actuarion.
    *   Explore integration with the Fragmenta Bus System (Actuarion as a Module, assessors as Tech Blocks).

The Actuarion Module will be a critical component for ensuring the Unified-AI-Project operates responsibly and reliably, building trust and safety into its core.
