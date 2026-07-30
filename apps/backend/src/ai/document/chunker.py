"""
ANGELA-MATRIX: [L3] [γ] [B] [L2]
Hierarchical document chunker — format→paragraph→sentence→token.
Filters out math formulas and code blocks before chunking.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# Math formula patterns to strip
_MATH_PATTERNS = [
    (r"\$\$[^$]*\$\$", "[MATH]"),
    (r"\$[^$\n]{1,200}\$", "[MATH]"),
    (r"\\\([^)]*\\\)", "[MATH]"),
    (r"\\\[[^\]]*\\\]", "[MATH]"),
]

# Code block patterns to strip
_CODE_PATTERNS = [
    (r"```[\s\S]*?```", "[CODE]"),
    (r"~~~[\s\S]*?~~~", "[CODE]"),
    (r"(?:^|\n)(?: {4}|\t)[^\n]+(?:\n(?: {4}|\t)[^\n]+)*", "\n[CODE]"),
]

# Section header patterns (in priority order)
_SECTION_PATTERNS = [
    (re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE), 1),            # Markdown ## Header
    (re.compile(r"^([A-Z][A-Za-z\s]{2,50})$", re.MULTILINE), 2),   # Capitalized short line = header
    (re.compile(r"^(\d+\.\d+\s+[A-Z].+)$", re.MULTILINE), 3),      # "1.1 Title"
    (re.compile(r"^(Abstract|Introduction|Method|Methods|Experiments|Results|Discussion|Conclusion|References|Related Work)$", re.MULTILINE | re.IGNORECASE), 4),
]

_SENTENCE_SPLIT = re.compile(r"(?<=[。！？.!?\n])\s*")


@dataclass
class Paragraph:
    text: str
    sentences: List[str] = field(default_factory=list)


@dataclass
class Section:
    header: str
    text: str
    paragraphs: List[Paragraph] = field(default_factory=list)
    level: int = 0


@dataclass
class ChunkTree:
    source: str = ""
    sections: List[Section] = field(default_factory=list)


class DocumentChunker:
    def chunk(self, text: str, source: str = "") -> ChunkTree:
        cleaned = self._strip_math_and_code(text)
        sections = self._split_sections(cleaned)
        tree = ChunkTree(source=source)
        for sec_header, sec_text, sec_level in sections:
            section = Section(header=sec_header, text=sec_text, level=sec_level)
            for para_text in self._split_paragraphs(sec_text):
                para = Paragraph(text=para_text)
                para.sentences = self._split_sentences(para_text)
                section.paragraphs.append(para)
            tree.sections.append(section)
        return tree

    def _strip_math_and_code(self, text: str) -> str:
        for pattern, replacement in _MATH_PATTERNS + _CODE_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def _split_sections(self, text: str) -> List[tuple[str, str, int]]:
        lines = text.split("\n")
        sections: List[tuple[int, str, int]] = []  # (line_idx, header_text, level)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            for pat, priority in _SECTION_PATTERNS:
                m = pat.match(stripped)
                if m:
                    sections.append((i, m.group(1).strip(), priority))
                    break

        if not sections:
            return [("", text.strip(), 0)]

        result = []
        for j, (start, header, level) in enumerate(sections):
            end = sections[j + 1][0] if j + 1 < len(sections) else len(lines)
            sec_text = "\n".join(lines[start:end]).strip()
            if j == 0 and start > 0:
                preamble = "\n".join(lines[:start]).strip()
                if preamble:
                    result.append(("", preamble, 0))
            result.append((header, sec_text, level))

        if sections[0][0] > 0:
            preamble = "\n".join(lines[:sections[0][0]]).strip()
            if preamble:
                result.insert(0, ("", preamble, 0))

        return result

    def _split_paragraphs(self, text: str) -> List[str]:
        parts = re.split(r"\n\s*\n", text)
        return [p.strip() for p in parts if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        sents = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
        return [s for s in sents if len(s) >= 3]

    def extract_tokens(self, text: str, min_len: int = 3) -> List[str]:
        tokens = set()
        for word in text.lower().split():
            cleaned = word.strip(".,!?;:'\"()[]{}「」『』【】《》""''")
            if cleaned and len(cleaned) >= min_len:
                tokens.add(cleaned)
        for run in re.findall(r"[\u4e00-\u9fff]{2,}", text.lower()):
            if len(run) >= 2:
                tokens.add(run)
        return sorted(tokens)
