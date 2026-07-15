"""Lightweight retrieval probe for the Query+Learning dimension score.

Measures dictionary hit-rate on a small known probe set (Chinese->English).
Pure-stdlib-friendly; no heavy ML deps required. Run from repo root:

    python scripts/utils/probe_retrieval.py

Output: PROBE_RESULT (<hits>, <total>) <msg> <seconds>
Used by docs/06-project-management/INTELLIGENCE_ASSESSMENT.md §1.0
(retrieval_hit_rate sub-metric of the Query+Learning dimension).
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src"))

PROBE = [
    ("蘋果", "apple"),
    ("貓", "cat"),
    ("狗", "dog"),
    ("書", "book"),
    ("水", "water"),
    ("天空", "sky"),
    ("星期一", "monday"),
    ("學習", "learn"),
]


def probe_dictionary():
    try:
        from ai.ed3n.dictionary_layer import DictionaryLayer
    except Exception as e:  # pragma: no cover
        return None, "import_failed: %s" % e
    try:
        dl = DictionaryLayer()
    except Exception as e:  # pragma: no cover
        return None, "init_failed: %s" % e
    hits = 0
    total = len(PROBE)
    for zh, en in PROBE:
        try:
            res = dl.lookup(zh) if hasattr(dl, "lookup") else None
        except Exception:
            res = None
        if bool(res):
            hits += 1
    return (hits, total), "dict_hits=%d/%d" % (hits, total)


def main():
    t0 = time.time()
    res, msg = probe_dictionary()
    dt = time.time() - t0
    print("PROBE_RESULT", res, msg, "%.1fs" % dt)


if __name__ == "__main__":
    main()
