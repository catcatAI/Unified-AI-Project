# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [B] [L2]
# =============================================================================
"""
data_eng.chunk — single canonical document/template splitting.

Consolidates the scattered splitters:
  * ``DocumentChunker._split_sections`` / ``_split_paragraphs`` /
    ``_split_sentences``
  * ``Composer._split_template`` — a near-identical sentence splitter

All splitters are pure, stateless, and dependency-free so any caller
(chunker, composer, dictionary tokenizer) may delegate here.  The regexes and
behaviour below are the EXACT originals from DocumentChunker / Composer —
migration must not change split results.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

__all__ = [
    "split_paragraphs",
    "split_sections",
    "split_sentence_blocks",
    "split_sentences",
]

# DocumentChunker originals (verbatim)
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？.!?\n])\s*")
_SECTION_PATTERNS = [
    (re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE), 1),  # Markdown ## Header
    (re.compile(r"^([A-Z][A-Za-z\s]{2,50})$", re.MULTILINE), 2),  # Capitalized line
    (re.compile(r"^(\d+\.\d+\s+[A-Z].+)$", re.MULTILINE), 3),  # "1.1 Title"
    (
        re.compile(
            r"^(Abstract|Introduction|Method|Methods|Experiments|Results|"
            r"Discussion|Conclusion|References|Related Work)$",
            re.MULTILINE | re.IGNORECASE,
        ),
        4,
    ),
]
_TEMPLATE_ENDERS = frozenset(["。", "！", "？", ".", "!", "?"])


def _find_header_lines(lines: List[str]) -> List[Tuple[int, str, int]]:
    """掃描行首標頭（依 pattern 優先序短路）；回 (行號, 標題, level)。"""
    sections: List[Tuple[int, str, int]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat, priority in _SECTION_PATTERNS:
            m = pat.match(stripped)
            if m:
                sections.append((i, m.group(1).strip(), priority))
                break
    return sections


def _preamble_block(lines: List[str], start: int) -> Optional[Tuple[str, str, int]]:
    """取 start 之前的前言塊；無前言回 None。"""
    if start <= 0:
        return None
    preamble = "\n".join(lines[:start]).strip()
    if not preamble:
        return None
    return ("", preamble, 0)


def split_sections(text: str) -> List[Tuple[str, str, int]]:
    """Split *text* into ``(header, section_text, level)`` tuples.

    Mirrors ``DocumentChunker._split_sections`` exactly: line scan with header
    priority, preamble capture, section body until the next header.
    """
    lines = text.split("\n")
    sections = _find_header_lines(lines)

    if not sections:
        return [("", text.strip(), 0)]

    result: List[Tuple[str, str, int]] = []
    for j, (start, header, level) in enumerate(sections):
        end = sections[j + 1][0] if j + 1 < len(sections) else len(lines)
        sec_text = "\n".join(lines[start:end]).strip()
        if j == 0 and start > 0:
            block = _preamble_block(lines, start)
            if block:
                result.append(block)
        result.append((header, sec_text, level))

    first_block = _preamble_block(lines, sections[0][0])
    if first_block:
        result.insert(0, first_block)

    return result


def split_paragraphs(text: str) -> List[str]:
    """Split on blank-line boundaries; returns non-empty stripped paragraphs."""
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def split_sentences(text: str, min_len: int = 3) -> List[str]:
    """Split into sentences, dropping fragments shorter than *min_len*.

    Mirrors ``DocumentChunker._split_sentences`` (same lookbehind regex).
    """
    sents = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return [s for s in sents if len(s) >= min_len]


def split_sentence_blocks(template: str) -> List[str]:
    """Split a template/string into sentence blocks on punctuation.

    Mirrors ``Composer._split_template``: accumulates chars until an ender
    (。！？.!?) appears, flushing the accumulated block.  Unlike
    ``split_sentences`` this keeps the trailing block if non-empty.
    """
    sentences: List[str] = []
    current = ""
    for char in template:
        current += char
        if char in _TEMPLATE_ENDERS:
            if current.strip():
                sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    return sentences
