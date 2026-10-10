# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""TaskSplitter — split tasks by CAPABILITY so each piece fits its executor.

Why this exists (measured live 2026-10-10): a monolithic model mixes
thinking, execution and chitchat inseparably — from outside it cannot be
finely separated while keeping long-range coherence. Small executors
(qwen0.5b) NAIL single constrained snippets and fail compound ones; the
thinker (gemma-4-E2B) scaffolds but errs and dies on long gens. The fix is
not a bigger model but SMALLER pieces: decompose until every piece fits a
proven envelope, then dispatch by kind:

- deterministic: math/clock/recall-shaped → solvers/bridges (no LLM).
- micro-act: ONE code artifact with explicit I/O + no-preamble framing →
  executor model (fast, stable).
- think: architecture/multi-constraint synthesis → thinker model.
- verify: compile/run/check → agents (shell/files) or reviewers.

Long-range coherence comes from the shared brief injected into every piece
(goal + decisions so far), not from one giant context. Agent configuration
(mounts/sessions) is derived from the pieces, so the main AI never has to
"deeply split" anything itself — and structured dispatch beats raw direct
invocation (each piece is generatable, verifiable, retryable alone).

Deterministic and stdlib-only: no LLM needed to split.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Proven executor envelope (measured): single deliverable, explicit I/O,
# short prompt. Anything bigger must split further, not "try harder".
_MICRO_MAX_CHARS = 220

_WRITE_VERBS = (
    "寫",
    "写",
    "輸出",
    "输出",
    "生成",
    "產生",
    "产生",
    "給出",
    "给出",
    "給",
    "给",
    "write",
    "generate",
    "give",
    "output",
    "produce",
)

_DELIVERABLE_MARKS = (
    "、",
    "和",
    "跟",
    "以及",
    "還有",
    "还有",
    "再加",
    "另外",
    "、",
    " and ",
    " plus ",
    " with ",
)

# Build verbs (broader than write verbs: 建/造/做 also assemble). Only
# license a compound split together with _CODE_NOUNS below — otherwise
# "做飯、洗碗" would split into nonsense micro-act pieces.
_BUILD_VERBS = (
    "建",
    "創建",
    "创建",
    "造",
    "做",
    "搭建",
    "make",
    "build",
    "create",
)

_CODE_NOUNS = (
    "Cube",
    "Cylinder",
    "Sphere",
    "函數",
    "函数",
    "函式",
    "類",
    "类",
    "方法",
    "method",
    "代碼",
    "代码",
    "腳本",
    "脚本",
    "C#",
    "csharp",
    "python",
    "java",
    "GameObject",
    "MonoBehaviour",
    "Prefab",
    "Scene",
    "場景",
    "场景",
)


@dataclass
class SplitPiece:
    """One executable piece of a split task."""

    piece_id: str
    kind: str  # think | micro-act | deterministic | verify
    prompt: str  # self-contained execution prompt (includes shared brief)
    capability: str  # thinker | executor | solver | agent
    depends_on: List[str] = field(default_factory=list)
    mounts_needed: List[str] = field(default_factory=list)
    budget_tokens: int = 256


@dataclass
class SplitPlan:
    """Decomposition result: pieces + shared brief + required mounts."""

    goal: str
    brief: str
    pieces: List[SplitPiece] = field(default_factory=list)
    mounts_needed: List[str] = field(default_factory=list)

    def ready_pieces(self, done: set) -> List[SplitPiece]:
        """Pieces whose dependencies are all done (execution order)."""
        return [p for p in self.pieces if all(d in done for d in p.depends_on)]


class TaskSplitter:
    """Deterministic capability splitter (no LLM)."""

    def split(self, task: str, context: Optional[Dict[str, Any]] = None) -> SplitPlan:
        """Split a task into capability-tagged pieces."""
        goal = (task or "").strip()
        brief = self._build_brief(goal, context)
        pieces: List[SplitPiece] = []
        mounts: List[str] = []
        if not goal:
            return SplitPlan(goal=goal, brief=brief, pieces=pieces, mounts_needed=mounts)

        deliverables = self._split_deliverables(goal)
        if len(deliverables) > 1:
            # Compound: one micro-act piece per deliverable + verify tail.
            for i, part in enumerate(deliverables, 1):
                pid = f"p{i}"
                pieces.append(
                    SplitPiece(
                        piece_id=pid,
                        kind="micro-act",
                        prompt=self._micro_prompt(brief, part),
                        capability="executor",
                        depends_on=[],
                    )
                )
            pieces.append(
                SplitPiece(
                    piece_id="verify",
                    kind="verify",
                    prompt=self._verify_prompt(brief, goal),
                    capability="agent",
                    depends_on=[p.piece_id for p in pieces],
                    mounts_needed=["shell", "files"],
                )
            )
            mounts = ["shell", "files"]
        elif self._is_code_write(goal):
            pieces.append(
                SplitPiece(
                    piece_id="p1",
                    kind="micro-act",
                    prompt=self._micro_prompt(brief, goal),
                    capability="executor",
                )
            )
            pieces.append(
                SplitPiece(
                    piece_id="verify",
                    kind="verify",
                    prompt=self._verify_prompt(brief, goal),
                    capability="agent",
                    depends_on=["p1"],
                    mounts_needed=["shell", "files"],
                )
            )
            mounts = ["shell", "files"]
        else:
            # Anything else: think first, verify after.
            pieces.append(
                SplitPiece(
                    piece_id="p1",
                    kind="think",
                    prompt=self._think_prompt(brief, goal),
                    capability="thinker",
                    budget_tokens=512,
                )
            )
            pieces.append(
                SplitPiece(
                    piece_id="verify",
                    kind="verify",
                    prompt=self._verify_prompt(brief, goal),
                    capability="agent",
                    depends_on=["p1"],
                    mounts_needed=["shell", "files"],
                )
            )
            mounts = ["shell", "files"]
        return SplitPlan(goal=goal, brief=brief, pieces=pieces, mounts_needed=mounts)

    # -- internals --

    def _build_brief(self, goal: str, context: Optional[Dict[str, Any]]) -> str:
        parts = [f"目標：{goal}"]
        if context:
            decisions = context.get("decisions") or []
            for d in decisions[-5:]:
                parts.append(f"已知：{d}")
        parts.append("約束：每步只交付一件可驗證成果；代碼零前言。")
        return "\n".join(parts)

    def _split_deliverables(self, goal: str) -> List[str]:
        """Split compound goals on deliverable joints (、/和/plus/with).

        A leading write verb propagates to bare tail chunks ("建A、B、C" →
        建A + 建B + 建C); without a leading verb nothing splits ("漢堡和可樂"
        stays whole). Tail chunks must be short noun phrases (≤15 chars) —
        a long tail is a new clause, not a deliverable.
        """
        mark_pattern = "|".join(re.escape(m) for m in _DELIVERABLE_MARKS if m.strip())
        chunks = [c.strip(" ，,、") for c in re.split(mark_pattern, goal) if c.strip(" ，,、")]
        if len(chunks) < 2:
            return [goal]
        first = chunks[0]
        verbs = [v for v in list(_WRITE_VERBS) + list(_BUILD_VERBS) if v in first]
        if not verbs:
            return [goal]
        if not any(n in goal for n in _CODE_NOUNS):
            return [goal]
        verb = max(verbs, key=len)
        out = [first]
        for tail in chunks[1:]:
            if any(v in tail for v in _WRITE_VERBS):
                out.append(tail)
                continue
            # Only CJK core counts toward clause length: bracketed specs,
            # identifiers and numbers (SaveScene存SimpleCarScene) don't make
            # a tail a new clause.
            core = re.sub(r"[（(][^）)]*[）)]", "", tail)
            core = re.sub(r"[^\u4e00-\u9fff]", "", core)
            if len(core) <= 15:
                out.append(verb + tail)
            else:
                return [goal]
        return out

    def _is_code_write(self, goal: str) -> bool:
        try:
            from services.execution.gate_execution import GateExecutionOwner

            return GateExecutionOwner.is_code_write_request(goal)
        except Exception:
            lowered = goal.lower()
            return any(v in lowered for v in _WRITE_VERBS)

    def _micro_prompt(self, brief: str, part: str) -> str:
        part = part.strip()
        if len(part) > _MICRO_MAX_CHARS:
            part = part[:_MICRO_MAX_CHARS]
        # Weak executors drown in context: the full brief degrades them
        # (measured: qwen nails bare micro-tasks, spams with briefed ones).
        # One-line topic anchor only; coherence rides the ledger, not the prompt.
        anchor = ""
        for line in brief.splitlines():
            if line.startswith("目標："):
                anchor = line[:60]
                break
        # Code pieces: weak executors need a singular METHOD shape with no
        # background at all — any context (even one anchor line) flips them
        # into narrating specs instead of writing (measured 3 rounds).
        if any(n in part for n in _CODE_NOUNS):
            return f"只輸出一個完整方法，無前言：{part}"
        head = f"背景：{anchor}\n" if anchor else ""
        return f"{head}只輸出這一件交付物，零前言後語：{part}"

    def _think_prompt(self, brief: str, goal: str) -> str:
        return f"{brief}\n請給出完成該目標的方案要點（分條列出，每條一件交付物）。\n目標：{goal}"

    def _verify_prompt(self, brief: str, goal: str) -> str:
        return (
            f"{brief}\n驗證：檢查上述交付物是否達成目標「{goal}」，"
            "列出不通過項（空即通過）。驗證手段：編譯/運行/文件存在性檢查。"
        )


class SplitRunner:
    """Execute a SplitPlan piece by piece (dependency order, shared ledger).

    Dispatch is injected (think_fn/act_fn/verify_fn) so the runner itself is
    LLM- and transport-free and unit-testable; the live driver wires real
    providers (thinker/executor) and agents. Results feed the shared brief so
    later pieces (and repairs) see earlier outputs — long-range coherence
    without one giant context.
    """

    async def run(
        self,
        plan: SplitPlan,
        think_fn=None,
        act_fn=None,
        verify_fn=None,
    ) -> Dict[str, Any]:
        """Run all pieces; return {results, ledger, ok}."""
        results: Dict[str, str] = {}
        ledger: List[str] = []
        done: set = set()
        pending = list(plan.pieces)
        guard = 0
        while pending and guard < 100:
            guard += 1
            progressed = False
            for piece in list(pending):
                if not all(d in done for d in piece.depends_on):
                    continue
                try:
                    if piece.kind == "think" and think_fn is not None:
                        out = await think_fn(piece.prompt)
                    elif piece.kind == "micro-act" and act_fn is not None:
                        out = await act_fn(piece.prompt)
                    elif piece.kind == "verify" and verify_fn is not None:
                        out = await verify_fn(piece.prompt, dict(results))
                    else:
                        out = f"[skipped:{piece.kind}:no-dispatch]"
                except Exception as exc:
                    out = f"[failed:{piece.piece_id}:{exc}]"
                results[piece.piece_id] = out if isinstance(out, str) else str(out)
                ledger.append(f"{piece.piece_id}({piece.kind}): {results[piece.piece_id][:120]}")
                done.add(piece.piece_id)
                pending.remove(piece)
                progressed = True
            if not progressed:
                break
        return {
            "results": results,
            "ledger": ledger,
            "ok": not pending,
            "unrun": [p.piece_id for p in pending],
        }
