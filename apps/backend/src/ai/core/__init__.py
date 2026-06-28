"""
Core AI module — query classification, model routing, execution gating.

P3: QueryClassifier (query type + confidence routing).
P4: ModelBus (LLM/ED3N/GARDEN routing with fallback).
P6: ExecutionGate (safety gating with consent/risk evaluation).
P7: DictionaryClassifier (dictionary-enhanced intent classification).
P28: TrainingCoordinator (domain training orchestration).
"""

from ai.core.dictionary_classifier import DictionaryClassifier, get_dictionary_classifier
from ai.core.execution_gate import GateDecision, ExecutionGate
from ai.core.model_bus import ModelCapability, ModelRouteResult, RouteDecision, ModelBus
from ai.core.query_classifier import QueryType, QueryResult, QueryClassifier
from ai.core.training_coordinator import DomainTrainingRecord, TrainingCoordinator
from ai.core.unicode_utils import (
    normalize_text,
    to_romaji,
    is_cjk,
    is_japanese,
    is_english_dominant,
    cjk_radical,
)

__all__ = [
    "DictionaryClassifier",
    "get_dictionary_classifier",
    "GateDecision",
    "ExecutionGate",
    "ModelCapability",
    "ModelRouteResult",
    "RouteDecision",
    "ModelBus",
    "QueryType",
    "QueryResult",
    "QueryClassifier",
    "DomainTrainingRecord",
    "TrainingCoordinator",
    "normalize_text",
    "to_romaji",
    "is_cjk",
    "is_japanese",
    "is_english_dominant",
    "cjk_radical",
]
