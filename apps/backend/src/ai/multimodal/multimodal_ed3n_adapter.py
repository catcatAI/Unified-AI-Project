"""MultimodalED3NAdapter — bidirectional wiring between multimodal RAG and ED3N.

P22: Enriches ED3N process_multimodal with cross-modal retrieval.
"""

import logging
from typing import Any, Dict, List, Optional

from ai.multimodal.multimodal_rag_engine import MultimodalRAGEngine

logger = logging.getLogger(__name__)


class MultimodalED3NAdapter:
    """Bidirectional adapter between MultimodalRAGEngine and ED3NEngine.

    Provides:
      - retrieve_multimodal(): query by image/audio → ED3N-compatible entries
      - inject_into_context(): add multimodal entries to ED3N context for decoding
    """

    def __init__(self, rag_engine: Optional[MultimodalRAGEngine] = None):
        self._rag_engine = rag_engine or MultimodalRAGEngine()

    @property
    def rag_engine(self) -> MultimodalRAGEngine:
        return self._rag_engine

    def retrieve_multimodal(
        self,
        image_data: Optional[bytes] = None,
        audio_data: Optional[bytes] = None,
        latent: Optional[List[float]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve ED3N-compatible entries from multimodal query.

        Returns:
            List of dicts: {key, surface_forms, contexts, confidence}
        """
        return self._rag_engine.retrieve_entries(
            image_data=image_data,
            audio_data=audio_data,
            latent=latent,
            top_k=top_k,
        )

    def inject_into_context(
        self,
        context: Dict[str, Any],
        image_data: Optional[bytes] = None,
        audio_data: Optional[bytes] = None,
        latent: Optional[List[float]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Inject multimodal RAG results into an ED3N context dict.

        The entries are added under context['multimodal_entries'] so that
        downstream decoding stages can reference them.
        """
        entries = self.retrieve_multimodal(
            image_data=image_data,
            audio_data=audio_data,
            latent=latent,
            top_k=top_k,
        )
        ctx = dict(context) if context else {}
        ctx["multimodal_entries"] = entries
        return ctx

    def index_image_for_retrieval(
        self,
        image_data: bytes,
        key: str,
        label: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index an image for future retrieval."""
        return self._rag_engine.index_image(image_data, key, label, metadata)

    def index_audio_for_retrieval(
        self,
        audio_data: bytes,
        key: str,
        label: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index an audio for future retrieval."""
        return self._rag_engine.index_audio(audio_data, key, label, metadata)

    def save_index(self, filepath: str) -> None:
        self._rag_engine.save_index(filepath)

    def load_index(self, filepath: str) -> int:
        return self._rag_engine.load_index(filepath)
