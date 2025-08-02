from typing import TypedDict, Required, Optional, List, Any, Union

# Fact Extractor Types
class UserPreferenceContent(TypedDict, total=False):
    category: Required[str]
    preference: Required[str]
    liked: Optional[bool]

class UserStatementContent(TypedDict, total=False):
    attribute: Required[str]
    value: Required[Any]

ExtractedFactContent = Union[UserPreferenceContent, UserStatementContent, Dict[str, Any]]

class ExtractedFact(TypedDict):
    fact_type: Required[str]
    content: Required[ExtractedFactContent]
    confidence: Required[float]

# Learning Manager Types
class LearnedFactRecord(TypedDict, total=False):
    record_id: Required[str]
    timestamp: Required[str]
    fact_type: Required[str]
    confidence: Required[float]
    source_text: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    source_interaction_ref: Optional[str]
    hsp_originator_ai_id: Optional[str]
    hsp_sender_ai_id: Optional[str]
    hsp_fact_id: Optional[str]
    hsp_fact_timestamp_created: Optional[str]
    resolution_strategy: Optional[str]
    supersedes_ham_records: Optional[List[str]]
    superseded_reason: Optional[str]
    conflicts_with_ham_records: Optional[List[str]]
    conflicting_values: Optional[List[str]]
    merged_from_ham_records: Optional[List[str]]
    original_values: Optional[List[Any]]
    merged_value: Optional[Any]
    merged_confidence: Optional[float]
    hsp_semantic_subject: Optional[str]
    hsp_semantic_predicate: Optional[str]
    hsp_semantic_object: Optional[Any]
    ca_subject_id: Optional[str]
    ca_predicate_type: Optional[str]
    ca_object_id: Optional[str]
