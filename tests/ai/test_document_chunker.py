"""
ANGELA-MATRIX: [L3] [γ] [B] [L2]
Tests for DocumentChunker — hierarchical document chunking.
"""

from ai.document.chunker import DocumentChunker, ChunkTree, Section, Paragraph


def test_empty_text():
    c = DocumentChunker()
    tree = c.chunk("")
    assert len(tree.sections) == 1
    assert not tree.sections[0].text


def test_single_section():
    c = DocumentChunker()
    tree = c.chunk("France is a country. Paris is the capital.")
    assert len(tree.sections) == 1
    assert len(tree.sections[0].paragraphs) == 1
    assert len(tree.sections[0].paragraphs[0].sentences) == 2


def test_markdown_sections():
    c = DocumentChunker()
    tree = c.chunk("# Section 1\nContent.\n\n## Section 2\nMore.")
    assert len(tree.sections) >= 2
    section_headers = [s.header for s in tree.sections if s.header]
    assert any("Section 1" in h for h in section_headers)
    assert any("Section 2" in h for h in section_headers)


def test_math_stripping_inline():
    c = DocumentChunker()
    cleaned = c._strip_math_and_code("Cost is $10. Formula: $x = y^2$.")
    assert "[MATH]" in cleaned
    assert "Cost" in cleaned


def test_math_stripping_display():
    c = DocumentChunker()
    cleaned = c._strip_math_and_code("Before. $$\nf(x) = x^2\n$$ After.")
    assert cleaned.count("[MATH]") == 1
    assert "After" in cleaned


def test_code_block_stripping():
    c = DocumentChunker()
    cleaned = c._strip_math_and_code("Text.\n```python\nprint('hi')\n```\nMore.")
    assert "[CODE]" in cleaned
    assert "More" in cleaned


def test_token_extraction():
    c = DocumentChunker()
    tokens = c.extract_tokens("France is a country in Western Europe.")
    assert "france" in tokens
    assert "country" in tokens
    assert "western" in tokens
    assert "europe" in tokens
    assert "is" not in tokens  # too short (min_len=3)
    assert "a" not in tokens


def test_cjk_token_extraction():
    c = DocumentChunker()
    tokens = c.extract_tokens("法国是欧洲的一个国家")
    assert any("法国" in t for t in tokens)
    assert any("欧洲" in t for t in tokens)


def test_sentence_splitting():
    c = DocumentChunker()
    sents = c._split_sentences("Hello world. How are you? I am fine!")
    assert len(sents) >= 3


def test_short_sentence_filter():
    c = DocumentChunker()
    sents = c._split_sentences("AB. CD EFG. Hello World.")
    assert all(len(s) >= 3 for s in sents)
    assert "Hello World" in sents[-1]


def test_very_short_sentence_filtered():
    c = DocumentChunker()
    sents = c._split_sentences("A. BC. DEF.")
    # "A." → len 2 < 3 → filtered; "BC." len 3 → kept; "DEF." len 4 → kept
    assert len(sents) == 2
    assert all(len(s) >= 3 for s in sents)
    assert sents[0] == "BC." or "BC" in sents[0]


def test_paragraph_splitting():
    c = DocumentChunker()
    paras = c._split_paragraphs("Para one.\n\nPara two.\n\nPara three.")
    assert len(paras) == 3


def test_section_fallback_no_headers():
    c = DocumentChunker()
    sections = c._split_sections("Plain text without headers. Just content.")
    assert len(sections) == 1
    assert sections[0][0] == ""
