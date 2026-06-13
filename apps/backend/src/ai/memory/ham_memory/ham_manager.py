"""
ANGELA-MATRIX: [L4] [αβγδ] [A] [L3]
HAM (Hierarchical Associative Memory) Manager — minimal JSON-backed implementation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HAMMemoryManager:
    """Minimal JSON-backed hierarchical associative memory manager."""

    def __init__(
        self,
        memory_file: str = "angela_memory.json",
        auto_save: bool = True,
        core_storage_filename: Optional[str] = None,
    ):
        self.memory_file = Path(memory_file)
        self.auto_save = auto_save
        self._data: Dict[str, Any] = {"templates": [], "conversations": [], "metadata": {}}
        self._load()

    def _load(self) -> None:
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError, IOError):
                self._data = {"templates": [], "conversations": [], "metadata": {}}

    def _save(self) -> None:
        if not self.auto_save:
            return
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError, TypeError) as e:
            logger.warning(f"HAMMemoryManager save failed: {e}")

    async def store_template(self, template: Any) -> None:
        self._data["templates"].append({
            "content": getattr(template, "content", str(template)),
            "id": getattr(template, "id", None),
            "keywords": getattr(template, "keywords", []),
        })
        self._save()

    async def retrieve_response_templates(
        self,
        query: str,
        top_k: int = 5,
        angela_state=None,
        user_impression=None,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> List[Any]:
        count = limit or top_k
        return self._data["templates"][-count:]

    async def store_experience(
        self,
        raw_data: Any,
        data_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Store a raw experience entry into the memory store."""
        entry = {
            "content": str(raw_data),
            "data_type": data_type,
            "metadata": metadata or {},
        }
        self._data["templates"].append(entry)
        self._save()
        return f"exp_{len(self._data['templates'])}"

    def store_conversation(self, conversation: Dict[str, Any]) -> None:
        self._data["conversations"].append(conversation)
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "template_count": len(self._data["templates"]),
            "conversation_count": len(self._data["conversations"]),
        }