# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""Visual facts — verdicts become recallable claims (2026-10-11).

Seeing without record is not seeing. This bridge turns pipeline outputs
(scan tracks, measurements, adjudications) into GroundedClaims:

- decided + no dissent .... VERIFIED (servable by verified_for recall)
- decided + dissent ........ DISPUTED, lean carried in text (NOT served;
  a disputed count must not be answered as fact)
- abstained ................ VERIFIED unknown-state ("unknown" IS the fact;
  serving "don't know" blocks confabulation downstream)
- deterministic measurements  VERIFIED, worded precisely (region-level is
  region-level — never shaped as person count)

Pure builders (testable) + thin grounding into GroundedKnowledgeStore.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_visual_facts(
    image_id: str,
    scan_result: Dict[str, Any],
    measurements: Dict[str, Any],
    verdicts: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Assemble fact drafts. No store touched (pure)."""
    drafts: List[Dict[str, Any]] = []
    objects = scan_result.get("objects", [])
    residue = scan_result.get("tracks", [])

    # Deterministic measurement facts (pipeline outputs, trustworthy records).
    drafts.append(
        {
            "claim_text": f"{image_id}：掃視{scan_result.get('fixations', 0)}注視，"
            f"物軌{len(objects)}（區域級，非人數），殘留{len(residue)}。",
            "sources": [("visual_memory.scan", f"objects={len(objects)} residue={len(residue)}")],
            "status": "verified",
            "confidence": 1.0,
        }
    )
    if measurements:
        drafts.append(
            {
                "claim_text": f"{image_id}：色塊{measurements.get('blobs', '?')}，"
                f"細節度{measurements.get('detail', '?')}，"
                f"鮮艷{measurements.get('colorfulness', '?')}。"
                f"（量測級，非語義）",
                "sources": [("visual_qa", str(measurements))],
                "status": "verified",
                "confidence": 1.0,
            }
        )
    # Stable-track facts (fixations>=3 only — noise tracks are not facts).
    for track in objects:
        if track.get("fixations", 0) >= 3:
            drafts.append(
                {
                    "claim_text": f"{image_id}：穩定區域{track['id']}（框{track['box']}，"
                    f"主色{track['top_color']}，{track['fixations']}注視）。"
                    f"（區域級，非人物）",
                    "sources": [("visual_memory.track", str(track))],
                    "status": "verified",
                    "confidence": 1.0,
                }
            )

    # Adjudicated semantic verdicts.
    for question, verdict in verdicts.items():
        votes = verdict.get("votes", [])
        srcs = [(f"model:{v}", f"vote={v}") for v in votes]
        if verdict.get("status") == "decided" and not verdict.get("dissent"):
            drafts.append(
                {
                    "claim_text": f"{image_id}：{question}＝{verdict['answer']}。",
                    "sources": srcs,
                    "status": "verified",
                    "confidence": float(verdict.get("agreement", 0.0)),
                }
            )
        elif verdict.get("status") == "decided":
            drafts.append(
                {
                    "claim_text": f"{image_id}：{question}傾向{verdict['answer']}（"
                    f"一致性{verdict.get('agreement')}，分歧{verdict.get('dissent')}）。"
                    f"（有分歧，不可當定論引用）",
                    "sources": srcs,
                    "status": "disputed",
                    "confidence": float(verdict.get("agreement", 0.0)),
                }
            )
        else:
            drafts.append(
                {
                    "claim_text": f"{image_id}：{question}未知（模型分歧"
                    f"{verdict.get('dissent')}，已棄權）。",
                    "sources": srcs,
                    "status": "verified",
                    "confidence": 1.0,
                }
            )
    return drafts


def ground_visual_facts(store: Any, drafts: List[Dict[str, Any]]) -> List[Any]:
    """Write drafts into a GroundedKnowledgeStore (verified-only downstream)."""
    from ai.memory.grounded_knowledge import SourceRef, VerificationStatus

    out = []
    for draft in drafts:
        claim = store.add_or_update(draft["claim_text"], domain="vision")
        store.record_verification(
            claim.claim_key,
            VerificationStatus(draft["status"]),
            sources=[
                SourceRef(url=url, title="visual", snippet=snip) for url, snip in draft["sources"]
            ],
            confidence=draft["confidence"],
        )
        out.append(claim)
    return out
