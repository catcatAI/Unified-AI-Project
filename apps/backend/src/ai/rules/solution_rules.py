# =============================================================================
# ANGELA-MATRIX: [L3] [β] [A] [L2]
# =============================================================================
"""Solution rule store: verified complex-answer rules, distilled once, replayed.

Pipeline (research 2026-10-18: amortized/FunSearch wide-vs-deep):

1. Admission — `verify_solution()` applies the "easy to evaluate, hard to
   solve" gate: an LLM answer is only stored when its explicit arithmetic
   steps re-evaluate to the claimed values (`evaluate_math` recomputes and
   corrects, so a claimed ``3+5=9`` is caught), its final claim agrees with
   its own steps, and the query is not dynamic (clock/weather/relative-date)
   or echoed back by the answer.
2. Serving — `recall()` matches on `canonical_key()` (NFKC + case + space +
   trailing punctuation only: conservative identity, no paraphrase guessing),
   re-verifies at serve time, and enforces a feedback-driven confidence gate.
3. Feedback — `record_outcome()` feeds success/failure back into the rule's
   confidence: conf = (2 + successes) / (3 + feedback); two failures without
   support drop it below the default 0.5 gate.

The template pool historically refuses unverified auto-fossilization; the
rule store is the verifier-backed counterpart for complex answers.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_MAX_RULES = 500
DEFAULT_MIN_CONFIDENCE = 0.5
MIN_QUERY_LEN = 2
MIN_ANSWER_LEN = 4
MAX_ANSWER_LEN = 600

# Explicit "expr = claimed" fragments inside an answer (ASCII/full-width
# operators and parens; must start with a digit or paren so symbolic
# assignments like "x=5" are never treated as verifiable claims).
_EQ_FRAG_RE = re.compile(r"([（(]?[0-9][0-9+\-*/().%×÷（） ]{0,60}?)\s*[=＝]\s*(-?\d+(?:\.\d+)?)")
_FINAL_CLAIM_RE = re.compile(
    r"(?:答案(?:是|為|为)|结果(?:是|为)|所以(?:答案)?(?:是|为)|answer is)\s*(-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_DYNAMIC_RE = re.compile(
    r"天氣|weather|運勢|fortune|隨機|random|擲|抽籤"
    r"|(?:今天|今日|明天|後天|后天|目前|現在|现在)"
    r".{0,6}(?:幾號|几号|星期|禮拜|礼拜|週[一二三四五六日]?|幾點|几点|日期)",
    re.IGNORECASE,
)
_WS_RE = re.compile(r"\s+")
_TRAILING_PUNCT = " \t?？。！!.,，、;；:：~～…\"'”’」』"


def canonical_key(query: str) -> str:
    """Conservative identity key: NFKC + lowercase + space collapse + trim.

    Numbers and wording are kept — only formatting varies. Two queries share
    a key only when they are the same problem modulo formatting.
    """
    text = unicodedata.normalize("NFKC", query or "")
    text = _WS_RE.sub(" ", text.strip().lower())
    return text.rstrip(_TRAILING_PUNCT)


def is_dynamic_query(query: str) -> bool:
    """True for answers that would go stale (clock/weather/relative date)."""
    return bool(_DYNAMIC_RE.search(unicodedata.normalize("NFKC", query or "")))


def _extract_equations(answer: str) -> List[Tuple[str, float]]:
    """(expr, claimed_value) pairs for every explicit equation in the answer."""
    pairs: List[Tuple[str, float]] = []
    for match in _EQ_FRAG_RE.finditer(answer):
        expr = unicodedata.normalize("NFKC", match.group(1)).strip()
        try:
            claimed = float(match.group(2))
        except ValueError:
            continue
        if expr:
            pairs.append((expr, claimed))
    return pairs


def _verify_equations(equations: List[Tuple[str, float]]) -> Tuple[Optional[List[float]], str]:
    """Recompute every claimed equation; (computed results, 'verified') or (None, reason)."""
    from services.math_verifier import evaluate_math

    results: List[float] = []
    for expr, claimed in equations:
        formatted = evaluate_math(expr)
        if not formatted or "=" not in formatted:
            return None, "math_eval_failed"
        raw_result = formatted.rsplit("=", 1)[1].strip()
        try:
            computed = float(raw_result)
        except ValueError:
            return None, "math_eval_failed"
        if not math.isclose(computed, claimed, rel_tol=1e-9, abs_tol=1e-9):
            logger.debug(
                "solution rule arithmetic mismatch: expr=%r claimed=%s computed=%s",
                expr,
                claimed,
                computed,
            )
            return None, "arithmetic_mismatch"
        results.append(computed)
    return results, "verified"


def _verify_final_claim(answer: str, results: List[float]) -> Optional[str]:
    """Ensure a stated final answer matches one of the verified step results."""
    for claim in _FINAL_CLAIM_RE.findall(answer):
        try:
            value = float(claim)
        except ValueError:
            continue
        if not any(math.isclose(value, r, rel_tol=1e-9, abs_tol=1e-9) for r in results):
            return "final_claim_mismatch"
    return None


def _check_arithmetic(answer: str) -> Tuple[Optional[List[float]], str]:
    """Full arithmetic gate: equations first, then the stated final claim."""
    equations = _extract_equations(answer)
    if not equations:
        return None, "no_equation"
    results, reason = _verify_equations(equations)
    if results is None:
        return None, reason
    claim_reason = _verify_final_claim(answer, results)
    if claim_reason is not None:
        return None, claim_reason
    return results, "verified"


def verify_solution(query: str, answer: str) -> Tuple[bool, str, str]:
    """Gate a (query, answer) pair: (ok, kind, reason). kind='' when rejected."""
    q_text = (query or "").strip()
    a_text = (answer or "").strip()
    if len(q_text) < MIN_QUERY_LEN:
        return False, "", "empty_query"
    if len(a_text) < MIN_ANSWER_LEN:
        return False, "", "answer_too_short"
    if len(a_text) > MAX_ANSWER_LEN:
        return False, "", "answer_too_long"
    if is_dynamic_query(q_text):
        return False, "", "dynamic_query"
    q_key = canonical_key(q_text)
    a_norm = _WS_RE.sub(" ", unicodedata.normalize("NFKC", a_text).lower())
    if len(q_key) >= 8 and q_key in a_norm:
        return False, "", "echo_of_query"
    _, reason = _check_arithmetic(a_text)
    if reason != "verified":
        return False, "", reason
    return True, "math", "arithmetic_verified"


@dataclass
class SolutionRule:
    """One distilled rule: canonical query key → verified answer, verbatim."""

    id: str
    key: str
    query: str
    answer: str
    kind: str
    created_at: float
    last_served_at: float = 0.0
    serves: int = 0
    feedback_count: int = 0
    successes: int = 0

    @property
    def confidence(self) -> float:
        """(2 + successes) / (3 + feedback): 0.67 fresh, 0.5 after one fail."""
        if self.feedback_count <= 0:
            return round((2.0 + self.successes) / 3.0, 4)
        return round((2.0 + self.successes) / (3.0 + self.feedback_count), 4)


class RuleStore:
    """Bounded, persisted store of verified solution rules (thread-safe)."""

    def __init__(
        self,
        path: str,
        max_rules: int = DEFAULT_MAX_RULES,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> None:
        self._path = path
        self._max_rules = max(1, int(max_rules))
        self._min_confidence = float(min_confidence)
        self._lock = threading.Lock()
        self._rules: Dict[str, SolutionRule] = {}
        self._loaded = False

    # ---------- persistence (caller holds the lock) ----------

    def _ensure_loaded_locked(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, encoding="utf-8") as handle:
                payload = json.load(handle)
            for raw in payload.get("rules", []):
                rule = SolutionRule(
                    id=str(raw["id"]),
                    key=str(raw["key"]),
                    query=str(raw.get("query", "")),
                    answer=str(raw["answer"]),
                    kind=str(raw.get("kind", "math")),
                    created_at=float(raw.get("created_at", 0.0)),
                    last_served_at=float(raw.get("last_served_at", 0.0)),
                    serves=int(raw.get("serves", 0)),
                    feedback_count=int(raw.get("feedback_count", 0)),
                    successes=int(raw.get("successes", 0)),
                )
                self._rules[rule.key] = rule
            logger.debug("loaded %d solution rules from %s", len(self._rules), self._path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self._rules = {}
            logger.warning("solution rule store unreadable (%s); starting empty", exc)

    def _save_locked(self) -> None:
        payload = {
            "version": 1,
            "updated_at": time.time(),
            "rules": [asdict(rule) for rule in self._rules.values()],
        }
        try:
            directory = os.path.dirname(self._path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            tmp_path = f"{self._path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=1)
            os.replace(tmp_path, self._path)
        except OSError as exc:
            logger.warning("failed to persist solution rules to %s: %s", self._path, exc)

    def _evict_locked(self) -> None:
        while len(self._rules) > self._max_rules:
            victim = min(
                self._rules.values(),
                key=lambda r: (r.confidence, r.last_served_at or r.created_at),
            )
            del self._rules[victim.key]
            logger.debug("evicted solution rule %s (conf=%.2f)", victim.id, victim.confidence)

    # ---------- public API ----------

    def remember(self, query: str, answer: str) -> Optional[SolutionRule]:
        """Verify and store; returns the rule, or None when not admitted."""
        ok, kind, reason = verify_solution(query, answer)
        if not ok:
            logger.debug("solution rule not admitted (%s): q=%r", reason, (query or "")[:80])
            return None
        key = canonical_key(query)
        if len(key) < MIN_QUERY_LEN:
            return None
        with self._lock:
            self._ensure_loaded_locked()
            existing = self._rules.get(key)
            if existing is not None:
                return existing
            rule = SolutionRule(
                id=uuid.uuid4().hex[:12],
                key=key,
                query=(query or "").strip(),
                answer=(answer or "").strip(),
                kind=kind,
                created_at=time.time(),
            )
            self._rules[key] = rule
            self._evict_locked()
            self._save_locked()
            logger.info("[SolutionRule] admitted kind=%s key=%r", kind, key[:80])
            return rule

    def recall(self, query: str) -> Optional[SolutionRule]:
        """Exact-identity lookup with confidence gate + serve-time re-verify."""
        key = canonical_key(query or "")
        if len(key) < MIN_QUERY_LEN:
            return None
        with self._lock:
            self._ensure_loaded_locked()
            rule = self._rules.get(key)
            if rule is None:
                return None
            if rule.confidence < self._min_confidence:
                logger.debug(
                    "solution rule %s below confidence gate (%.2f)",
                    rule.id,
                    rule.confidence,
                )
                return None
            ok, _, reason = verify_solution(query, rule.answer)
            if not ok:
                logger.warning(
                    "[SolutionRule] serve-time re-verify failed (%s); dropping rule %s",
                    reason,
                    rule.id,
                )
                del self._rules[rule.key]
                self._save_locked()
                return None
            rule.serves += 1
            rule.last_served_at = time.time()
            self._save_locked()
            return rule

    def record_outcome(self, rule_id: str, success: bool) -> bool:
        """Feed serving feedback into the rule's confidence; False if unknown id."""
        with self._lock:
            self._ensure_loaded_locked()
            for rule in self._rules.values():
                if rule.id == rule_id:
                    rule.feedback_count += 1
                    if success:
                        rule.successes += 1
                    self._save_locked()
                    return True
        return False

    def stats(self) -> Dict[str, Any]:
        """Aggregate counters for observability/metrics."""
        with self._lock:
            rules = list(self._rules.values())
        if not rules:
            return {
                "total": 0,
                "serves": 0,
                "feedback": 0,
                "avg_confidence": 0.0,
                "by_kind": {},
            }
        by_kind: Dict[str, int] = {}
        for rule in rules:
            by_kind[rule.kind] = by_kind.get(rule.kind, 0) + 1
        return {
            "total": len(rules),
            "serves": sum(rule.serves for rule in rules),
            "feedback": sum(rule.feedback_count for rule in rules),
            "avg_confidence": round(sum(rule.confidence for rule in rules) / len(rules), 4),
            "by_kind": by_kind,
        }


def _default_rules_path() -> str:
    override = os.environ.get("ANGELA_SOLUTION_RULES_PATH")
    if override:
        return override
    return os.path.join("data", "rules", "solution_rules.json")


_STORE: Optional[RuleStore] = None
_STORE_LOCK = threading.Lock()


def get_rule_store() -> RuleStore:
    """Process-wide singleton store (path overridable via env for tests/ops)."""
    global _STORE
    with _STORE_LOCK:
        if _STORE is None:
            _STORE = RuleStore(path=_default_rules_path())
        return _STORE
