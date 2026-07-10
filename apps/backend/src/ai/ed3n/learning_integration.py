# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L3]
# =============================================================================

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ED3NLearningIntegration:
    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine
        self._learning_manager: Optional[Any] = None
        self._replay_buffer: Optional[Any] = None
        self._memory_learning: Optional[Any] = None
        self._connected_systems: Dict[str, bool] = {
            "learning_manager": False,
            "replay_buffer": False,
            "memory_learning": False,
        }
        self._sync_history: List[Dict[str, Any]] = []

    def connect_to_learning_manager(self, learning_manager: Any) -> None:
        self._learning_manager = learning_manager
        self._connected_systems["learning_manager"] = True
        logger.info("Connected to LearningManager.")

    def connect_to_replay_buffer(self, replay_buffer: Any) -> None:
        self._replay_buffer = replay_buffer
        self._connected_systems["replay_buffer"] = True
        logger.info("Connected to ExperienceReplayBuffer.")

    def connect_to_memory_learning(self, memory_learning: Any) -> None:
        self._memory_learning = memory_learning
        self._connected_systems["memory_learning"] = True
        logger.info("Connected to MemoryLearningEngine.")

    def _get_learning_manager(self):
        # ai.learning package was removed in Phase 9-12 cleanup
        return None

    def _get_replay_buffer(self):
        # ai.learning package was removed in Phase 9-12 cleanup
        return None

    def _get_memory_learning(self):
        # ai.learning package was removed in Phase 9-12 cleanup
        return None

    def extract_concepts_from_interaction(self, text: str) -> List[Dict]:
        lm = self._get_learning_manager()
        if lm is None or not hasattr(lm, "fact_extractor") or lm.fact_extractor is None:
            logger.warning("No fact extractor available via LearningManager.")
            return []

        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(
                lm.fact_extractor.extract_facts(text), loop
            )
            return future.result()
        except RuntimeError:
            return asyncio.run(lm.fact_extractor.extract_facts(text))
        except Exception as e:
            logger.exception("Failed to extract concepts: %s", e)
            return []

    def record_training_feedback(
        self, example_key: str, success: bool, metadata: Dict
    ) -> None:
        ml = self._get_memory_learning()
        if ml is None:
            logger.warning("MemoryLearningEngine not available; feedback not recorded.")
            return
        try:
            if hasattr(ml, "record_feedback"):
                ml.record_feedback(
                    example_key=example_key, success=success, metadata=metadata
                )
            else:
                logger.warning("MemoryLearningEngine has no record_feedback method.")
            logger.info(
                "Recorded training feedback for %s (success=%s).",
                example_key,
                success,
            )
        except Exception as e:
            logger.exception("Failed to record feedback: %s", e)

    def synchronize_knowledge(self) -> Dict:
        lm = self._get_learning_manager()
        if lm is None:
            return {"synced": 0, "errors": ["LearningManager not available"]}

        ham = getattr(lm, "ham_memory", None)
        if ham is None:
            logger.warning("HAM memory not available via LearningManager.")
            return {"synced": 0, "errors": ["HAM memory not available"]}

        dictionary = self._get_ed3n_dictionary()
        if dictionary is None or not dictionary.entries:
            logger.warning("ED3N dictionary is empty or not available.")
            return {"synced": 0, "errors": ["ED3N dictionary empty or unavailable"]}

        synced_count = 0
        errors: List[str] = []

        for key, entry in dictionary.entries.items():
            try:
                memory_entry = {
                    "source": "ed3n",
                    "dictionary_key": key,
                    "surface_forms": entry.surface_forms,
                    "confidence": entry.confidence,
                    "relations": entry.relations,
                    "contexts": entry.contexts,
                    "timestamp": datetime.now().isoformat(),
                }
                ham.store_experience(
                    memory_entry,
                    data_type="ed3n_entry",
                    keywords=[key] + list(entry.surface_forms.values())[:5] if entry.surface_forms else [],
                )
                synced_count += 1
            except Exception as e:
                errors.append(f"Failed to sync entry {key}: {e}")

        self._sync_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "synced": synced_count,
                "errors": errors,
            }
        )

        logger.info("Synchronized %d ED3N entries to HAM memory.", synced_count)
        return {"synced": synced_count, "errors": errors}

    def _get_ed3n_dictionary(self) -> Optional[Any]:
        if self.engine is not None and hasattr(self.engine, "dictionary"):
            return self.engine.dictionary
        try:
            from .dictionary_layer import DictionaryLayer

            return DictionaryLayer()
        except ImportError:
            logger.warning("ED3N DictionaryLayer not available.")
            return None

    def get_integration_status(self) -> Dict:
        lm = self._get_learning_manager()
        rb = self._get_replay_buffer()
        ml = self._get_memory_learning()

        return {
            "connected": dict(self._connected_systems),
            "learning_manager_available": lm is not None,
            "replay_buffer_available": rb is not None,
            "memory_learning_available": ml is not None,
            "sync_history_count": len(self._sync_history),
            "last_sync": self._sync_history[-1] if self._sync_history else None,
        }
