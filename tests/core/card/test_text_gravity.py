"""E6 — TextGravityField unit tests"""

from core.card.resolver.text_gravity import TextGravityField, _ngram_jaccard_distance


class TestNGramJaccardDistance:

    def test_identical_strings(self):
        d = _ngram_jaccard_distance("abcde", "abcde")
        assert d == 0.0

    def test_completely_different(self):
        d = _ngram_jaccard_distance("abcde", "vwxyz")
        assert d == 1.0

    def test_partial_overlap(self):
        d = _ngram_jaccard_distance("abcde", "abcxy")
        assert 0.0 < d < 1.0

    def test_empty_strings(self):
        d = _ngram_jaccard_distance("", "")
        assert d == 0.0

    def test_one_empty(self):
        d = _ngram_jaccard_distance("abc", "")
        assert d == 1.0


class TestTextGravityField:

    def test_gravity_ranks_by_similarity(self):
        field = TextGravityField()
        scored = field.compute_gravity("務實行動派", ["按計劃執行", "浪漫幻想", "數據分析"])
        assert scored[0][1] >= scored[-1][1]

    def test_empty_candidates_returns_empty(self):
        field = TextGravityField()
        scored = field.compute_gravity("test", [])
        assert len(scored) == 0

    def test_empty_core_trait_returns_zero(self):
        field = TextGravityField()
        scored = field.compute_gravity("", ["a", "b"])
        for _, s in scored:
            assert s == 0.0

    def test_single_candidate(self):
        field = TextGravityField()
        scored = field.compute_gravity("test", ["only"])
        assert len(scored) == 1
        assert scored[0][1] > 0.0

    def test_repulsion_changes_ranking(self):
        field = TextGravityField()
        candidates = ["勇敢前進", "謹慎觀察", "理性分析"]
        first = field.compute_gravity("行動派", candidates)
        second = field.compute_gravity("行動派", candidates)
        first_top = first[0][0]
        second_top = second[0][0]
        assert first_top == "勇敢前進"
        assert second_top != first_top or second[0][1] < first[0][1]

    def test_reset_history_clears_repulsion(self):
        field = TextGravityField()
        candidates = ["A", "B"]
        field.compute_gravity("test", candidates)
        field.reset_history()
        after = field.compute_gravity("test", candidates)
        assert after[0][1] > 0.0

    def test_gravity_score_positive(self):
        field = TextGravityField()
        scored = field.compute_gravity("核心", ["相關", "無關"])
        for _, s in scored:
            assert s >= 0.0

    def test_custom_g_constant(self):
        field = TextGravityField(g=10.0)
        scored = field.compute_gravity("test", ["candidate"])
        assert scored[0][1] > 0.0

    def test_multiple_candidates_ranked(self):
        field = TextGravityField()
        candidates = ["非常相似", "有點相似", "完全不一樣"]
        scored = field.compute_gravity("非常相似", candidates)
        assert scored[0][0] == "非常相似"
