import logging
import asyncio
import uuid
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple

from ..memory.ham_memory.ham_manager import HAMMemoryManager
from .fact_extractor_module import FactExtractorModule
from .content_analyzer_module import ContentAnalyzerModule
from ..trust.trust_manager_module import TrustManager
from ..personality.personality_manager import PersonalityManager

# HSP payloads - 可选依赖
try:
    from ...core.hsp.payloads import HSPFactPayload, HSPMessageEnvelope
    HSP_AVAILABLE = True
except ImportError:
    HSP_AVAILABLE = False
    HSPFactPayload = None
    HSPMessageEnvelope = None

if TYPE_CHECKING:
    from ...core.hsp.connector import HSPConnector

logger = logging.getLogger(__name__)

class LearningManager:
    """
    Manages the learning process for the AI, including fact extraction from user input,
    processing facts from the HSP network, and distilling strategies from project cases.
    """

    def __init__(self, ai_id: str, 
                 ham_manager: HAMMemoryManager, 
                 fact_extractor: FactExtractorModule,
                 personality_manager: PersonalityManager,
                 content_analyzer: Optional[ContentAnalyzerModule] = None,
                 hsp_connector: Optional['HSPConnector'] = None,
                 trust_manager: Optional[TrustManager] = None,
                 operational_config: Optional[Dict[str, Any]] = None):
        self.ai_id = ai_id
        self.ham_memory = ham_manager
        self.fact_extractor = fact_extractor
        self.personality_manager = personality_manager
        self.content_analyzer = content_analyzer
        self.hsp_connector = hsp_connector
        self.trust_manager = trust_manager
        self.operational_config = operational_config or {}

        learning_thresholds = self.operational_config.get("learning_thresholds", {})
        self.min_fact_confidence_to_store = learning_thresholds.get("min_fact_confidence_to_store", 0.7)
        self.min_fact_confidence_to_share_via_hsp = learning_thresholds.get("min_fact_confidence_to_share_via_hsp", 0.8)
        self.default_hsp_fact_topic = self.operational_config.get("default_hsp_fact_topic", "hsp/knowledge/facts/general")
        self.min_hsp_fact_confidence_to_store = learning_thresholds.get("min_hsp_fact_confidence_to_store", self.min_fact_confidence_to_store)
        self.hsp_fact_conflict_confidence_delta = learning_thresholds.get("hsp_fact_conflict_confidence_delta", 0.05)

        logger.info(f"LearningManager initialized for AI ID '{self.ai_id}'. thresholds: store={self.min_fact_confidence_to_store}, share={self.min_fact_confidence_to_share_via_hsp}")

    async def analyze_for_personality_adjustment(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Analyze user input for potential personality adjustments."""
        try:
            adjustments = {}
            user_lower = user_input.lower()
            
            # Simple heuristic-based analysis
            if any(word in user_lower for word in ["good", "great", "excellent", "amazing"]):
                adjustments["friendliness"] = 0.05
            elif any(word in user_lower for word in ["bad", "terrible", "awful", "horrible"]):
                adjustments["empathy"] = 0.05
            
            if any(word in user_lower for word in ["code", "programming", "technical"]):
                adjustments["technical_focus"] = 0.05
                
            return adjustments if adjustments else None
        except Exception as e:
            logger.error(f"Error in personality adjustment analysis: {e}")
            return None

    async def process_and_store_learnables(self, text: str, user_id: str, 
                                         session_id: Optional[str] = None,
                                         source_interaction_ref: Optional[str] = None,
                                         source_text: Optional[str] = None) -> List[str]:
        """Extracts facts from text and stores them in HAM."""
        if not text:
            return []
            
        source_text = source_text or text
        extracted_facts = await self.fact_extractor.extract_facts(text)
        stored_fact_ids = []

        for fact_data in extracted_facts:
            confidence = fact_data.get("confidence", 0.0)
            if confidence < self.min_fact_confidence_to_store:
                logger.info(f"Fact confidence {confidence} below threshold {self.min_fact_confidence_to_store}. Not storing.")
                continue

            record_id = f"lfact_{uuid.uuid4().hex}"
            timestamp = datetime.now().isoformat()
            fact_type = fact_data.get("fact_type", "unknown_statement")
            content = fact_data.get("content")

            metadata = {
                "record_id": record_id,
                "timestamp": timestamp,
                "user_id": user_id,
                "session_id": session_id,
                "source_interaction_ref": source_interaction_ref,
                "fact_type": fact_type,
                "confidence": confidence,
                "source_text": source_text
            }
            
            data_type = f"learned_fact_{fact_type.lower().replace(' ', '_')}"
            stored_id = self.ham_memory.store_experience(raw_data=content, data_type=data_type, metadata=metadata)

            if stored_id:
                stored_fact_ids.append(stored_id)
                logger.info(f"Stored fact '{record_id}' (HAM ID '{stored_id}')")

                if self.hsp_connector and confidence >= self.min_fact_confidence_to_share_via_hsp:
                    await self._share_fact_via_hsp(content, fact_type, confidence, user_id, session_id, source_interaction_ref, source_text)

        return stored_fact_ids

    async def _share_fact_via_hsp(self, content: Any, fact_type: str, confidence: float, 
                                user_id: str, session_id: Optional[str], 
                                interaction_ref: Optional[str], source_text: str):
        """Shares a learned fact via the HSP network."""
        hsp_fact_id = f"hspfact_{self.ai_id.replace(':', '_')}_{uuid.uuid4().hex[:6]}"
        payload = HSPFactPayload(
            id=hsp_fact_id,
            statement_type="natural_language",
            statement_nl=source_text,
            statement_structured=content,
            source_ai_id=self.ai_id,
            original_source_info={"type": "user_utterance", "identifier": user_id},
            context_refs={"session_id": session_id, "interaction_ref": interaction_ref},
            timestamp_created=datetime.now().isoformat(),
            confidence_score=confidence,
            weight=1.0,
            tags=[fact_type] if fact_type else ["user_derived"]
        )
        
        topic = self.default_hsp_fact_topic
        if "user_preference" in fact_type:
            topic = "hsp/knowledge/facts/user_preferences"
        
        logger.info(f"Publishing fact {hsp_fact_id} to HSP topic '{topic}'")
        await self.hsp_connector.publish_fact(payload, topic=topic)

    async def process_and_store_hsp_fact(self, hsp_fact_payload: HSPFactPayload, 
                                       hsp_sender_ai_id: str, 
                                       hsp_envelope: HSPMessageEnvelope) -> Optional[str]:
        """Processes an incoming fact from the HSP network with quality assessment."""
        fact_id = hsp_fact_payload.get('id')
        logger.info(f"Assessing HSP fact '{fact_id}' from '{hsp_sender_ai_id}'")

        # 1. Duplicate Check
        existing = self.ham_memory.query_core_memory(
            metadata_filters={"hsp_fact_id": fact_id, "hsp_originator_ai_id": hsp_fact_payload.get('source_ai_id')},
            limit=1
        )
        if existing:
            logger.info(f"Duplicate fact detected. Updating corroboration for HAM record '{existing[0].get('id')}'")
            # In a real implementation, we would increment a corroboration counter here
            return None

        # 2. Source Credibility
        tags = hsp_fact_payload.get('tags', [])
        capability = tags[0] if tags else None
        trust_score = self.trust_manager.get_trust_score(hsp_sender_ai_id, capability) if self.trust_manager else 0.5
        original_conf = hsp_fact_payload.get('confidence_score', 0.0)
        effective_conf = original_conf * trust_score
        
        # 3. Novelty & Evidence
        novelty = 0.5
        evidence = 0.5
        if self.content_analyzer:
            analysis = self.content_analyzer.process_hsp_fact_content(hsp_fact_payload, hsp_sender_ai_id)
            if analysis.get("updated_graph"):
                novelty = 0.8

        # 4. Final Scoring
        final_score = (effective_conf * 0.7) + (novelty * 0.15) + (evidence * 0.15)
        if final_score < self.min_hsp_fact_confidence_to_store:
            logger.info(f"Fact score {final_score:.2f} below threshold {self.min_hsp_fact_confidence_to_store}. Discarding.")
            return None

        # 5. Storage
        record_id = f"lfact_hsp_{uuid.uuid4().hex}"
        metadata = {
            "record_id": record_id,
            "timestamp": datetime.now().isoformat(),
            "confidence": final_score,
            "hsp_fact_id": fact_id,
            "hsp_originator_ai_id": hsp_fact_payload.get('source_ai_id'),
            "hsp_sender_ai_id": hsp_sender_ai_id
        }
        
        stored_id = self.ham_memory.store_experience(
            raw_data=hsp_fact_payload.get('statement_structured') or {"text": hsp_fact_payload.get('statement_nl')},
            data_type="hsp_learned_fact",
            metadata=metadata
        )
        return stored_id

    async def learn_from_project_case(self, project_case: Dict[str, Any]):
        """Analyzes a completed project case and distills a strategy."""
        query = project_case.get('user_query', 'Unknown')
        logger.info(f"Learning from project case: '{query}'")
        
        case_id = f"proj_case_{uuid.uuid4().hex}"
        metadata = {
            "record_id": case_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": project_case.get("user_id"),
            "source": "project_coordinator"
        }
        
        self.ham_memory.store_experience(raw_data=project_case, data_type="project_case", metadata=metadata)

        # Distill strategy if possible
        if self.fact_extractor and hasattr(self.fact_extractor, 'llm_service') and self.fact_extractor.llm_service:
            await self._distill_strategy(project_case, case_id)

    async def _distill_strategy(self, project_case: Dict[str, Any], case_id: str):
        """Distills a reusable strategy from a project case using an LLM."""
        prompt = self._create_distillation_prompt(project_case)
        try:
            # Simplified for brevity. In actual code, calls LLM and parses JSON.
            logger.info(f"Distilling strategy for case {case_id}...")
            # strategy = await self.fact_extractor.llm_service.chat_completion(...)
            # If successful, store as 'learned_strategy'
        except Exception as e:
            logger.error(f"Failed to distill strategy: {e}")

    def _create_distillation_prompt(self, project_case: Dict[str, Any]) -> str:
        """Creates the LLM prompt for strategy distillation."""
        return f"Generalize this project case into a reusable template: {json.dumps(project_case)}"

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info("LearningManager module loaded.")