"""
ANGELA-MATRIX: [L3-L4] [γδ] [B] [L2]
DocumentLearner — hierarchical document ingestion into GARDEN + ED3N.
Learns Section→Paragraph→Sentence→Token levels with dedup.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Dict, Optional

from ai.document.chunker import DocumentChunker

logger = logging.getLogger(__name__)

_DOCUMENT_REGISTRY: Dict[str, float] = {}


class DocumentLearner:
    def __init__(self, garden_engine=None, ed3n_engine=None, chunker=None):
        self.garden = garden_engine
        self.ed3n = ed3n_engine
        self.chunker = chunker or DocumentChunker()

    def learn(self, text: str, source: str = "") -> Dict:
        doc_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if doc_hash in _DOCUMENT_REGISTRY:
            elapsed = time.time() - _DOCUMENT_REGISTRY[doc_hash]
            logger.warning("Duplicate document '%s' (learned %.1fs ago), skipping", source, elapsed)
            return {"status": "skipped_duplicate", "source": source, "hash": doc_hash}

        _DOCUMENT_REGISTRY[doc_hash] = time.time()

        tree = self.chunker.chunk(text, source=source)
        stats = {"sections": 0, "paragraphs": 0, "sentences": 0, "tokens": 0}

        for sec in tree.sections:
            self._learn_section(sec.header, sec.text, stats)
            for para in sec.paragraphs:
                self._learn_paragraph(para, sec.header, stats)
                for sent in para.sentences:
                    self._learn_sentence(sent, stats)
                tokens = self.chunker.extract_tokens(para.text)
                for token in tokens:
                    self._learn_token(token, para.text, stats)

        logger.info(
            "Learned '%s': %d sections, %d paragraphs, %d sentences, %d tokens",
            source, stats["sections"], stats["paragraphs"], stats["sentences"], stats["tokens"],
        )
        return {"status": "ok", "source": source, "hash": doc_hash, **stats}

    def _learn_section(self, header: str, text: str, stats: Dict) -> None:
        if not header or not text or self.garden is None:
            return
        self.garden.learn_from_interaction(header, text, confidence=0.5)
        stats["sections"] += 1

    def _learn_paragraph(self, para, section_header: str, stats: Dict) -> None:
        if not para.text or self.garden is None:
            return
        enriched_input = f"{section_header} {para.text}" if section_header else para.text
        self.garden.learn_from_interaction(enriched_input, para.text, confidence=0.6)
        stats["paragraphs"] += 1

    def _learn_sentence(self, sent: str, stats: Dict) -> None:
        if not sent:
            return
        if self.garden is not None:
            self.garden.learn_from_interaction(sent, sent, confidence=0.7)
        if self.ed3n is not None:
            self.ed3n.learn_reflex(sent, sent)
        stats["sentences"] += 1

    def _learn_token(self, token: str, context: str, stats: Dict) -> None:
        if self.garden is not None:
            existing = self.garden.dictionary._find_similar_key(token, threshold=0.9)
            if not existing:
                self.garden.dictionary.grow(token, token)
        if self.ed3n is not None:
            if not self.ed3n.dictionary.entries.get(token):
                self.ed3n.dictionary.add_entry(token, {"en": token})
        stats["tokens"] += 1
