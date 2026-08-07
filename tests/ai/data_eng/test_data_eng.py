# =============================================================================
# ANGELA-MATRIX: [L3] [αβγ] [C] [L2]
# =============================================================================
"""
Tests for ai.data_eng — the unified data-engineering pipeline.

Covers dedup (prefix/surface/hash-domain/download-key), chunking
(sections/paragraphs/sentences/template blocks), anchored reassembly
(slot budget + key selection), and growth gating.
"""

import random
import string

from ai.data_eng.assemble import decode_slot_budget, select_anchored_keys
from ai.data_eng.chunk import (
    split_paragraphs,
    split_sections,
    split_sentence_blocks,
    split_sentences,
)
from ai.data_eng.dedup import (
    count_suffix_key,
    download_dedup_key,
    hash_domain_dedup,
    prefix_dedup,
    prefix_overlap,
    surface_dedup,
)
from ai.data_eng.grow import (
    batch_cap_ok,
    growth_cap_ok,
    growth_gate_batch,
    resolved_max_entries,
)


def _rand_word(min_len=4, max_len=10):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(random.randint(min_len, max_len)))


class TestPrefixOverlap:
    def test_exact(self):
        assert prefix_overlap("happy", "happy") == 1.0

    def test_word_forms(self):
        assert prefix_overlap("happy", "happiness") == 0.8

    def test_short_prefix_below_min(self):
        assert prefix_overlap("ab", "abc") == 0.0  # prefix 2 < min 3

    def test_unrelated(self):
        assert prefix_overlap("happy", "glad") == 0.0

    def test_empty(self):
        assert prefix_overlap("", "x") == 0.0
        assert prefix_overlap("x", "") == 0.0


class TestPrefixDedup:
    def test_finds_shared_prefix(self):
        forms = [("happy", "e1"), ("glad", "e2")]
        key, score = prefix_dedup("happiness", forms, threshold=0.5)
        assert key == "e1"
        assert score >= 0.8

    def test_threshold_gates(self):
        forms = [("glad", "e2")]
        key, _ = prefix_dedup("happiness", forms, threshold=0.5)
        assert key is None

    def test_empty_forms(self):
        key, score = prefix_dedup("hello", [])
        assert key is None
        assert score == 0.0


class TestSurfaceDedup:
    def test_exact_lookup(self):
        assert surface_dedup(" Hello ", {"hello": "g1"}) == "g1"

    def test_miss(self):
        assert surface_dedup("nope", {"hello": "g1"}) is None


class TestHashDomainDedup:
    def test_first_seen_returns_false(self):
        seen = {}
        assert hash_domain_dedup("hello", seen, "knowledge") is False

    def test_duplicate_returns_true(self):
        seen = {}
        hash_domain_dedup("hello", seen, "knowledge")
        assert hash_domain_dedup("hello", seen, "knowledge") is True

    def test_domains_isolated(self):
        seen = {}
        hash_domain_dedup("hello", seen, "knowledge")
        assert hash_domain_dedup("hello", seen, "garden") is False

    def test_bound_drops_oldest(self):
        seen = {}
        for i in range(150):
            hash_domain_dedup(f"sample-{i}", seen, "d", max_hashes_per_domain=100)
        assert len(seen["d"]) == 100


class TestDownloadKey:
    def test_first_key_no_suffix(self):
        c = {}
        k, n = count_suffix_key("hello", c)
        assert k == "hello"
        assert n == 1

    def test_second_key_gets_suffix(self):
        c = {}
        count_suffix_key("hello", c)
        k, n = count_suffix_key("hello", c)
        assert k == "hello_2"
        assert n == 2

    def test_download_dedup_key_prefix(self):
        c = {}
        assert download_dedup_key("happy day", c, "jmdict") == "jmdict_happy_day"
        assert download_dedup_key("happy day", c, "jmdict") == "jmdict_happy_day_2"

    def test_download_dedup_key_seen_words(self):
        c = {}
        seen = set()
        first = download_dedup_key("hello", c, "cedict", seen_words=seen)
        assert first == "cedict_hello"
        # Same base via a different column now collides -> suffix.
        again = download_dedup_key("hello", c, "cedict", seen_words=seen)
        assert again.startswith("cedict_hello_")

    def test_short_word_hashed(self):
        c = {}
        k = download_dedup_key("a", c, "koedict")
        assert k.startswith("koedict_")


class TestChunking:
    def test_split_sentences(self):
        sents = split_sentences("Hello world. How are you? I am fine!")
        assert "How are you?" in sents
        assert len(sents) >= 3

    def test_split_sentences_drops_short(self):
        sents = split_sentences("A. BC. DEF.")
        assert all(len(s) >= 3 for s in sents)

    def test_split_paragraphs(self):
        paras = split_paragraphs("Para one.\n\nPara two.\n\nPara three.")
        assert paras == ["Para one.", "Para two.", "Para three."]

    def test_split_sections_plain(self):
        sections = split_sections("Plain text without headers. Just content.")
        assert len(sections) == 1
        assert sections[0][0] == ""

    def test_split_sections_headers(self):
        text = "# Intro\n\nhello\n\n## Body\n\nworld"
        sections = split_sections(text)
        headers = [h for h, _s, _l in sections]
        assert "Intro" in headers
        assert "Body" in headers

    def test_split_sentence_blocks(self):
        blocks = split_sentence_blocks("你好！我是Angela。How are you?")
        assert blocks == ["你好！", "我是Angela。", "How are you?"]


class TestAssemble:
    def test_slot_budget(self):
        assert decode_slot_budget(2) == (2, 4)
        assert decode_slot_budget(8) == (3, 3)
        assert decode_slot_budget(20) == (3, 6)

    def test_select_anchored_keys_anchors_first(self):
        result = select_anchored_keys(
            {"k9": 0.9},
            {"k1": 1.0, "k2": 0.8},
            decode_gate=0.15,
        )
        assert result[0] == "k1"
        assert "k2" in result

    def test_select_anchored_keys_dedup(self):
        # SNN key identical to an anchor must not be duplicated.
        result = select_anchored_keys(
            {"k1": 0.99, "k5": 0.6},
            {"k1": 1.0},
            decode_gate=0.15,
        )
        assert result.count("k1") == 1

    def test_select_anchored_keys_gate_filters(self):
        result = select_anchored_keys(
            {"kLow": 0.01},
            {"k1": 1.0},
            decode_gate=0.15,
        )
        assert "kLow" not in result


class TestGrow:
    def test_growth_cap_ok(self):
        assert growth_cap_ok(99, 100) is True
        assert growth_cap_ok(100, 100) is False

    def test_batch_cap_ok(self):
        assert batch_cap_ok(90, 10, 100) is True
        assert batch_cap_ok(91, 10, 100) is False

    def test_growth_gate_batch_stops_at_cap(self):
        texts = [f"w{i}" for i in range(10)]
        accepted = growth_gate_batch(95, texts, max_entries=100)
        assert len(accepted) == 5

    def test_resolved_max_entries(self):
        assert resolved_max_entries(None, default=10000) == 10000
        assert resolved_max_entries(40786) == 40786
        assert resolved_max_entries(0) == 10000


class TestRandomSampling:
    """Random-sample equivalence: dedup/chunk outputs stay consistent."""

    def test_prefix_overlap_is_deterministic(self):
        rng = random.Random(42)
        for _ in range(200):
            a = _rand_word(3, 12)
            b = _rand_word(3, 12)
            assert prefix_overlap(a, b) == prefix_overlap(a, b)

    def test_chunk_roundtrip_preserves_enders(self):
        rng = random.Random(7)
        for _ in range(50):
            blocks = []
            for _ in range(rng.randint(1, 4)):
                blocks.append(_rand_word(3, 8) + rng.choice(["。", "！", "？", "!", "?"]))
            text = "".join(blocks)
            reblocked = split_sentence_blocks(text)
            # Every ender-terminated block must survive intact.
            assert reblocked == blocks

    def test_hash_dedup_no_false_positives(self):
        rng = random.Random(99)
        seen = {}
        words = [_rand_word(4, 12) for _ in range(50)]
        for w in words:
            assert hash_domain_dedup(w, seen, "rand") is False
        for w in words:
            assert hash_domain_dedup(w, seen, "rand") is True
