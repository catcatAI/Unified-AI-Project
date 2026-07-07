"""Tests for ai.core.unicode_utils — CJK text normalization and detection"""
import pytest
from ai.core.unicode_utils import (
    cjk_radical,
    is_cjk,
    is_english_dominant,
    is_japanese,
    normalize_text,
    to_romaji,
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


class TestCjkRadical:
    def test_radical_known(self):
        result = cjk_radical("\u597d")
        assert isinstance(result, str)

    def test_radical_non_cjk(self):
        assert cjk_radical("a") == ""

    def test_radical_empty(self):
        assert cjk_radical("") == ""
