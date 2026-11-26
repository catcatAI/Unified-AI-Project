"""report_intelligence.py 的快取新鮮度契約：不能用過期數字冒充量測。"""

from __future__ import annotations

import os
import time

import pytest

from tests.tools.test_native_dialogue_gates import _load


@pytest.fixture(scope="module")
def report():
    return _load("report_intelligence")


def test_current_caches_are_not_stale(report) -> None:
    """目前工作樹上 --from-cache 的來源都比產生腳本新。"""
    assert report.stale_caches() == []


def test_a_cache_older_than_its_producer_is_stale(report, tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "data" / "intelligence_reports"
    cache_dir.mkdir(parents=True)
    producer = tmp_path / "scripts" / "probe_paraphrase.py"
    producer.parent.mkdir(parents=True)
    producer.write_text("# producer\n")
    cache = cache_dir / "paraphrase.json"
    cache.write_text("{}")
    now = time.time()
    os.utime(producer, (now + 100, now + 100))
    os.utime(cache, (now, now))
    monkeypatch.setattr(report, "REPORT_DIR", cache_dir)
    monkeypatch.setattr(report, "REPO_ROOT", tmp_path)
    assert any("paraphrase" in s for s in report.stale_caches())
