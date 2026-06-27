"""MultimodalRAGEngine — cross-modal retrieval-augmented generation for ED3N.

P21: Orchestrates encoding → retrieval → dictionary integration pipeline.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from ai.multimodal.multimodal_bridge import MultimodalBridge
from ai.multimodal.multimodal_retriever import MultimodalRetriever

logger = logging.getLogger(__name__)


class MultimodalRAGEngine:
    """Cross-modal RAG engine: encode query → retrieve related entries → ED3N-ready output.

    Connects MultimodalBridge (encoding/decoding) with MultimodalRetriever
    (vector index) and generates ED3N DictionaryLayer-compatible entries.

    Usage:
        engine = MultimodalRAGEngine()
        engine.index_image(image_bytes, "img_001", label="sunset photo")
        engine.index_audio(audio_bytes, "aud_001", label="ocean waves")
        results = engine.query_by_image(image_bytes)  # cross-modal retrieval!
    """

    def __init__(self, retriever: Optional[MultimodalRetriever] = None,
                 bridge: Optional[MultimodalBridge] = None):
        self._retriever = retriever or MultimodalRetriever()
        self._bridge = bridge or MultimodalBridge()

    # --- Indexing ---

    def index_image(self, image_data: bytes, key: str,
                    label: str = "",
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Encode image and index its latent vector."""
        latent = self._bridge.encode_image_to_latent(image_data)
        if latent is None:
            return False
        meta = {"label": label, **(metadata or {})}
        self._retriever.add_from_bridge(key, latent, modality="vision", metadata=meta)
        return True

    def index_audio(self, audio_data: bytes, key: str,
                    label: str = "",
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Encode audio and index its latent vector."""
        latent = self._bridge.encode_audio_to_latent(audio_data)
        if latent is None:
            return False
        meta = {"label": label, **(metadata or {})}
        self._retriever.add_from_bridge(key, latent, modality="audio", metadata=meta)
        return True

    def index_latent(self, latent: List[float], key: str,
                     modality: str = "",
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Index an already-computed latent vector."""
        self._retriever.add_from_bridge(key, latent, modality=modality, metadata=metadata or {})

    def index_from_entry(self, latent: List[float],
                         entry: Dict[str, Any]) -> None:
        """Index from a MultimodalBridge-generated dictionary entry."""
        self._retriever.add_from_bridge(
            entry.get("key", ""), latent,
            modality="vision" if entry.get("key", "").startswith("mm_vision") else "",
            metadata={"value": entry.get("value", ""), "source": "bridge"}
        )

    # --- Querying ---

    def query_by_image(self, image_data: bytes, top_k: int = 5
                       ) -> List[Dict[str, Any]]:
        """Encode an image query and retrieve similar indexed entries (cross-modal)."""
        latent = self._bridge.encode_image_to_latent(image_data)
        if latent is None:
            return []
        return self._retriever.search_by_list(latent, top_k=top_k)

    def query_by_audio(self, audio_data: bytes, top_k: int = 5
                       ) -> List[Dict[str, Any]]:
        """Encode an audio query and retrieve similar indexed entries."""
        latent = self._bridge.encode_audio_to_latent(audio_data)
        if latent is None:
            return []
        return self._retriever.search_by_list(latent, top_k=top_k)

    def query_by_latent(self, latent: List[float], top_k: int = 5
                        ) -> List[Dict[str, Any]]:
        """Query by raw latent vector."""
        return self._retriever.search_by_list(latent, top_k=top_k)

    # --- ED3N integration ---

    def to_ed3n_entries(self, results: List[Dict[str, Any]]
                        ) -> List[Dict[str, Any]]:
        """Convert retriever results to ED3N DictionaryLayer-compatible entries.

        Each entry: {'key': str, 'surface_forms': dict, 'contexts': list, 'confidence': float}
        """
        entries = []
        for r in results:
            label = r.get("metadata", {}).get("label", r["key"])
            entries.append({
                "key": r["key"],
                "surface_forms": {"en": label},
                "contexts": [{
                    "modality": r.get("modality", ""),
                    "similarity_score": r["score"],
                    "source": "multimodal_rag",
                }],
                "confidence": max(0.0, min(1.0, (r["score"] + 1.0) / 2.0)),
            })
        return entries

    def retrieve_entries(self, image_data: Optional[bytes] = None,
                         audio_data: Optional[bytes] = None,
                         latent: Optional[List[float]] = None,
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Unified retrieval: accepts any modality query, returns ED3N entries."""
        if latent is not None:
            results = self.query_by_latent(latent, top_k)
        elif image_data is not None:
            results = self.query_by_image(image_data, top_k)
        elif audio_data is not None:
            results = self.query_by_audio(audio_data, top_k)
        else:
            return []
        return self.to_ed3n_entries(results)

    # --- Persistence ---

    def save_index(self, filepath: str) -> None:
        self._retriever.save(filepath)

    def load_index(self, filepath: str) -> int:
        return self._retriever.load(filepath)

    @property
    def retriever(self) -> MultimodalRetriever:
        return self._retriever

    @property
    def bridge(self) -> MultimodalBridge:
        return self._bridge