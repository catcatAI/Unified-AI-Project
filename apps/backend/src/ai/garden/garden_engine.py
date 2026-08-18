# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [B] [L2]
# =============================================================================
"""
GARDEN GARDENEngine — Unified reasoning engine for the GARDEN-1G model tier.

Three-stage pipeline:
  1. VectorDictionary.encode(text)  -> concept keys (via cosine similarity)
  2. TensorSNNCore.forward(keys)    -> activated output keys (LIF multi-step)
  3. Anchored decode                -> human-readable response

Additional capabilities:
  - Hormonal modulation passthrough (cortisol/serotonin affect SNN threshold)
  - Continuous learning: learn_from_interaction() grows dictionary and runs Hebbian update
  - Save/load full engine state (dictionary JSON + SNN .pt checkpoint)
  - CLI-friendly stats() method
"""

from __future__ import annotations

import json
import logging
import os
import re
import string
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from ai.core.unicode_utils import is_english_dominant
from ai.data_eng.assemble import decode_slot_budget, select_anchored_keys
from core.system.config.magic_numbers import (
    cache_value,
    confidence_value,
    compute_bool,
    learning_rate,
    limit_value,
    threshold_value,
)
from core.utils import any_keyword

from .dictionary import VectorDictionary
from .snn_core import TensorSNNCore
from .vector_decoder import VectorDecoder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reflex layer (fast pattern table, same design as ED3N)
# ---------------------------------------------------------------------------


class _ReflexTable:
    """O(1) exact-pattern lookup with LRU cache. Triggers before vector encoding."""

    PRESETS: Dict[str, str] = {
        "你好": "你好！很高兴见到你！",
        "早上好": "早上好！祝你今天愉快！",
        "晚上好": "晚上好！祝你今晚愉快！",
        "欢迎": "欢迎！很高兴你能来！",
        "再见": "再见！期待下次见面！",
        "谢谢": "不客气！很高兴能帮到你！",
        "对不起": "没关系，别放在心上。",
        "没关系": "嗯，谢谢你理解！",
        "开心": "开心真好！希望你一直保持好心情！",
        "难过": "别难过，我在这里陪着你。",
        "烦恼": "别烦恼了，我们一起想办法。",
        "在忙吗": "不忙，随时为你服务！",
        "名字": "我是Angela AI，很高兴认识你！",
        "hello": "Hello! Nice to meet you!",
        "hi": "Hi there! How can I help you today?",
        "good morning": "Good morning! Hope you have a great day!",
        "goodbye": "Goodbye! Take care!",
        "thank you": "You're welcome! Happy to help!",
        "help": "I'm here to help! What do you need?",
    }

    def __init__(self, max_cache: Optional[int] = None):
        max_cache = (
            max_cache if max_cache is not None else cache_value("ai.garden.reflex.max_cache", 256)
        )
        self.patterns: Dict[str, str] = dict(self.PRESETS)
        self._cache: Dict[str, str] = {}
        self._max_cache = max_cache

    def match(self, text: str) -> Optional[str]:
        lower = text.strip().lower()
        if lower in self._cache:
            return self._cache[lower]
        for pattern, response in self.patterns.items():
            if pattern in lower:
                if len(self._cache) >= self._max_cache:
                    oldest = next(iter(self._cache))
                    del self._cache[oldest]
                self._cache[lower] = response
                return response
        return None

    def add(self, pattern: str, response: str) -> None:
        self.patterns[pattern.lower().strip()] = response

    def clear(self) -> None:
        """Drop all patterns (used when restoring a saved reflex table)."""
        self.patterns = {}
        self._cache = {}


# ---------------------------------------------------------------------------
# Output anchoring (prevent semantic drift)
# ---------------------------------------------------------------------------


# Decode gate: the minimum SNN activation score an output key needs to be
# decodable (>=1 spike in 6 timesteps ≈ 0.167 with margin). Single source of
# truth for both the anchored-decode filter and the learned-rescue floor, so a
# rescaled learned candidate is exactly at the decodable boundary — not above
# (arbitrary boost) and not below (invisible).
_DECODE_GATE = 0.15


def _slot_budget(n_input: int) -> tuple:
    """Return (anchor_slots, snn_slots) for an input of *n_input* concept keys.

    Single source of truth in ``ai.data_eng.assemble.decode_slot_budget``.
    """
    return decode_slot_budget(n_input)


_TPL_STOPWORDS = frozenset(
    {
        "is", "the", "of", "than", "what", "in", "on", "at", "to", "for",
        "a", "an", "and", "or", "this", "that", "was", "are", "be", "do",
        "does", "did", "with", "from", "by", "it", "its", "as", "not",
    }
)


def _unwrap_brackets(token: str) -> str:
    """Strip one balanced pair of enclosing square brackets.

    ``[Alice]`` -> ``Alice`` (a bracket-wrapped entity is still an entity);
    ``[1,`` / ``5]`` are left intact (unbalanced — fragment of an interval or
    array literal, not a bracketed token).  A bare ``[]`` unwraps to the empty
    string, which keeps it out of number/entity variable detection (it is a
    literal empty-value marker, equivalent by meaning to the SNN's ``[]`` slot).
    """
    if len(token) >= 2 and token[0] == "[" and token[-1] == "]":
        return token[1:-1]
    return token


def _is_number_variable(tok: str) -> bool:
    """True for a standalone numeric token (no bracket fragments).

    ``[1,`` and ``5].`` must NOT count as numbers — they are fragments of an
    interval/array literal whose structure should be preserved verbatim.
    """
    if "[" in tok or "]" in tok:
        return False
    return bool(re.fullmatch(r"\d[\d,.]*", tok.strip(string.punctuation)))


def _is_entity_variable(tok: str, raw: str) -> bool:
    """True for an initial-capped entity token (bracket-wrapped allowed).

    Sentence-initial function words (``The``, ``This``) are excluded so a
    capitalised ordinary word is not mistaken for a slot filler.
    """
    bare = _unwrap_brackets(raw)
    if not bare or not (bare[0].isupper() and bare[0].isalpha()):
        return False
    return bare.strip(string.punctuation).lower() not in _TPL_STOPWORDS


def _extract_template_pair(
    input_text: str, output_text: str
) -> Optional[Tuple[str, str, List[str], List[str]]]:
    """Extract a structural template pair from an (input, output) sample.

    Implements the "dictionary stays a token store, SNN stays a structural
    store" separation: the dictionary holds the concrete concept tokens
    (1, 2, 3, +, =), while the SNN holds the *structure* those tokens fill
    ([] + [] = [], [] is taller than []).  Tokens that play the role of
    fill-in-the-blank variables — pure numbers, initial-capped entities, and
    shared non-stopword tokens appearing on both sides — are replaced with the
    slot marker ``[]``.

    Returns ``(in_tpl, out_tpl, in_vars, out_vars)`` where ``in_tpl`` /
    ``out_tpl`` are space-joined slot skeletons and ``in_vars`` / ``out_vars``
    are the slot filler tokens in order of appearance.  ``None`` when either
    side yields an empty skeleton (nothing structural to learn).
    """
    if not input_text or not output_text:
        return None

    in_raw = input_text.split()
    out_raw = output_text.split()
    in_toks = [t.lower() for t in in_raw]
    out_toks = [t.lower() for t in out_raw]
    in_set, out_set = set(in_toks), set(out_toks)
    shared = in_set & out_set

    variables: set = set()
    for toks, raw in ((in_toks, in_raw), (out_toks, out_raw)):
        for t, r in zip(toks, raw):
            if _is_number_variable(t):
                variables.add(t)
            elif _is_entity_variable(t, r):
                variables.add(t)
    for t in shared:
        # Balanced bracket tokens ([Alice]) may still be entities; unbalanced
        # bracket fragments ([1, / 5].) are interval/array-literal pieces whose
        # structure must be preserved verbatim, never turned into slots.
        if _unwrap_brackets(t) == t and ("[" in t or "]" in t):
            continue
        bare = _unwrap_brackets(t).strip(string.punctuation)
        if bare and bare not in _TPL_STOPWORDS:
            variables.add(t)

    in_tpl = " ".join("[]" if t in variables else t for t in in_toks)
    out_tpl = " ".join("[]" if t in variables else t for t in out_toks)
    # Slot fillers are stored punctuation-stripped so out-slot -> in-slot
    # mapping aligns ("bob." vs "bob" would otherwise never match).
    in_vars = [t.strip(string.punctuation) for t in in_toks if t in variables]
    out_vars = [t.strip(string.punctuation) for t in out_toks if t in variables]

    if not in_tpl.strip() or not out_tpl.strip():
        return None
    return in_tpl, out_tpl, in_vars, out_vars


def _fill_template(
    out_tpl: str, slot_map: Dict[int, int], in_vars: List[str]
) -> str:
    """Fill an output template's slots from the input's slot fillers.

    ``slot_map`` maps an output-slot index -> input-slot index (e.g. the
    "Alice is taller than Bob -> Bob is shorter than Alice" reversal stores
    out slot 0 <- in slot 1, out slot 1 <- in slot 0).  Unmapped slots stay
    ``[]``.
    """
    pieces = out_tpl.split(" ")
    out_idx = 0
    out: List[str] = []
    for piece in pieces:
        if piece == "[]":
            src = slot_map.get(out_idx)
            out.append(in_vars[src] if src is not None and src < len(in_vars) else "[]")
            out_idx += 1
        else:
            out.append(piece)
    return " ".join(out)


def _extract_query_template(input_text: str) -> Optional[Tuple[str, List[str]]]:
    """Extract the structural skeleton of a *query* (input only).

    The query-side counterpart of ``_extract_template_pair``: variables are
    the initial-capped entities and pure numbers (shared-with-output detection
    is impossible without a reference output), everything else stays as fixed
    structure.  Returns ``(tpl, vars_in_order)`` or ``None`` when the query
    yields no structural skeleton.
    """
    if not input_text:
        return None
    raw = input_text.split()
    toks = [t.lower() for t in raw]
    variables: set = set()
    for t, r in zip(toks, raw):
        if _is_number_variable(t):
            variables.add(t)
        elif _is_entity_variable(t, r):
            variables.add(t)
    tpl = " ".join("[]" if t in variables else t for t in toks)
    if not tpl.strip():
        return None
    return tpl, [t.strip(string.punctuation) for t in toks if t in variables]


def _anchored_decode(
    network_output: Dict[str, float],
    input_keys: Dict[str, float],
    dictionary: VectorDictionary,
    top_k: Optional[int] = None,
    original_text: Optional[str] = None,
) -> str:
    """
    Combine highest-scored SNN output keys with top anchor input keys,
    then decode to text.  Anchoring prevents the response from drifting
    entirely away from the user's original intent.

    Selection policy lives in ``ai.data_eng.assemble.select_anchored_keys``
    (single canonical anchor-first + deduped-SNN-keys rule shared with ED3N).
    """
    if not network_output and not input_keys:
        return ""

    combined = select_anchored_keys(network_output, input_keys, decode_gate=_DECODE_GATE)
    return dictionary.decode(combined, original_text=original_text)


# ---------------------------------------------------------------------------
# Module-level deterministic-engine helpers
# Shared by GARDENEngine (defense-in-depth) and the training pipeline
# (single-pass filtering for both ED3N and GARDEN).
# Each function delegates to its respective deterministic subsystem.
# ---------------------------------------------------------------------------


def _try_math(text: str) -> Optional[str]:
    """Evaluate math expression via VectorDictionary route_math."""
    try:
        return VectorDictionary.route_math(text)
    except Exception as e:
        logger.debug("GARDEN: math routing failed for %r: %s", text, e)
        return None


def _try_logic(text: str) -> Optional[str]:
    """Evaluate boolean logic via MathVerifier."""
    try:
        from services.math_verifier import evaluate_logic

        return evaluate_logic(text)
    except Exception as e:
        logger.debug("GARDEN: logic eval failed for %r: %s", text, e)
        return None


def _try_knowledge(text: str) -> Optional[str]:
    """Answer factual question via knowledge base."""
    try:
        from ai.knowledge_base import route_knowledge

        return route_knowledge(text)
    except Exception as e:
        logger.debug("GARDEN: knowledge routing failed for %r: %s", text, e)
        return None


def _try_reasoning(text: str) -> Optional[str]:
    """Apply symbolic reasoning via symbolic_reasoner."""
    try:
        from ai.symbolic_reasoner import route_reasoning

        return route_reasoning(text)
    except Exception as e:
        logger.debug("GARDEN: symbolic reasoning failed for %r: %s", text, e)
        return None


def _try_chain_reasoning(text: str) -> Optional[str]:
    """Resolve relational chain via relational_chain resolver."""
    try:
        from ai.reasoning.relational_chain import (
            parse_and_resolve_relational_chain,
            resolve_relational_chain,
        )

        return parse_and_resolve_relational_chain(text, resolver=resolve_relational_chain)
    except Exception as e:
        logger.debug("GARDEN: chain reasoning failed for %r: %s", text, e)
        return None


def _math_value_matches(engine_output: str, expected: str) -> bool:
    """Value-level match for math results.

    Extracts numbers from both sides and compares with tolerance (1e-4).
    Catches cases like engine ``"784 / 983 = 0.7975584944"`` vs training
    ``"0.7976"`` (different rounding), or engine ``"100 / 4 = 25"`` vs
    training ``"25.0"`` (int vs float representation).

    Uses the number on the RESULT side of engine output (after ``" = "``,
    avoiding operands in number-theory outputs like ``"17 is prime = true"``)
    and checks against EVERY number in expected (to handle
    ``"the answer is 279"``).
    """
    result_part = engine_output.split(" = ", 1)[-1] if " = " in engine_output else engine_output
    eng_nums = re.findall(r"-?\d+(?:\.\d+)?", result_part)
    exp_nums = re.findall(r"-?\d+(?:\.\d+)?", expected)
    if not eng_nums or not exp_nums:
        return False
    eng_val = float(eng_nums[-1])
    for en in exp_nums:
        exp_val = float(en)
        if eng_val == exp_val or abs(eng_val - exp_val) < 1e-2:
            return True
    return False


def _output_matches(
    engine_output: str, expected: str, engine_type: str = "text"
) -> bool:
    """Check if the deterministic engine output matches the expected training output.

    ``engine_type`` controls the comparison strategy:

    * ``"math"`` — value-level comparison with tolerance (catches rounding
      mismatches like ``"0.7975584944"`` vs ``"0.7976"``).
    * ``"logic"`` — boolean comparison (``True`` / ``False``).
    * ``"reasoning"`` — numeric-multiset comparison (structured outputs like
      ``"23 chicken, 12 rabbit"`` vs ``"12 rabbits and 23 chickens"``); falls
      back to ``"text"`` when either side carries no numbers.
    * ``"text"`` — bidirectional substring (handles format variations like
      ``"42"`` inside ``"the answer is 42"``).

    Substring matching (text mode) is only applied when the shorter string
    is at least 2 characters to avoid single-digit false positives.
    """
    eng = engine_output.strip()
    exp = expected.strip()
    if eng == exp:
        return True

    if engine_type == "math":
        return _math_value_matches(eng, exp)

    if engine_type == "logic":
        return eng.lower().strip(".?!;") == exp.lower().strip(".?!;")

    if engine_type == "reasoning":
        eng_nums = re.findall(r"-?\d+", eng)
        exp_nums = re.findall(r"-?\d+", exp)
        if eng_nums and exp_nums:
            return sorted(eng_nums) == sorted(exp_nums)

    # Default (text): bidirectional substring
    short, long = (eng, exp) if len(eng) <= len(exp) else (exp, eng)
    if len(short) >= 2 and short in long:
        return True
    return False


def is_deterministic_match(user_text: str, response_text: str) -> bool:
    """Run all 5 deterministic engines against user_text; return True if any
    produces output that matches response_text.

    When True, the sample is a pure computational fact (math/logic/knowledge/
    reasoning) that the engines already handle correctly.  Training should
    skip this sample — neither ED3N nor GARDEN benefits from learning
    computational facts as associations.
    """
    engines = [
        (_try_math, "math"),
        (_try_logic, "logic"),
        (_try_knowledge, "text"),
        (_try_reasoning, "reasoning"),
        (_try_chain_reasoning, "text"),
    ]
    for fn, etype in engines:
        result = fn(user_text)
        if result is not None and _output_matches(result, response_text, etype):
            record_template_match(user_text, response_text, etype, result)
            return True
    return False


# ---------------------------------------------------------------------------
# TemplateLearner: inverse matching + L0 placeholder for NL reconstruction
# ---------------------------------------------------------------------------
# The idea: when a deterministic engine matches a training sample, we can
# learn which parts of (input, output) are "consumed" by the engine and
# which parts are natural-language wrapping.  At runtime, the engine
# computes the answer and the template reconstructs the full NL sentence.
#
# Template storage keyed by engine_type. Each entry:
#   (input_prefix, input_suffix, output_template)
# where output_template uses {L0_input} (the consumed input expression)
# and {L0_result} (the engine's computed result).
#
# Example: sample ("What is 178 + 101", "What is 178 + 101 = 279")
#   engine → "178 + 101 = 279"
#   expr="178 + 101", result="279"
#   output: "What is {L0_input} = {L0_result}"
#   runtime "What is 55 + 23" → "What is 55 + 23 = 78"

_TEMPLATES: Dict[str, List[Tuple[str, str, str]]] = {}
"""engine_type -> [(input_prefix, input_suffix, output_template)]"""


def _data_region(text: str) -> str:
    """Substring from the first to the last number in ``text``.

    This is the numeric data a deterministic engine consumes (e.g. the
    ``"35 heads and 94 legs"`` span of a chicken-rabbit prompt), or ``""``
    when the text carries no numbers.
    """
    nums = list(re.finditer(r"-?\d+(?:\.\d+)?", text))
    if not nums:
        return ""
    return text[nums[0].start():nums[-1].end()]


def _result_numbers(text: str) -> List[str]:
    """The numbers in an engine result, in order, as strings."""
    return [m.group(0) for m in re.finditer(r"-?\d+(?:\.\d+)?", text)]


def _learn_template(
    sample_input: str,
    sample_output: str,
    engine_type: str,
    engine_result: str,
) -> None:
    """Extract and store a template from a deterministic match.

    Reverse-searches the engine result inside the sample to determine
    which parts are natural-language wrapping.
    """
    input_prefix, input_suffix = "", sample_input

    # Extract expression and result from engine_result
    if engine_type == "math":
        parts = engine_result.split(" = ", 1)
        expr = parts[0].strip() if len(parts) == 2 else ""
        result_val = parts[1].strip() if len(parts) == 2 else engine_result
    elif engine_type == "reasoning":
        # The consumed input is the numeric data region (e.g. "35 heads and
        # 94 legs"); the result numbers are replaced with {R0}, {R1}, ...
        expr = _data_region(sample_input)
        result_val = engine_result.strip()
    else:
        expr = ""
        result_val = engine_result.strip()

    # --- Input side: find where the engine's consumed input appears ---
    if expr and expr in sample_input:
        idx = sample_input.find(expr)
        input_prefix = sample_input[:idx]
        input_suffix = sample_input[idx + len(expr):]
    elif not expr:
        # Non-math engines consume the whole input
        input_prefix, input_suffix = "", ""

    # --- Output side: build output_template with placeholders ---
    output_template = sample_output
    inserted = False

    if engine_type == "reasoning":
        # Replace result numbers in order with {R0}, {R1}, ...
        for i, n in enumerate(_result_numbers(result_val)):
            m = re.search(re.escape(n), output_template)
            if m:
                output_template = output_template[:m.start()] + f"{{R{i}}}" + output_template[m.end():]
                inserted = True
        if expr and expr in output_template:
            output_template = output_template.replace(expr, "{L0_input}", 1)
            inserted = True
    else:
        # Replace result value with {L0_result} in output
        rv = result_val
        if rv in output_template:
            output_template = output_template.replace(rv, "{L0_result}", 1)
            inserted = True
        else:
            # Try finding by numeric value
            nums = re.findall(r"-?\d+(?:\.\d+)?", output_template)
            for n in nums:
                if engine_type == "math":
                    if _math_value_matches(rv, n):
                        output_template = output_template.replace(n, "{L0_result}", 1)
                        inserted = True
                        break

        # Replace input expression with {L0_input} in output (if present)
        if expr and expr in output_template:
            output_template = output_template.replace(expr, "{L0_input}", 1)
            inserted = True

    # Only store if output has NL wrapping beyond bare placeholders AND at
    # least one placeholder was actually substituted (skips garbage templates
    # whose output never referenced the engine result).
    cleaned = output_template.replace("{L0_input}", "").replace("{L0_result}", "")
    cleaned = re.sub(r"\{R\d+\}", "", cleaned).strip()
    if not cleaned or not inserted:
        return

    # Deduplicate: skip if identical template already exists
    entry = (input_prefix, input_suffix, output_template)
    existing = _TEMPLATES.setdefault(engine_type, [])
    if entry not in existing:
        if len(existing) >= 20:
            existing.pop(0)
        existing.append(entry)


def _reconstruct_with_template(
    user_input: str,
    engine_result: str,
    engine_type: str,
) -> str:
    """Apply saved templates to wrap engine_result back into NL.

    Finds a matching template by non-empty input_prefix/suffix, then
    fills {L0_input} and {L0_result} with the current user input's
    consumed expression and the engine's result value.

    Only matches templates where input_prefix or input_suffix is
    non-empty, so generic templates don't accidentally match every input.
    """
    templates = _TEMPLATES.get(engine_type, [])
    if not templates:
        return engine_result

    if engine_type == "math":
        parts = engine_result.split(" = ", 1)
        result_val = parts[1].strip() if len(parts) == 2 else engine_result
    else:
        result_val = engine_result.strip()

    if engine_type == "reasoning":
        result_nums = _result_numbers(engine_result)
        for input_prefix, input_suffix, output_template in templates:
            if not input_prefix and not input_suffix:
                continue
            if user_input.startswith(input_prefix) and user_input.endswith(input_suffix):
                filled = output_template
                for i, n in enumerate(result_nums):
                    filled = filled.replace(f"{{R{i}}}", n, 1)
                if "{L0_input}" in filled:
                    filled = filled.replace("{L0_input}", _data_region(user_input), 1)
                if filled != engine_result:
                    return filled
        return engine_result

    for input_prefix, input_suffix, output_template in templates:
        if not input_prefix and not input_suffix:
            continue
        if user_input.startswith(input_prefix) and user_input.endswith(input_suffix):
            middle = user_input[len(input_prefix):]
            if input_suffix:
                middle = middle[:-len(input_suffix)] if len(input_suffix) else middle
            filled = output_template.replace("{L0_input}", middle).replace("{L0_result}", result_val)
            if filled != engine_result:
                return filled

    return engine_result


def record_template_match(
    sample_input: str,
    sample_output: str,
    engine_type: str,
    engine_result: str,
) -> None:
    """Public entry point for training pipeline to record a template."""
    _learn_template(sample_input, sample_output, engine_type, engine_result)


# ---------------------------------------------------------------------------
# GARDENEngine
# ---------------------------------------------------------------------------


class GARDENEngine:
    """
    GARDEN-1G unified reasoning engine.

    Instantiate and call process(text) to get a response.
    All components (reflex table, vector dictionary, SNN core) are lazy-initialised
    on first use so import time stays fast.

    Example:
        engine = GARDENEngine()
        engine.load_presets()
        reply = engine.process("你好，今天心情怎么样？")
        print(reply)
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        snn_timesteps: Optional[int] = None,
        device: str = "cpu",
        compatibility_mode: bool = False,
    ):
        top_k = top_k if top_k is not None else limit_value("ai.garden.engine.top_k", 8)
        similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else threshold_value("ai.garden.engine.similarity_threshold", 0.30)
        )
        snn_timesteps = (
            snn_timesteps
            if snn_timesteps is not None
            else limit_value("ai.garden.engine.snn_timesteps", 6)
        )
        
        # Use compute config to determine device for SNN
        use_gpu = compute_bool("garden_snn", True)
        if use_gpu:
            if device == "cpu":
                device = "cuda"  # Will be handled by SNN core's dual backend
        else:
            device = "cpu"
        
        self.model_name = model_name
        self.device = device

        self.reflex = _ReflexTable()
        self.dictionary = VectorDictionary(
            model_name=model_name,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            device=device,
            compatibility_mode=compatibility_mode,
        )
        self.snn = TensorSNNCore(timesteps=snn_timesteps, device=device)

        self._presets_loaded = False
        self._query_count = 0
        self._learn_count = 0
        self._learning_enabled = True
        self._last_confidence = 0.0
        self._last_network_output: Dict[str, float] = {}

        # Learned-association recall (composition-layer provenance, bounded).
        # learn_batch/learn_from_interaction record (input-concept set ->
        # output-concept set) here so process() can surface learned output
        # tokens whose Hebbian weight never reaches the SNN spike/decode
        # threshold on a single pass. Cap prevents unbounded growth.
        #
        # Storage is an inverted index over input concepts so retrieval touches
        # only records that share a concept with the query (near-constant)
        # instead of a full linear scan over every stored record.
        self._learned_recall: Dict[int, tuple] = {}
        self._learned_order = deque()
        self._learned_index: Dict[str, set] = {}
        self._learned_next_id = 0
        self._learned_recall_cap = limit_value("ai.garden.engine.learned_recall_cap", 5000)

        # Structural-template store (the SNN's own key space, separate from
        # the dictionary's token keys).  "Dictionary is dictionary, SNN is
        # SNN": the dictionary holds concrete concepts (1, 2, 3, +, =), the
        # SNN holds the structures those tokens fill ([] + [] = []).
        # in_tpl -> (out_tpl, slot_map) pairs learned from samples, plus a
        # sample-count for confidence weighting.
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._templates_cap = limit_value("ai.garden.engine.templates_cap", 500)

    def get_last_network_output(self) -> Dict[str, float]:
        """Return the most recent SNN forward() activation output (writeback source).

        Used by the NeuralBridge to map SNN activations back into the
        StateMatrix axis values, closing the minimal-translation loop.
        """
        return dict(self._last_network_output or {})

    # ------------------------------------------------------------------
    # Preset / init
    # ------------------------------------------------------------------

    def _load_config_reflex_into(self, reflex_table) -> None:
        """Merge reflex patterns from the config/ JSON files into a reflex table.

        Used by ``load()`` to backfill patterns for checkpoints that predate
        reflex persistence, so greeting/canned replies from config always
        survive a checkpoint load.
        """
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        if not os.path.isdir(config_dir):
            return
        for fname in sorted(os.listdir(config_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(config_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for pattern, response in data.get("reflex_patterns", {}).items():
                    if pattern not in reflex_table.patterns:
                        reflex_table.add(pattern, response)
            except Exception as e:
                logger.warning("GARDEN: failed to read config %s: %s", fname, e)

    def load_presets(self) -> None:
        """Load built-in dictionary presets and wire their relations into the SNN.

        Loads in this order:
          1. Hard-coded preset concepts (from dictionary.load_presets())
          2. Config JSON files from the config/ directory (if they exist)
          3. Wire all dictionary relations into the SNN weight matrix
        """
        if self._presets_loaded:
            return
        try:
            self.dictionary.load_presets()
        except Exception as e:
            logger.error("GARDEN: dictionary.load_presets() failed: %s", e, exc_info=True)
            self._presets_loaded = True
            return

        # Also load from config JSON files
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        if os.path.isdir(config_dir):
            loaded_from_config = 0
            for fname in sorted(os.listdir(config_dir)):
                if not fname.endswith(".json"):
                    continue
                fpath = os.path.join(config_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Load reflex patterns
                    for pattern, response in data.get("reflex_patterns", {}).items():
                        self.reflex.add(pattern, response)
                    # Load dictionary entries
                    for entry_data in data.get("dictionary_entries", []):
                        key = entry_data.get("key")
                        if key and key not in self.dictionary.entries:
                            self.dictionary.add_entry(
                                key=key,
                                surface_forms=entry_data.get("surface_forms", {}),
                                relations=entry_data.get("relations"),
                                confidence=entry_data.get(
                                    "confidence",
                                    confidence_value("ai.garden.engine.preset_confidence", 0.9),
                                ),
                            )
                            loaded_from_config += 1
                except Exception as e:
                    logger.warning("GARDEN: failed to load config %s: %s", fname, e)
            if loaded_from_config > 0:
                logger.info(
                    "GARDEN: loaded %d additional concepts from config/", loaded_from_config
                )

        # Collect all unique keys (entries + relation targets) for pre-allocation
        all_keys: set = set(self.dictionary.entries.keys())
        for entry in self.dictionary.entries.values():
            for targets in entry.relations.values():
                all_keys.update(targets)
        self.snn._pre_allocate(list(all_keys))

        # Wire dictionary relations into the SNN weight matrix
        for entry in self.dictionary.entries.values():
            self.snn.add_relations_from_entry(entry.key, entry.relations)
            self.snn._register_key(entry.key)
        self._presets_loaded = True
        logger.info(
            "GARDEN: presets loaded — %d concepts, %d SNN vocab",
            len(self.dictionary.entries),
            self.snn.vocab_size,
        )

    # ------------------------------------------------------------------
    # Core processing pipeline
    # ------------------------------------------------------------------

    def _learn_template(
        self,
        input_text: str,
        output_text: str,
        confidence: float = 1.0,
    ) -> Optional[Tuple[str, str]]:
        """Extract a structural template pair and register it in the SNN.

        This is the "SNN learns structures, not tokens" entry point.  The
        dictionary still owns the concrete tokens; the SNN learns that the
        structure ``[] is taller than []`` maps to ``[] is shorter than []``.

        Registers the template keys in the SNN (auto-registered on first
        Hebbian touch too) and records the (out_tpl, slot_map) pair in the
        engine-side template store.  Returns ``(in_tpl, out_tpl)`` or ``None``.
        """
        pair = _extract_template_pair(input_text, output_text)
        if pair is None:
            return None
        in_tpl, out_tpl, in_vars, out_vars = pair

        # slot_map: output-slot index -> input-slot index.  For the reversal
        # "Alice is taller than Bob -> Bob is shorter than Alice" this is
        # {0: 1, 1: 0} — output slot 0 (Bob) <- input slot 1 (Bob).
        slot_map: Dict[int, int] = {}
        for out_idx, ov in enumerate(out_vars):
            if ov in in_vars:
                slot_map[out_idx] = in_vars.index(ov)

        entry = self._templates.setdefault(
            in_tpl,
            {"out_tpl": out_tpl, "slot_map": slot_map, "samples": 0, "confidence": 0.0},
        )
        entry["samples"] += 1
        n = entry["samples"]
        entry["confidence"] = entry["confidence"] * ((n - 1) / n) + confidence / n
        # If the same in-template produced a different out-template, keep the
        # more-frequent one (structure -> structure is the strongest signal).
        if entry["out_tpl"] != out_tpl and entry["samples"] > 1:
            entry["out_tpl"] = (
                out_tpl if confidence > entry["confidence"] else entry["out_tpl"]
            )

        # Register the template keys into the SNN key space (not the
        # dictionary's token keys — those stay in the dictionary).
        try:
            self.snn._register_key(f"tpl:{in_tpl}")
            self.snn._register_key(f"tpl:{out_tpl}")
        except Exception as e:
            logger.debug("GARDEN: template key registration failed: %s", e)

        # Enforce the template-store cap (FIFO by first-seen).  When a template
        # is evicted, its SNN keys must follow — otherwise the SNN keeps a dead
        # tpl: neuron for every evicted template (unbounded drift, exactly the
        # dict/SNN V divergence the separation forbids).  Only the out-tpl is
        # compacted when it is no longer referenced by any surviving template
        # (multiple in-tpls may share one out-tpl, e.g. taller/older -> X).
        if len(self._templates) > self._templates_cap:
            oldest = next(iter(self._templates))
            evicted_out = self._templates[oldest].get("out_tpl")
            self._templates.pop(oldest, None)
            try:
                orphan_keys = [f"tpl:{oldest}"]
                if evicted_out and evicted_out != oldest and not any(
                    v.get("out_tpl") == evicted_out for v in self._templates.values()
                ):
                    orphan_keys.append(f"tpl:{evicted_out}")
                removed = self.snn.compact_removed_keys(orphan_keys)
                if removed:
                    logger.debug(
                        "GARDEN: compacted %d orphan template keys after FIFO evict", removed
                    )
            except Exception as e:
                logger.debug("GARDEN: template orphan compaction failed: %s", e)

        return in_tpl, out_tpl

    def _learned_slots(
        self, in_tpl: str, in_vars: List[str]
    ) -> List[Tuple[str, Dict[int, int], float]]:
        """Return (out_tpl, slot_map, confidence) candidates for a query template."""
        entry = self._templates.get(in_tpl)
        if entry is None:
            return []
        return [(entry["out_tpl"], entry["slot_map"], entry["confidence"])]

    def _try_template_recall(self, text: str) -> Optional[str]:
        """Structural-template recall for a query.

        Extracts the query's skeleton (``[] is taller than []``), looks up the
        learned output skeleton in the template store, optionally confirms via
        the SNN weight matrix (template -> template Hebbian), and fills the
        output skeleton's slots from the query's entities.  Returns ``None``
        when no learned template matches — the caller falls through to the
        token-level path.
        """
        if not self._templates:
            return None
        query = _extract_query_template(text)
        if query is None:
            return None
        in_tpl, in_vars = query

        candidates = self._learned_slots(in_tpl, in_vars)
        if not candidates:
            return None

        # SNN cross-check: the learned template->template Hebbian weight
        # (>= 0.3) confirms the association isn't a store-only artifact.
        out_tpl, slot_map, _conf = candidates[0]
        try:
            tpl_out = self.snn.forward({f"tpl:{in_tpl}": 1.0})
            snn_conf = tpl_out.get(f"tpl:{out_tpl}", 0.0)
        except Exception as e:
            logger.debug("GARDEN: template SNN cross-check failed: %s", e)
            snn_conf = 0.0

        filled = _fill_template(out_tpl, slot_map, in_vars)
        if not filled or "[]" in filled:
            return None

        # Prefer the SNN-confirmed route; if the Hebbian weight is too weak
        # (single-pass learning rarely reaches 0.3), still surface the
        # engine-side template store with a lower confidence.
        self._last_confidence = 0.85 if snn_conf >= 0.3 else 0.60
        return filled

    def _record_learned(
        self, input_keys: Dict[str, float], output_keys: Dict[str, float]
    ) -> None:
        """Record an input-concept set -> output-concept set in the provenance
        store so process() can surface learned output tokens whose Hebbian
        weight never reaches the SNN/decode threshold on a single pass.

        Bounded to ``_learned_recall_cap`` (FIFO) to prevent unbounded growth.
        Composition-layer bookkeeping; does not touch the dictionary or SNN.

        Storage is an inverted index keyed by input concept: each record gets a
        stable monotonic id, indexed under every concept of its input set. FIFO
        eviction pops the oldest id from the deque and removes only that record's
        concepts from the index (O(concepts-here)), so adds/evicts stay cheap and
        retrieval only ever visits records that actually share a concept.
        """
        if not input_keys or not output_keys:
            return
        rec_id = self._learned_next_id
        self._learned_next_id += 1
        concepts = frozenset(input_keys.keys())
        self._learned_recall[rec_id] = (concepts, dict(output_keys))
        self._learned_order.append(rec_id)
        for c in concepts:
            self._learned_index.setdefault(c, set()).add(rec_id)

        # FIFO eviction: pop the oldest id and drop only its concepts.
        while len(self._learned_recall) > self._learned_recall_cap and self._learned_order:
            old_id = self._learned_order.popleft()
            old_rec = self._learned_recall.pop(old_id, None)
            if old_rec is None:
                continue
            for c in old_rec[0]:
                slot = self._learned_index.get(c)
                if slot is not None:
                    slot.discard(old_id)
                    if not slot:
                        self._learned_index.pop(c, None)

    def _retrieval_targets(
        self,
        input_keys: Dict[str, float],
        slots: Optional[int] = None,
    ) -> Dict[str, float]:
        """Return the strongest *learned* output targets for the active input.

        Composition-layer calibration (not an SNN/dictionary change): single-pass
        Hebbian writes weights ~0.02-0.03, far under the spike threshold (0.30)
        and decode gate (0.15), and W mixes those with near-full preset weights,
        so ``forward()`` never surfaces one-shot learned output. This rescues
        learned output candidates from the engine-side provenance store
        (recorded by learn_batch/learn_from_interaction), scored by how much the
        stored input set overlaps the current input.

        ``slots`` is the SNN slot budget the decoder can place for the current
        input (from ``_slot_budget``); the returned candidate count is capped by
        it so we never gather more than the decoder can use.

        Uses the inverted index: candidate records are the union of the index
        buckets for the query's input concepts, so cost is proportional to
        matching overlap — not to total stored records (was a full linear scan).
        """
        if not input_keys or not self._learned_recall:
            return {}
        slots = slots if slots is not None and slots > 0 else 3
        input_set = set(input_keys.keys())

        # Candidate record ids = union of the index buckets for input concepts.
        cand_ids: set = set()
        for c in input_set:
            cand_ids |= self._learned_index.get(c, set())

        acc: Dict[str, float] = {}
        for rec_id in cand_ids:
            rec = self._learned_recall.get(rec_id)
            if rec is None:
                continue
            in_set, out_keys = rec
            overlap = in_set & input_set
            if not overlap:
                continue
            # Overlap-weighted: shared concepts -> stronger learned target.
            w = len(overlap) / max(1.0, len(in_set))
            for k, v in out_keys.items():
                if k in input_set:
                    continue
                sc = v * (0.5 + 0.5 * w)
                if sc > acc.get(k, 0.0):
                    acc[k] = sc
        if not acc:
            return {}
        ranked = sorted(acc.items(), key=lambda kv: -kv[1])[:slots]
        return dict(ranked)

    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Full GARDEN inference pipeline:
          emotion detect → reflex → multi-step check → vector encode → SNN forward → anchored decode
        """
        if not text or not isinstance(text, str):
            self._last_confidence = 0.0
            return ""

        self._query_count += 1

        # Stage 0: Emotion detection + hormonal modulation
        emotion = self._detect_emotion(text)
        self._adjust_hormones(emotion)

        # Stage 1: High-precision structural answers (math + symbolic reasoning).
        # These run BEFORE the reflex stage so that structurally-answerable
        # questions (e.g. "Which is heavier: 1kg of feathers or 1kg of steel?")
        # are not hijacked by an over-broad reflexive greeting pattern.
        math_result = self._try_math_eval(text)
        if math_result is not None:
            self._last_confidence = 0.85
            return _reconstruct_with_template(text, math_result, "math")

        logic_result = self._try_logic_eval(text)
        if logic_result is not None:
            self._last_confidence = 0.85
            return _reconstruct_with_template(text, logic_result, "logic")

        reasoning_result = self._try_reasoning(text)
        if reasoning_result is not None:
            self._last_confidence = 0.85
            return _reconstruct_with_template(text, reasoning_result, "reasoning")

        # Stage 1.6a: Structural template recall (SNN layer, separate key space
        # from the dictionary).  The dictionary owns concrete tokens; the SNN
        # owns the structures those tokens fill.  If the query's skeleton was
        # learned (e.g. "[] is taller than []"), the SNN fires the paired
        # output skeleton and the slot fillers from the query are substituted
        # back in — pure structure, no token-key mirroring into the SNN.
        # Runs before relational-chain so a learned comparison reversal (taller
        # -> shorter) is not swallowed by the offline graph resolver (which
        # would mis-answer a single comparison as "the greatest").
        template_answer = self._try_template_recall(text)
        if template_answer is not None:
            self._last_confidence = 0.85
            return template_answer

        # Stage 1.6b: Relational-chain reasoning (offline graph derivation).
        # Catches relational comparison questions the symbolic reasoner's regex
        # patterns miss (novel comparators / longer chains / paraphrases) by
        # building a transient directed graph from the stated comparisons and
        # resolving it via transitive closure. No LLM or torch dependency.
        chain_result = self._try_chain_reasoning(text)
        if chain_result is not None:
            self._last_confidence = 0.85
            return _reconstruct_with_template(text, chain_result, "text")

        # Stage 2: Reflex (fast pattern match) — greetings / canned replies.
        reflex_hit = self.reflex.match(text)
        if reflex_hit is not None:
            self._last_confidence = 0.95
            return reflex_hit

        # Stage 3: Knowledge retrieval (deterministic KB, like math)
        kb_result = self._try_knowledge(text)
        if kb_result is not None:
            self._last_confidence = 0.80
            return _reconstruct_with_template(text, kb_result, "text")

        # Stage 4: Multi-step detection
        if self._is_multi_step(text):
            self._last_confidence = 0.70
            return self._process_multi_step(text, context)

        # Stage 5: Vector encode
        if not self._presets_loaded:
            self.load_presets()

        input_keys = self.dictionary.encode(text)

        if not input_keys:
            self._last_confidence = 0.0
            return self._fallback_str(text)

        # Stage 6: SNN forward
        network_output = self.snn.forward(input_keys, context=context)
        self._last_network_output = network_output

        # Stage 6.5: Anchor calibration — single-pass Hebbian weights never
        # reach the SNN spike/decode threshold, so forward() alone never
        # surfaces one-shot learned associations (presets, at 0.5-0.9, dominate
        # top-k). Recover learned output targets from the engine-side
        # provenance store (input-concept overlap, no preset mixing) and merge
        # them at a decodable magnitude so the neural layer's learned
        # associations actually surface. Inert when nothing was learned for the
        # active input.
        rescue = self._retrieval_targets(
            input_keys, slots=_slot_budget(len(input_keys))[1]
        )
        if rescue:
            w_max = max(rescue.values())
            for k, w in rescue.items():
                # Rescale into the decodable band [gate, 1]: the floor is the
                # decode gate itself (a candidate is visible iff >= gate), so
                # the strongest learned target maps to 1.0 and the weakest to
                # exactly gate — monotone, non-arbitrary.
                scaled = _DECODE_GATE + (1.0 - _DECODE_GATE) * (w / w_max)
                if scaled > network_output.get(k, 0.0):
                    network_output[k] = scaled
            self._last_network_output = network_output

        # Stage 7: Anchored decode
        response = _anchored_decode(network_output, input_keys, self.dictionary, original_text=text)

        if not response:
            # Fallback: decode input keys directly
            fallback_keys = list(input_keys.keys())[: limit_value("ai.garden.engine.fallback_decode_keys", 4)]
            response = self.dictionary.decode(
                fallback_keys,
                original_text=text,
            )

        if not response:
            self._last_confidence = 0.0
            return self._fallback_str(text)

        # Stage 6: Cycling — iterative refinement if response is weak
        MAX_CYCLES = getattr(self, "max_cycles", 3)
        MIN_RESPONSE_LEN = 5
        current_output = response
        cycles_used = 0

        for cycle in range(MAX_CYCLES):
            if len(current_output) >= MIN_RESPONSE_LEN:
                break
            cycles_used += 1

            # Re-run with previous output as context
            cycle_context = dict(context) if context else {}
            cycle_context["previous_output"] = current_output
            cycle_context["cycle"] = cycle + 1

            cycle_network = self.snn.forward(input_keys, context=cycle_context)
            cycle_response = _anchored_decode(cycle_network, input_keys, self.dictionary, original_text=text)

            if cycle_response and len(cycle_response) > len(current_output):
                current_output = cycle_response

        # Compute confidence: key coverage × response quality × cycle penalty
        key_ratio = min(1.0, len(input_keys) / limit_value("ai.garden.engine.top_k", 8))
        resp_quality = min(1.0, len(current_output) / 50.0)
        cycle_penalty = 1.0 - (cycles_used * 0.1)
        self._last_confidence = round(
            max(0.0, key_ratio * 0.5 + resp_quality * 0.3 + 0.2 * cycle_penalty), 3
        )

        return current_output

    # ------------------------------------------------------------------
    # Multi-step reasoning (Phase 4.3)
    # ------------------------------------------------------------------

    _MULTI_STEP_MARKERS = [
        "然后",
        "然後",
        "接著",
        "接着",
        "之後",
        "之后",
        "然后再",
        "然後再",
        "and then",
        "after that",
    ]

    def _is_multi_step(self, text: str) -> bool:
        """Detect if the input contains multiple sequential steps."""
        lower = text.lower()
        return any_keyword(lower, tuple(self._MULTI_STEP_MARKERS))

    def _process_multi_step(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Split multi-step input and process each step sequentially."""
        sorted_markers = sorted(self._MULTI_STEP_MARKERS, key=len, reverse=True)
        pattern = "|".join(re.escape(m) for m in sorted_markers)
        steps = re.split(pattern, text, flags=re.IGNORECASE)
        results = []
        for step in steps:
            step = step.strip()
            if not step:
                continue
            # Process each step through the single-step pipeline
            result = self._single_step_process(step, context)
            if result:
                results.append(result)
        return "\n".join(results) if results else self._fallback_str(text)

    def _single_step_process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a single step through the GARDEN pipeline."""
        # Reflex check
        reflex_hit = self.reflex.match(text)
        if reflex_hit is not None:
            return reflex_hit

        # Vector encode + SNN + decode
        if not self._presets_loaded:
            self.load_presets()

        input_keys = self.dictionary.encode(text)
        if not input_keys:
            return ""

        network_output = self.snn.forward(input_keys, context=context)
        response = _anchored_decode(network_output, input_keys, self.dictionary, original_text=text)

        if not response:
            response = self.dictionary.decode(
                list(input_keys.keys())[: limit_value("ai.garden.engine.fallback_decode_keys", 4)],
                original_text=text,
            )

        return response or ""

    # ------------------------------------------------------------------
    # Emotion detection + hormonal modulation (Phase 4.4)
    # ------------------------------------------------------------------

    _EMOTION_KEYWORDS: Dict[str, List[str]] = {
        "happy": [
            "开心",
            "高兴",
            "太好了",
            "happy",
            "great",
            "好开心",
            "好高兴",
            "開心",
            "高興",
            "好開心",
            "好高興",
        ],
        "sad": [
            "难过",
            "伤心",
            "糟糕",
            "sad",
            "bad",
            "好难过",
            "好伤心",
            "難過",
            "傷心",
            "好難過",
            "好傷心",
        ],
        "angry": ["生气", "气死", "烦", "angry", "mad", "好生气", "生氣", "氣死", "好生氣"],
        "anxious": [
            "担心",
            "紧张",
            "害怕",
            "worried",
            "anxious",
            "好担心",
            "擔心",
            "緊張",
            "害怕",
            "好擔心",
        ],
    }

    _HORMONE_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
        "happy": {"serotonin": 0.8, "dopamine": 0.7},
        "sad": {"serotonin": 0.3, "cortisol": 0.6},
        "angry": {"cortisol": 0.8, "adrenaline": 0.7},
        "anxious": {"cortisol": 0.7, "adrenaline": 0.6},
        "neutral": {"serotonin": 0.5, "cortisol": 0.3},
    }

    def _detect_emotion(self, text: str) -> str:
        """Detect the dominant emotion in user input."""
        lower = text.lower()
        for emotion, keywords in self._EMOTION_KEYWORDS.items():
            if any_keyword(lower, tuple(keywords)):
                return emotion
        return "neutral"

    def _adjust_hormones(self, emotion: str) -> None:
        """Adjust hormone levels based on detected emotion."""
        adjustments = self._HORMONE_ADJUSTMENTS.get(emotion, {})
        for hormone, level in adjustments.items():
            self.set_hormone(hormone, level)

    def _try_math_eval(self, text: str) -> Optional[str]:
        return _try_math(text)

    def _try_logic_eval(self, text: str) -> Optional[str]:
        return _try_logic(text)

    def _try_knowledge(self, text: str) -> Optional[str]:
        return _try_knowledge(text)

    def _try_reasoning(self, text: str) -> Optional[str]:
        return _try_reasoning(text)

    def _try_chain_reasoning(self, text: str) -> Optional[str]:
        return _try_chain_reasoning(text)

    def _is_deterministic_match(self, user_text: str, response_text: str) -> bool:
        """Return True when a deterministic engine already handles this query.

        Delegates to the shared module-level ``is_deterministic_match()`` so
        the pipeline can also call it directly for pre-filtering.
        """
        return is_deterministic_match(user_text, response_text)

    # ------------------------------------------------------------------
    # VectorDecoder (iterative generation)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_str(text: str) -> str:
        """Return language-appropriate fallback message."""
        if is_english_dominant(text):
            return "Sorry, I couldn't understand what you meant."
        return "抱歉，我暂时无法理解你的意思。"

    @property
    def vector_decoder(self) -> VectorDecoder:
        if not hasattr(self, "_vector_decoder"):
            self._vector_decoder = VectorDecoder(
                dictionary=self.dictionary,
                snn=self.snn,
            )
        return self._vector_decoder

    def generate(
        self,
        input_text: str,
        temperature: Optional[float] = None,
        max_steps: Optional[int] = None,
    ) -> str:
        return self.vector_decoder.generate_text(
            input_text, temperature=temperature, max_steps=max_steps
        )

    # ------------------------------------------------------------------
    # Continuous learning
    # ------------------------------------------------------------------

    def learn_from_interaction(
        self,
        user_text: str,
        response_text: str,
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Online learning from a single interaction.
        1. Detect and grow new concepts in the dictionary (from both user and response text)
        2. Run Hebbian weight update in SNN between input and response keys
        Returns a summary dict.
        """
        if not self._learning_enabled:
            return {
                "interaction": self._learn_count,
                "new_concepts": [],
                "input_keys": [],
                "output_keys": [],
                "hebbian_delta": 0.0,
            }

        # If a deterministic engine already handles this input, skip learning
        if self._is_deterministic_match(user_text, response_text):
            return {
                "interaction": self._learn_count,
                "new_concepts": [],
                "input_keys": [],
                "output_keys": [],
                "hebbian_delta": 0.0,
                "engine_handled": True,
            }

        confidence = (
            confidence
            if confidence is not None
            else confidence_value("ai.garden.engine.learn_confidence", 0.7)
        )
        if not self._presets_loaded:
            self.load_presets()

        self._learn_count += 1

        new_keys: List[str] = []

        # Grow dictionary with novel concepts from user text
        all_tokens = []
        for text in [user_text, response_text]:
            tokens = [
                t
                for t in text.lower().split()
                if len(t) >= limit_value("ai.garden.engine.min_token_length", 3)
            ]
            all_tokens.extend(tokens)

        # Clean punctuation from tokens
        cleaned_tokens = []
        for token in all_tokens:
            cleaned = token.strip(string.punctuation)
            if cleaned and len(cleaned) >= limit_value("ai.garden.engine.min_token_length", 3):
                cleaned_tokens.append(cleaned)

        # Batch grow - don't rebuild index until all tokens processed
        for token in cleaned_tokens:
            existing = self.dictionary._find_similar_key(
                token, threshold=threshold_value("ai.garden.engine.dedup_similarity", 0.90)
            )
            if not existing and confidence >= self.dictionary.growth_threshold:
                new_key = self.dictionary.grow(token, token, confidence=confidence)
                if new_key:
                    new_keys.append(new_key)

        # Structural learning: the dictionary grows tokens, the SNN learns the
        # STRUCTURE those tokens fill.  Template keys live in the SNN's own key
        # space (tpl:...) — dictionary token keys are NOT mirrored into the SNN.
        self._learn_template(user_text, response_text, confidence=confidence)

        # Only rebuild index ONCE after all grows, not per token
        if new_keys and self.dictionary._dirty:
            self.dictionary._rebuild_index()

        # Compute input/output keys
        input_keys = self.dictionary.encode(user_text)
        output_keys = self.dictionary.encode(response_text)
        self._record_learned(input_keys, output_keys)

        # Hebbian update
        delta = 0.0
        if input_keys and output_keys:
            delta = self.snn.hebbian_update(
                input_keys,
                output_keys,
                lr=learning_rate("ai.garden.engine.hebbian_lr", 0.05),
                target_strength=confidence_value("ai.garden.engine.hebbian_target_strength", 0.35),
            )

        return {
            "interaction": self._learn_count,
            "new_concepts": new_keys,
            "input_keys": input_keys,
            "output_keys": output_keys,
            "hebbian_delta": round(delta, 6),
        }

    def learn_batch(
        self,
        samples: List[Dict[str, str]],
        confidence: Optional[float] = None,
        train_associations: bool = True,
    ) -> Dict[str, Any]:
        """
        Batch learning from multiple interactions.
        Grows all new concepts first, rebuilds index ONCE, then runs Hebbian updates.
        Much faster than calling learn_from_interaction() in a loop.

        Architectural rule: the SNN learns ASSOCIATIONS (relations between
        concepts), not KNOWLEDGE FACTS. When ``train_associations=False`` the
        Hebbian input->output mirror is skipped, so knowledge facts are stored
        in the dictionary only and are NOT baked into the neural weights (which
        would make the SNN a memorizing AI no different from a normal one).
        """
        if not self._learning_enabled or not samples:
            return {"interaction": self._learn_count, "new_concepts": 0, "samples_processed": 0}

        confidence = (
            confidence
            if confidence is not None
            else confidence_value("ai.garden.engine.learn_confidence", 0.7)
        )
        if not self._presets_loaded:
            self.load_presets()

        # Pre-compute which samples are handled by deterministic engines.
        # Those samples are pure computational facts — skip dictionary growth
        # and Hebbian learning to keep numeric/formula noise out of GARDEN's
        # vocabulary.
        filtered_indices: List[int] = []
        for idx, s in enumerate(samples):
            user_text = s.get("input", "") or ""
            response_text = s.get("output", "") or ""
            if not self._is_deterministic_match(str(user_text), str(response_text)):
                filtered_indices.append(idx)

        if not filtered_indices:
            return {
                "interaction": self._learn_count,
                "new_concepts": 0,
                "samples_processed": len(samples),
                "engine_handled_count": len(samples),
            }

        all_new_keys: List[str] = []
        all_tokens: List[str] = []

        # Stage 1: Collect all tokens from non-engine-handled samples
        for idx in filtered_indices:
            s = samples[idx]
            user_text = s.get("input", "") or ""
            response_text = s.get("output", "") or ""
            if not isinstance(user_text, str) or not isinstance(response_text, str):
                user_text = str(user_text)
                response_text = str(response_text)
            for text in [user_text, response_text]:
                tokens = [
                    t
                    for t in text.lower().split()
                    if len(t) >= limit_value("ai.garden.engine.min_token_length", 3)
                ]
                all_tokens.extend(tokens)

        # Clean punctuation from tokens
        cleaned_tokens = []
        for token in all_tokens:
            cleaned = token.strip(string.punctuation)
            if cleaned and len(cleaned) >= limit_value("ai.garden.engine.min_token_length", 3):
                cleaned_tokens.append(cleaned)

        # Stage 2: Grow new concepts from training data.
        # With prefix dedup (threshold=0.5), word forms share neurons:
        # "happy"/"happiness"/"happier" → same neuron, "glad" → new neuron.
        # V grows proportionally to unique concepts, not word forms.
        seen_tokens: set = set()
        grew_any = False
        for token in cleaned_tokens:
            if token in seen_tokens:
                continue
            seen_tokens.add(token)
            result_key = self.dictionary.grow(token, token, confidence=confidence)
            if result_key and result_key.startswith("l"):
                grew_any = True
                all_new_keys.append(result_key)

        # Stage 2b: Learn STRUCTURES into the SNN.  The dictionary above grows
        # concrete tokens; the SNN learns the structural skeleton each sample
        # fills ([] + [] = [], [] is taller than []).  Dictionary token keys
        # are NOT mirrored into the SNN — the two stay separate key spaces
        # (dictionary is dictionary, SNN is SNN).
        template_pairs: Dict[int, Optional[Tuple[str, str]]] = {}
        for idx in filtered_indices:
            s = samples[idx]
            user_text = s.get("input", "") or ""
            response_text = s.get("output", "") or ""
            template_pairs[idx] = self._learn_template(
                str(user_text), str(response_text), confidence=confidence
            )

        # Stage 2c: Sync SNN with dictionary pruning.  If the dictionary hit
        # its cap and evicted low-value entries, those are dead neurons in the
        # SNN registry — compact them out so V doesn't drift (dict 9,573 vs
        # SNN 20,573 wastes up to 2x matrix memory).
        if getattr(self.dictionary, "drain_pruned_keys", None) is not None:
            pruned = self.dictionary.drain_pruned_keys()
            if pruned:
                try:
                    self.snn.compact_removed_keys(pruned)
                except Exception as e:
                    logger.warning(f"SNN prune compaction failed: {e}", exc_info=True)

        # Stage 3: Rebuild index ONCE after all grows
        if grew_any and self.dictionary._dirty:
            self.dictionary._rebuild_index()

        # Stage 4: Hebbian updates for each non-engine-handled sample.
        # Skipped when train_associations=False (knowledge-only ingestion: the
        # fact lives in the dictionary, the SNN only ever learns associations).
        hebbian_delta = 0.0
        auto_regressive_delta = 0.0
        updates_performed = 0
        if train_associations:
            lr = learning_rate("ai.garden.engine.hebbian_lr", 0.05)
            target_str = confidence_value(
                "ai.garden.engine.hebbian_target_strength", 0.35
            )

            # Batch-level text dedup: identical input/output strings recur a
            # lot inside a batch (common phrases, templates). Encode each
            # unique string ONCE and reuse the key dict across samples —
            # avoids re-running the O(V) TF-IDF query for every occurrence.
            batch_texts: Dict[str, str] = {}
            batch_text_keys: Dict[str, Dict[str, float]] = {}
            for idx in filtered_indices:
                s = samples[idx]
                for field in ("input", "output"):
                    txt = str(s.get(field, "") or "")
                    if txt and txt not in batch_texts:
                        batch_texts[txt] = txt
            for txt in batch_texts:
                batch_text_keys[txt] = self.dictionary.encode(txt)

            for idx in filtered_indices:
                s = samples[idx]
                user_text = str(s.get("input", "") or "")
                response_text = str(s.get("output", "") or "")
                input_keys = batch_text_keys.get(user_text) or {}
                output_keys = batch_text_keys.get(response_text) or {}
                # Token-level provenance (composition layer, NOT the SNN): lets
                # process() recover learned output tokens that never reached
                # the SNN spike threshold.  Dictionary keys never enter the
                # SNN key space from here.
                self._record_learned(input_keys, output_keys)

                # Structural Hebbian: the SNN learns template -> template
                # ([] is taller than [] -> [] is shorter than []).  This is
                # the ONLY weight write for learned data — dictionary token
                # keys are not Hebbian targets (dictionary is dictionary,
                # SNN is SNN).
                tpl_pair = template_pairs.get(idx)
                if tpl_pair is not None:
                    in_tpl, out_tpl = tpl_pair
                    if in_tpl and out_tpl:
                        delta = self.snn.hebbian_update(
                            {f"tpl:{in_tpl}": 1.0},
                            {f"tpl:{out_tpl}": 1.0},
                            lr=lr,
                            target_strength=target_str,
                        )
                        hebbian_delta += delta

                        # Pass 2: Auto-regressive — SNN forward on the input
                        # template, then teach (input + intermediate) ->
                        # output.  Chains template associations so the SNN
                        # learns multi-hop structural reasoning.
                        snn_intermediate = self.snn.forward({f"tpl:{in_tpl}": 1.0})
                        intermediate: Dict[str, float] = {
                            k: v for k, v in snn_intermediate.items()
                            if v > 0.3
                        }
                        if intermediate:
                            combined: Dict[str, float] = dict(intermediate)
                            combined[f"tpl:{in_tpl}"] = 1.0
                            delta_ar = self.snn.hebbian_update(
                                combined,
                                {f"tpl:{out_tpl}": 1.0},
                                lr=lr * 0.5,
                                target_strength=target_str,
                            )
                            auto_regressive_delta += delta_ar

                        updates_performed += 1

                # Periodic global decay every 1000 Hebbian updates
                if updates_performed > 0 and updates_performed % 1000 == 0:
                    self.snn.apply_decay(weight_decay=0.002)

        self._learn_count += len(samples)

        engine_handled = len(samples) - len(filtered_indices)
        return {
            "interaction": self._learn_count,
            "new_concepts": len(all_new_keys),
            "samples_processed": len(filtered_indices),
            "hebbian_delta": round(hebbian_delta, 6),
            "auto_regressive_delta": round(auto_regressive_delta, 6),
            "associations_trained": train_associations,
            "engine_handled_count": engine_handled,
        }

    # ------------------------------------------------------------------
    # Hormonal modulation passthrough
    # ------------------------------------------------------------------

    def set_hormone(self, name: str, value: float) -> None:
        """Update a hormone level that modulates SNN spike threshold."""
        self.snn.modulator.set_hormone(name, value)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        dict_stats = self.dictionary.get_stats()
        snn_stats = self.snn.get_stats()
        return {
            "tier": "GARDEN-1G (Lightweight Local)",
            "query_count": self._query_count,
            "learn_count": self._learn_count,
            "presets_loaded": self._presets_loaded,
            "reflex_patterns": len(self.reflex.patterns),
            "dictionary": dict_stats,
            "snn": snn_stats,
        }

    # ------------------------------------------------------------------
    # Save / load
    # ------------------------------------------------------------------

    def save(self, directory: str) -> None:
        """
        Persist the full engine state to a directory:
          - dictionary.json  — all concept entries
          - snn.pt           — SNN weight matrix + key registry
        """
        os.makedirs(directory, exist_ok=True)
        self.dictionary.export_to_json(os.path.join(directory, "dictionary.json"))
        self.snn.save(os.path.join(directory, "snn.pt"))
        # Save engine metadata
        meta = {
            "tier": "GARDEN-1G",
            "model_name": self.model_name,
            "query_count": self._query_count,
            "learn_count": self._learn_count,
            # Structural-template store (SNN's own key space, separate from
            # the dictionary token keys).  Persisted so template recall
            # survives checkpoint reload.
            "templates": self._templates,
            # Reflex patterns are engine state too: without this, a checkpoint
            # load would silently drop the config-reflex patterns (e.g.
            # "how are you" -> "I'm doing great...") and degrade the learned
            # model to its constructor-time reflex table only.
            "reflex_patterns": dict(self.reflex.patterns),
        }
        with open(os.path.join(directory, "engine_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        logger.info("GARDEN: engine saved to %s", directory)

    def load(self, directory: str) -> None:
        """Load full engine state from a previously saved directory."""
        dict_path = os.path.join(directory, "dictionary.json")
        snn_path = os.path.join(directory, "snn.pt")
        meta_path = os.path.join(directory, "engine_meta.json")

        if os.path.exists(dict_path):
            self.dictionary.import_from_json(dict_path)
        if os.path.exists(snn_path) or os.path.exists(snn_path + ".npy") or os.path.exists(
            snn_path + ".npz"
        ):
            self.snn.load(snn_path)
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._query_count = meta.get("query_count", 0)
            self._learn_count = meta.get("learn_count", 0)
            # Restore the structural-template store (SNN structural layer).
            saved_templates = meta.get("templates")
            if isinstance(saved_templates, dict):
                self._templates = {}
                for in_tpl, entry in saved_templates.items():
                    if not isinstance(entry, dict):
                        continue
                    slot_map = entry.get("slot_map") or {}
                    # JSON serialization stringifies int dict keys — restore.
                    self._templates[in_tpl] = {
                        "out_tpl": entry.get("out_tpl", ""),
                        "slot_map": {
                            int(k) if str(k).lstrip("-").isdigit() else k: v
                            for k, v in slot_map.items()
                        },
                        "samples": int(entry.get("samples", 0)),
                        "confidence": float(entry.get("confidence", 0.0)),
                    }
            # Restore the reflex table saved with the checkpoint. If the
            # checkpoint predates reflex persistence (or stores none), fall
            # back to the config-reflex presets so greeting/canned replies do
            # not silently vanish from the loaded model.
            saved_reflex = meta.get("reflex_patterns")
            if saved_reflex:
                self.reflex.clear()
                for pattern, response in saved_reflex.items():
                    self.reflex.add(pattern, response)
        self._presets_loaded = True
        # Apply updated preset surface forms (adds Arabic numerals, operator symbols)
        self._apply_preset_updates()
        # Merge in any config-reflex patterns that are not already present
        # (covers checkpoints saved before reflex persistence was added).
        self._load_config_reflex_into(self.reflex)
        logger.info("GARDEN: engine loaded from %s", directory)

    def _apply_preset_updates(self) -> None:
        """Update existing preset entries with enriched surface forms.

        This handles the case where a checkpoint was saved before new surface
        forms (e.g., Arabic numerals, operator symbols) were added to presets.
        """
        updates = {
            "m0": {"zh": "零 0", "en": "zero 0"},
            "m1": {"zh": "一 1", "en": "one 1"},
            "m2": {"zh": "二 2", "en": "two 2"},
            "m3": {"zh": "三 3", "en": "three 3"},
            "m4": {"zh": "四 4", "en": "four 4"},
            "m5": {"zh": "五 5", "en": "five 5"},
            "m6": {"zh": "六 6", "en": "six 6"},
            "m7": {"zh": "七 7", "en": "seven 7"},
            "m8": {"zh": "八 8", "en": "eight 8"},
            "m9": {"zh": "九 9", "en": "nine 9"},
            "op1": {"zh": "加", "en": "plus +"},
            "op2": {"zh": "减", "en": "minus -"},
            "op3": {"zh": "乘", "en": "multiply *"},
            "op4": {"zh": "除", "en": "divide /"},
            "op5": {"zh": "等于", "en": "equals ="},
        }
        new_entries = {
            "op6": {"surface_forms": {"zh": "大于", "en": "greater >"}, "relations": {}},
            "op7": {"surface_forms": {"zh": "小于", "en": "less <"}, "relations": {}},
            "op8": {"surface_forms": {"zh": "问号", "en": "question ?"}, "relations": {}},
        }
        for key, forms in updates.items():
            if key in self.dictionary.entries:
                self.dictionary.entries[key].surface_forms = forms
        for key, entry_data in new_entries.items():
            if key not in self.dictionary.entries:
                self.dictionary.add_entry(key=key, **entry_data)
        self.dictionary._dirty = True
        self.dictionary._surface_to_key = None
