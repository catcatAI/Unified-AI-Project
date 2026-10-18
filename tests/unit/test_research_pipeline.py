# -*- coding: utf-8 -*-
"""research_pipeline 單測 — 排序/抽取/矛盾/組答/管線（第二輪研究品質修復）。"""

import pytest


class TestSourceScore:
    def test_wikipedia_high(self):
        from core.tools.research_pipeline import source_score

        score, label = source_score("https://en.wikipedia.org/wiki/Search_engine")
        assert label == "高" and score >= 3

    def test_gov_edu_high(self):
        from core.tools.research_pipeline import source_score

        assert source_score("https://www.nasa.gov/pricing")[1] == "高"
        assert source_score("https://cs.stanford.edu/research")[1] == "高"

    def test_official_docs_path_bonus(self):
        from core.tools.research_pipeline import source_score

        score, label = source_score("https://api.example.com/docs/pricing")
        assert score >= 2 and label == "高"

    def test_youtube_penalized_low(self):
        from core.tools.research_pipeline import source_score

        score, label = source_score("https://www.youtube.com/watch?v=abc")
        assert label == "低" and score <= -4

    def test_config_trusted_extends_defaults(self):
        from core.tools.research_pipeline import source_score

        cfg = {"trusted_domains": ["mycorp.example"]}
        score, label = source_score("https://docs.mycorp.example/api", cfg)
        assert label == "高"

    def test_non_http_rejected(self):
        from core.tools.research_pipeline import source_score

        assert source_score("file:///etc/passwd")[1] == "低"


class TestRankResults:
    def test_trusted_floats_up_stable_within_tie(self):
        from core.tools.research_pipeline import rank_results

        raw = [
            {"title": "seo", "url": "https://randomsite.example/x"},
            {"title": "yt", "url": "https://www.youtube.com/watch?v=1"},
            {"title": "wiki", "url": "https://en.wikipedia.org/wiki/x"},
            {"title": "seo2", "url": "https://othersite.example/y"},
        ]
        ranked = rank_results(raw)
        urls = [r["url"] for r in ranked]
        assert urls[0].endswith("/wiki/x")  # 可信浮頂
        assert urls[-1].endswith("v=1")  # 殼站沉底
        # 同分穩定：randomsite 在 othersite 前（原序保留）
        assert urls[1].endswith("/x") and urls[2].endswith("/y")

    def test_error_entries_dropped_and_trust_annotated(self):
        from core.tools.research_pipeline import rank_results

        ranked = rank_results(
            [
                {"error": "boom"},
                {"title": "t", "url": "https://en.wikipedia.org/wiki/x"},
            ]
        )
        assert len(ranked) == 1
        assert ranked[0]["trust"] == "高"
        assert ranked[0]["trust_score"] >= 3


class TestFactsExtraction:
    def test_query_terms_latin_and_cjk(self):
        from core.tools.research_pipeline import query_terms

        terms = query_terms("DuckDuckGo vs Brave API 免費額度")
        assert "duckduckgo" in terms
        assert "brave" in terms
        assert "api" in terms
        assert any(len(t) == 2 for t in terms)  # CJK 二元組

    def test_english_sentences_extracted(self):
        from core.tools.research_pipeline import extract_facts, query_terms

        text = (
            "The Brave Search API free tier allows 2,000 queries per month. "
            "After removal of free access, paid plans start at 3 USD per thousand. "
            "DuckDuckGo does not offer a public search API at all."
        )
        facts = extract_facts(text, query_terms("Brave Search API free tier"))
        assert facts
        assert any("2,000 queries" in f for f in facts)

    def test_numeric_sentences_score_higher(self):
        from core.tools.research_pipeline import extract_facts, query_terms

        text = (
            "Brave Search API offers generous numbers here. "
            "The Brave Search API free tier is 2,000 queries per month."
        )
        facts = extract_facts(text, query_terms("Brave Search API free tier"), max_facts=1)
        assert "2,000" in facts[0]

    def test_taglike_sentence_rejected(self):
        from core.tools.research_pipeline import extract_facts, query_terms

        text = 'Brave Search <link rel="stylesheet" href="/x.css" integrity="sha256-abc"> tail'
        facts = extract_facts(text, query_terms("Brave Search"))
        assert facts == []

    def test_js_soup_sentence_rejected(self):
        from core.tools.research_pipeline import extract_facts, query_terms

        text = (
            "Brave Search API Pricing , so they run before the first paint. "
            "The Brave Search API free tier includes 2,000 queries per month."
        )
        facts = extract_facts(text, query_terms("Brave Search API free tier"))
        assert len(facts) == 1
        assert "2,000" in facts[0]

    def test_cjk_sentence_extracted(self):
        from core.tools.research_pipeline import extract_facts, query_terms

        text = "氣象局宣布台北今日高溫三十六度。另外一則無關訊息出現。"
        facts = extract_facts(text, query_terms("台北 高溫"))
        assert facts and "三十六度" in facts[0]


class TestConflicts:
    def test_different_numbers_same_unit_flagged(self):
        from core.tools.research_pipeline import find_conflicts, query_terms

        facts = [
            ("The free tier allows 2,000 queries per month.", "a.com"),
            ("The free tier allows 5,000 queries per month.", "b.com"),
        ]
        conflicts = find_conflicts(facts, query_terms("free tier queries"))
        assert conflicts
        assert "2000" in conflicts[0] and "5000" in conflicts[0]

    def test_same_numbers_no_conflict(self):
        from core.tools.research_pipeline import find_conflicts, query_terms

        facts = [
            ("Free tier allows 2,000 queries per month.", "a.com"),
            ("Free tier allows 2,000 queries per month.", "b.com"),
        ]
        assert find_conflicts(facts, query_terms("free tier queries")) == []

    def test_negation_vs_affirmation_flagged(self):
        from core.tools.research_pipeline import find_conflicts, query_terms

        facts = [
            ("Brave Search API removed its free tier in 2026.", "official.com"),
            ("Brave Search API still has a free tier for developers.", "blog.com"),
        ]
        conflicts = find_conflicts(facts, query_terms("Brave Search API free tier"))
        assert conflicts
        assert "矛盾" in conflicts[0]

    def test_no_facts_no_conflicts(self):
        from core.tools.research_pipeline import find_conflicts, query_terms

        assert find_conflicts([], query_terms("anything")) == []


class TestComposeAnswer:
    def test_contract_header_and_sections(self):
        from core.tools.research_pipeline import compose_answer

        out = compose_answer(
            "q1",
            [{"title": "T", "url": "https://x.example/y", "trust": "高"}],
            [("fact one", "x.example")],
            ["數值不一致：1 vs 2"],
            n_fetched=1,
            fetched_k=3,
        )
        assert out.startswith("「q1」的搜尋結果")
        assert "【關鍵事實】" in out and "fact one" in out
        assert "（x.example）" in out  # 溯源標記
        assert "【來源分歧】" in out
        assert "[高] T — https://x.example/y" in out

    def test_no_fetch_degrades_gracefully(self):
        from core.tools.research_pipeline import compose_answer

        out = compose_answer(
            "q2",
            [{"title": "T", "url": "https://x.example/y", "trust": "中"}],
            [],
            [],
            n_fetched=0,
            fetched_k=3,
        )
        assert "未能抓取內文" in out
        assert "https://x.example/y" in out


class TestRunResearchPipeline:
    def _fake_tool(self, results):
        class T:
            def search(self, query, num_results=5):
                return results

        return T()

    def test_full_pipeline_with_fetch(self, monkeypatch):
        import core.tools.research_pipeline as rp

        page = (
            "The Brave Search API free tier allows 2,000 queries per month for developers. "
            "DuckDuckGo has no official public API endpoint documented anywhere."
        )
        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: page)
        r = rp.run_research(
            "Brave Search API free tier",
            tool=self._fake_tool(
                [{"title": "Brave pricing", "url": "https://brave.com/brave/search/api/pricing"}]
            ),
        )
        assert r["ok"] is True
        assert r["n_fetched"] == 1
        assert any("2,000" in f for f in r["facts"])
        assert "【關鍵事實】" in r["answer"]
        assert "brave.com" in r["answer"]

    def test_fetch_failure_falls_back_to_snippet(self, monkeypatch):
        import core.tools.research_pipeline as rp

        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: None)
        r = rp.run_research(
            "Brave Search API free tier",
            tool=self._fake_tool(
                [
                    {
                        "title": "T",
                        "url": "https://x.example/z",
                        "snippet": "The free tier includes 2,000 queries for Brave Search API users.",
                    }
                ]
            ),
        )
        assert r["ok"] is True
        assert r["n_fetched"] == 0
        assert r["facts"]  # snippet 兜底仍有事實
        assert "2,000" in r["answer"]

    def test_empty_results(self):
        import core.tools.research_pipeline as rp

        r = rp.run_research("q", tool=self._fake_tool([]))
        assert r["ok"] is True and r["answer"] == ""

    def test_pricing_reformulation_appends_missing_pricing_source(self, monkeypatch):
        """定價意圖＋pool 無定價頁 → 補「query pricing」；同 URL 不重複。"""
        import core.tools.research_pipeline as rp

        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: None)
        calls = []

        class T:
            def search(self, query, num_results=5):
                calls.append(query)
                if len(calls) == 1:
                    return [
                        {
                            "title": "Compare",
                            "url": "https://a.example/compare",
                            "snippet": "Free tier for Brave Search API includes 2,000 queries monthly.",
                        },
                    ]
                return [
                    {
                        "title": "Pricing",
                        "url": "https://api.example/pricing",
                        "snippet": "Paid plans start at 3 USD per thousand queries for the API.",
                    },
                    {"title": "Compare", "url": "https://a.example/compare"},  # duplicate
                ]

        r = rp.run_research("Brave Search API 免費額度", tool=T())
        assert len(calls) == 2
        assert "pricing" in calls[1]
        urls = [s["url"] for s in r["sources"]]
        assert urls.count("https://a.example/compare") == 1
        assert "https://api.example/pricing" in urls

    def test_no_reformulation_when_pricing_source_present(self, monkeypatch):
        import core.tools.research_pipeline as rp

        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: None)
        calls = []

        class T:
            def search(self, query, num_results=5):
                calls.append(query)
                return [
                    {
                        "title": "Pricing",
                        "url": "https://api.example/pricing",
                        "snippet": "Free tier includes 2,000 queries per month for the API.",
                    },
                ]

        rp.run_research("Brave Search API 免費額度", tool=T())
        assert len(calls) == 1  # 已有定價源 → 不補搜

    def test_no_reformulation_without_pricing_intent(self, monkeypatch):
        import core.tools.research_pipeline as rp

        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: None)
        calls = []

        class T:
            def search(self, query, num_results=5):
                calls.append(query)
                return [{"title": "t", "url": "https://a.example/x"}]

        rp.run_research("台北今天天氣如何", tool=T())
        assert len(calls) == 1

    def test_fetch_targets_deduplicated_by_host(self, monkeypatch):
        """zh/en 同域雙佔額不排擠其他來源——fetch 只抓每 host 首見者。"""
        import core.tools.research_pipeline as rp

        fetched_urls = []

        def fake_fetch(url, *a, **k):
            fetched_urls.append(url)
            return "The free tier includes 2,000 queries per month for Brave Search API users."

        monkeypatch.setattr(rp, "fetch_page_text", fake_fetch)
        r = rp.run_research(
            "Brave Search API free tier",
            tool=self._fake_tool(
                [
                    {"title": "zh", "url": "https://site.example/zh/compare"},
                    {"title": "en", "url": "https://site.example/en/compare"},
                    {"title": "other", "url": "https://other.example/pricing"},
                ]
            ),
        )
        assert r["n_fetched"] == 2
        assert sorted(fetched_urls) == [
            "https://other.example/pricing",
            "https://site.example/zh/compare",
        ]  # 並發抓取順序不保證；en 同域頁不佔 fetch 額

    def test_all_error_results(self):
        import core.tools.research_pipeline as rp

        r = rp.run_research("q", tool=self._fake_tool([{"error": "down"}]))
        assert r["ok"] is False and r["error"] == "down"

    def test_fetch_page_text_junk_page_returns_none(self, monkeypatch):
        import core.tools.research_pipeline as rp

        class FakeResp:
            def read(self, n=-1):
                return b"<html><head><title>x</title></head><body></body></html>"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(rp.urllib.request, "urlopen", lambda req, timeout=8: FakeResp())
        assert rp.fetch_page_text("https://x.example/junk") is None  # < 500B

    def test_fetch_page_text_truncated_tag_cut(self, monkeypatch):
        """read cap 截在半標籤 → 砍最後 `<` 之後（brave 24KB 教訓）。"""
        import core.tools.research_pipeline as rp

        body = ("word " * 60000).encode() + b"<link rel='x' NO_CLOSE"  # >250KB 且尾截標籤

        class FakeResp:
            def read(self, n=-1):
                return body if n is None or n < 0 else body[:n]

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(rp.urllib.request, "urlopen", lambda req, timeout=8: FakeResp())
        text = rp.fetch_page_text("https://x.example/big")
        assert text is not None
        assert "NO_CLOSE" not in text
        assert "<link" not in text
