# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""VisualFacts: verdicts become claims. Only clean ones are servable."""

import pytest
from services.visual_facts import build_visual_facts, ground_visual_facts


def _scan():
    return {
        "fixations": 45,
        "tracks": [{"id": 1}, {"id": 7}],
        "objects": [
            {"id": 1, "fixations": 4, "box": [0, 0, 0.3, 0.3], "top_color": [120, 168, 216]},
            {"id": 2, "fixations": 1, "box": [0.3, 0, 0.4, 0.1], "top_color": [1, 2, 3]},
        ],
    }


def test_unanimous_verdict_becomes_verified():
    drafts = build_visual_facts(
        "img",
        _scan(),
        {},
        {
            "角色數": {
                "status": "decided",
                "answer": 3,
                "agreement": 1.0,
                "dissent": [],
                "votes": [3, 3],
            }
        },
    )
    picked = [d for d in drafts if "角色數" in d["claim_text"]][0]
    assert picked["status"] == "verified"


def test_disputed_verdict_not_servable_as_fact():
    # The 001 count shape: decided lean, live dissent -> DISPUTED text.
    drafts = build_visual_facts(
        "img",
        _scan(),
        {},
        {
            "角色數": {
                "status": "decided",
                "answer": 3,
                "agreement": 0.667,
                "dissent": [4],
                "votes": [3, 3, 4],
            }
        },
    )
    picked = [d for d in drafts if "角色數" in d["claim_text"]][0]
    assert picked["status"] == "disputed"
    assert "4" in picked["claim_text"] and "不可當定論" in picked["claim_text"]


def test_abstention_becomes_verified_unknown():
    drafts = build_visual_facts(
        "img",
        _scan(),
        {},
        {
            "作品": {
                "status": "abstained",
                "answer": None,
                "agreement": 0.5,
                "dissent": ["a", "b"],
                "votes": ["a", "b"],
            }
        },
    )
    picked = [d for d in drafts if "作品" in d["claim_text"]][0]
    assert picked["status"] == "verified" and "未知" in picked["claim_text"]


def test_only_stable_tracks_become_facts():
    drafts = build_visual_facts("img", _scan(), {}, {})
    track_claims = [d for d in drafts if "穩定區域" in d["claim_text"]]
    assert len(track_claims) == 1 and "區域1" in track_claims[0]["claim_text"]


def test_grounding_serves_only_clean():
    from ai.memory.grounded_knowledge import GroundedKnowledgeStore

    store = GroundedKnowledgeStore()
    drafts = build_visual_facts(
        "img",
        _scan(),
        {},
        {
            "角色數": {
                "status": "decided",
                "answer": 3,
                "agreement": 0.667,
                "dissent": [4],
                "votes": [3, 3, 4],
            },
            "作品": {
                "status": "abstained",
                "answer": None,
                "agreement": 0.5,
                "dissent": ["a", "b"],
                "votes": ["a", "b"],
            },
        },
    )
    ground_visual_facts(store, drafts)
    served = store.verified_for("img 角色數 作品")
    texts = " ".join(c.claim_text for c in served)
    assert "未知" in texts  # abstention IS servable (blocks invention)
    assert "傾向3" not in texts  # disputed lean is NOT served as fact
