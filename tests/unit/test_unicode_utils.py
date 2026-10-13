"""Tests for ai.core.unicode_utils — CJK text normalization and detection"""

import pytest
from ai.core.unicode_utils import (
    cjk_radical,
    is_cjk,
    is_english_dominant,
    is_japanese,
    normalize_text,
    to_romaji,
    to_simplified,
)


class TestNormalizeText:
    def test_ascii_fast_path(self):
        assert normalize_text("hello") == "hello"

    def test_strip_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_fullwidth_to_halfwidth(self):
        result = normalize_text("\uff28\uff45\uff4c\uff4c\uff4f")
        assert result == "Hello"

    def test_nfkc_compatibility(self):
        result = normalize_text("\u2460")
        assert result != ""

    def test_zero_width_stripped(self):
        original = "he\u200bll\u200co"
        assert normalize_text(original) == "hello"

    def test_mixed_content(self):
        result = normalize_text("  \u2460\u2461 \u200b ABC  ")
        assert "ABC" in result


class TestToRomaji:
    def test_hiragana(self):
        assert to_romaji("\u3053\u3093\u306b\u3061\u306f") == "konnichiha"

    def test_katakana(self):
        assert to_romaji("\u30b3\u30f3\u30cb\u30c1\u30cf") == "konnichiha"

    def test_mixed_non_kana(self):
        assert to_romaji("abc\u3042") == "abca"

    def test_pure_ascii(self):
        assert to_romaji("hello") == "hello"

    def test_empty_string(self):
        assert to_romaji("") == ""


class TestCharacterDetection:
    def test_is_cjk_kanji(self):
        assert is_cjk("\u4e00")
        assert is_cjk("\u9fff")

    def test_is_cjk_non_cjk(self):
        assert not is_cjk("a")
        assert not is_cjk("\u3041")

    def test_is_japanese_hiragana(self):
        assert is_japanese("\u3041")

    def test_is_japanese_katakana(self):
        assert is_japanese("\u30a1")

    def test_is_japanese_non_kana(self):
        assert not is_japanese("a")
        assert not is_japanese("\u4e00")

    def test_is_english_dominant_ascii(self):
        assert is_english_dominant("hello world")

    def test_is_english_dominant_cjk(self):
        assert not is_english_dominant("\u4e16\u754c\u4f60\u597d")

    def test_is_english_dominant_mixed(self):
        assert is_english_dominant("hello\u4e16\u754c")

    def test_is_english_dominant_empty(self):
        assert is_english_dominant("")

    def test_is_english_dominant_pure_cjk(self):
        assert not is_english_dominant("\u65e5\u672c\u8a9e")

    def test_is_english_dominant_no_alpha_returns_true(self):
        assert is_english_dominant("12345 !!!") is True


class TestToSimplified:
    """The template library, emotion lexicon and categories are all Simplified;
    a Traditional input used to match none of their keywords (我好難過 matched
    nothing and fell through to a random category pick)."""

    def test_traditional_folds_to_simplified(self):
        assert to_simplified("我好難過") == "我好难过"
        assert to_simplified("我很開心") == "我很开心"
        assert to_simplified("謝謝你") == "谢谢你"

    def test_simplified_unchanged(self):
        assert to_simplified("我好难过") == "我好难过"
        assert to_simplified("想你了") == "想你了"

    def test_ascii_and_empty_pass_through(self):
        assert to_simplified("hello world") == "hello world"
        assert to_simplified("") == ""

    def test_mixed_script_only_folds_cjk(self):
        assert to_simplified("I miss you 想你") == "I miss you 想你"
        assert to_simplified("我很開心 OK") == "我很开心 OK"

    def test_returns_new_string_without_mutating_input(self):
        original = "我好難過"
        assert to_simplified(original) == "我好难过"
        assert original == "我好難過"

    def test_table_is_parallel_and_complete(self):
        """A truncated or misaligned regeneration must fail loudly, not fold
        characters to whatever happens to line up."""
        from ai.core.t2s_table import PAIR_COUNT, SIMPLIFIED, TRADITIONAL

        assert len(TRADITIONAL) == len(SIMPLIFIED) == PAIR_COUNT
        assert PAIR_COUNT > 3000
        assert len(set(TRADITIONAL)) == PAIR_COUNT


class TestCjkRadical:
    def test_radical_known(self):
        result = cjk_radical("\u597d")
        assert isinstance(result, str)

    def test_radical_non_cjk(self):
        assert cjk_radical("a") == ""

    def test_radical_empty(self):
        assert cjk_radical("") == ""

    def test_hira_to_kata_passthrough_for_non_hiragana(self):
        from ai.core.unicode_utils import _hira_to_kata

        assert _hira_to_kata("A") == "A"
        assert _hira_to_kata("\u30a2") == "\u30a2"
