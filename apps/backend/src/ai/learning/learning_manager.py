# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager  # noqa: F401
except ImportError:
    HAMMemoryManager = None  # type: ignore

try:
    from ai.trust.trust_manager_module import TrustManager  # noqa: F401
except ImportError:
    TrustManager = None  # type: ignore

try:
    from ai.personality.personality_manager import PersonalityManager  # noqa: F401
except ImportError:
    PersonalityManager = None  # type: ignore

try:
    from core.interfaces.protocols import HSPProtocol  # noqa: F401
except ImportError:
    HSPProtocol = None  # type: ignore

try:
    from ai.knowledge_graph.types import KnowledgeGraphTypes  # noqa: F401
except ImportError:
    KnowledgeGraphTypes = None  # type: ignore

try:
    from core.hsp.types import HSPTypes  # noqa: F401
except ImportError:
    HSPTypes = None  # type: ignore

try:
    import networkx  # noqa: F401
except ImportError:
    networkx = None  # type: ignore


_POSITIVE_KEYWORDS = {"great", "amazing", "excellent", "wonderful", "fantastic", "good", "nice", "happy", "love", "perfect"}
_NEGATIVE_KEYWORDS = {"terrible", "awful", "bad", "horrible", "sad", "angry", "hate", "worst", "poor", "ugly"}
_TECHNICAL_KEYWORDS = {"code", "programming", "python", "function", "class", "api", "bug", "fix", "algorithm", "data"}


class LearningManager:
    """学习管理器 - 管理事实提取、存储、HSP共享和个性调整"""

    def __init__(
        self,
        ai_id: str,
        ham_manager: Any = None,
        fact_extractor: Any = None,
        personality_manager: Any = None,
        content_analyzer: Any = None,
        hsp_connector: Any = None,
        trust_manager: Any = None,
        operational_config: Optional[Dict[str, Any]] = None,
    ):
        self.ai_id = ai_id
        self.ham_memory = ham_manager
        self.fact_extractor = fact_extractor
        self.personality_manager = personality_manager
        self.content_analyzer = content_analyzer
        self.hsp_connector = hsp_connector
        self.trust_manager = trust_manager
        self.operational_config = operational_config or {}

        thresholds = self.operational_config.get("learning_thresholds", {})
        self.min_fact_confidence_to_store = thresholds.get("min_fact_confidence_to_store", 0.7)
        self.min_fact_confidence_to_share_via_hsp = thresholds.get("min_fact_confidence_to_share_via_hsp", 0.8)
        self.min_hsp_fact_confidence_to_store: float = 0.5

    async def analyze_for_personality_adjustment(self, text: str) -> Optional[Dict[str, float]]:
        if not text:
            return None
        words = set(text.lower().split())
        if words & _POSITIVE_KEYWORDS:
            return {"friendliness": 0.05}
        if words & _NEGATIVE_KEYWORDS:
            return {"empathy": 0.05}
        if words & _TECHNICAL_KEYWORDS:
            return {"technical_focus": 0.05}
        return None

    async def process_and_store_learnables(self, text: str, user_id: str) -> List[str]:
        if not text:
            return []
        if self.fact_extractor is None:
            return []
        facts = await self.fact_extractor.extract_facts(text)
        stored_ids = []
        for fact in facts:
            if fact.get("confidence", 0) >= self.min_fact_confidence_to_store:
                store_data = {
                    "fact": fact,
                    "user_id": user_id,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
                fact_keywords = [k for k in [
                    fact.get("subject"),
                    fact.get("predicate"),
                    fact.get("object"),
                    user_id,
                ] if k]
                stored_id = self.ham_memory.store_experience(
                    store_data, data_type="learned_fact", keywords=fact_keywords,
                )
                stored_ids.append(stored_id)
                if (
                    fact.get("confidence", 0) >= self.min_fact_confidence_to_share_via_hsp
                    and self.hsp_connector is not None
                ):
                    await self.hsp_connector.publish_fact(fact)
        return stored_ids

    async def process_and_store_hsp_fact(
        self,
        hsp_payload: Dict[str, Any],
        sender_ai_id: str,
        _interaction_id: Optional[str] = None,
    ) -> Optional[str]:
        fact_id = hsp_payload.get("id", "")
        if not fact_id:
            return None

        existing = self.ham_memory.query_core_memory({"hsp_fact_id": fact_id})
        if existing:
            return None

        trust_score = 0.5
        if self.trust_manager is not None:
            trust_score = self.trust_manager.get_trust_score(sender_ai_id)

        confidence = hsp_payload.get("confidence_score", 0.0)
        effective_confidence = confidence * trust_score

        if effective_confidence < self.min_hsp_fact_confidence_to_store:
            return None

        if self.content_analyzer is not None:
            self.content_analyzer.process_hsp_fact_content(hsp_payload)

        store_data = {
            "hsp_payload": hsp_payload,
            "sender_ai_id": sender_ai_id,
            "trust_score": trust_score,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
        hsp_keywords = [k for k in [
            sender_ai_id,
            hsp_payload.get("type"),
            hsp_payload.get("topic"),
        ] if k]
        stored_id = self.ham_memory.store_experience(
            store_data, data_type="hsp_fact", keywords=hsp_keywords,
        )
        return stored_id

    async def learn_from_project_case(self, project_case: Dict[str, Any]) -> None:
        case_keywords = [k for k in [
            project_case.get("name"),
            project_case.get("type"),
            project_case.get("category"),
        ] if k]
        self.ham_memory.store_experience(
            project_case, data_type="project_case", keywords=case_keywords,
        )
