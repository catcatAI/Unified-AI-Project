"""Tests for text_utils — char_bigrams, bigram_jaccard, normalize_text."""
import pytest
from utils.text_utils import char_bigrams, bigram_jaccard, normalize_text


class TestCharBigrams:
    def test_normal_string(self):
        assert char_bigrams("abc") == {"ab", "bc"}

    def test_single_char(self):
        assert char_bigrams("a") == {"a"}

    def test_empty_string(self):
        assert char_bigrams("") == set()

    def test_two_chars(self):
        assert char_bigrams("ab") == {"ab"}

    def test_unicode(self):
        result = char_bigrams("你好")
        assert len(result) == 2

    def test_with_spaces(self):
        assert " " in char_bigrams("a b") or len(char_bigrams("a b")) == 2


class TestBigramJaccard:
    def test_identical_strings(self):
        sim = bigram_jaccard("hello", "hello")
        assert sim <= 0.95
        assert sim > 0.0

    def test_completely_different(self):
        sim = bigram_jaccard("abc", "xyz")
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = bigram_jaccard("abc", "abd")
        assert 0.0 < sim < 0.95

    def test_one_empty(self):
        assert bigram_jaccard("", "abc") == 0.0

    def test_both_empty(self):
        assert bigram_jaccard("", "") == 0.0

    def test_single_chars(self):
        sim = bigram_jaccard("a", "a")
        assert sim == 0.0

    def test_scaling_applied(self):
        sim = bigram_jaccard("abcd", "abcd")
        assert sim > 0.9

    def test_capped_at_0_95(self):
        for _ in range(10):
            sim = bigram_jaccard("abcdefghij", "abcdefghij")
            assert sim <= 0.95


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("HELLO") == "hello"

    def test_remove_punctuation(self):
        assert normalize_text("hello! world?") == "helloworld"

    def test_remove_chinese_punctuation(self):
        assert normalize_text("你好。世界？") == "你好世界"

    def test_already_normalized(self):
        assert normalize_text("hello") == "hello"

    def test_mixed_punctuation(self):
        result = normalize_text("Hi! 你好，世界？")
        assert "，" not in result
        assert "？" not in result
        assert "!" not in result
