# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

"""
Domain Ripple / State Propagation Framework
============================================

"哪些 token 該漣漪/狀態傳遞、哪些不該？"
------------------------------------------
Every domain engine below follows ONE rule, decided from the user's earlier
instruction *「無狀態運算無情緒，有意義的題目/ RPG 屬性才產生認知」*:

  * STATELESS token  → pure arithmetic with no narrative, no question framing,
    and no reference to a *stateful* attribute (RPG stat, physical quantity,
    chemical species). It is COMPUTED and ANSWERED, but produces NO ripple and
    NO emotion/state change. Example: ``917 * 814`` or ``1+1``.
  * MEANINGFUL token → a posed problem, or math/domain computation tied to a
    stateful attribute. It gets (a) a *ripple* (the cognitive structure of the
    operation: amplification, splitting, tension, …) and (b) *bounded
    cognitions* (joy at a correct answer, dampened interest on repeats,
    transient waiting/attending, happiness scaled by a high RPG/domain value).

What "ripple / state propagation" looks like
--------------------------------------------
Each engine emits ``RippleEffect`` dicts with a fixed key schema:

    epsilon_delta   -> ε (数理): logic / complexity / certainty
    alpha_arousal   -> α (生理): arousal
    alpha_tension   -> α (生理): tension
    beta_focus      -> β (认知): focus
    beta_confusion  -> β (认知): confusion
    beta_clarity    -> β (认知): clarity
    gamma_excitement-> γ (情感): happiness        (excitement ≡ happiness here)
    gamma_fear      -> γ (情感): fear
    gamma_surprise  -> γ (情感): surprise
    gamma_sadness   -> γ (情感): sadness
    delta_engagement-> δ (社交): engagement / bond
    overload/fear/confusion -> boolean triggers (negative valence)

``apply_ripple_to_state`` maps every key onto the real StateMatrix4D axis
values (α/β/γ/δ/ε), clamped to [0, 1]. It NEVER writes a key that is not part
of the axis schema, so no spurious dimensions are created.

Value magnitudes are deliberately small and principled (see the constants
block): a single correct answer nudges happiness by ~JOY_ON_CORRECT (≈0.12 of
the [0,1] scale); a high RPG/domain value adds at most ~0.15. All values are
clamped, so emotion can never run away.

Engines
-------
* ``MathDomainEngine``   — arithmetic (wraps MathRippleEngine for ripple shape).
* ``PhysicsDomainEngine``— kinematics/force/energy quantities.
* ``ChemistryDomainEngine``—molar mass + ideal-gas from a chemical formula.

The framework is open: add a subclass of ``DomainRippleEngine`` and register
it in ``DOMAIN_REGISTRY``. ``route_domain(text)`` picks the right engine.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Principled magnitude constants (all on the [0,1] StateMatrix scale)
# ---------------------------------------------------------------------------
JOY_ON_CORRECT = 0.12        # happiness bump for a freshly-solved problem
EXCITEMENT_ON_CORRECT = 0.06  # γ.excitement (== happiness here) secondary bump
WAITING_FOCUS = 0.05          # β.focus while attending / resolving
WAITING_ANTICIPATION = 0.05   # γ.anticipation while attending
REPEAT_FOCUS_PENALTY = 0.15   # β.focus drop on a repeated problem
REPEAT_EXCITE_PENALTY = 0.08  # γ.excitement drop on a repeated problem
REPEAT_CLARITY_PENALTY = 0.05  # β.clarity drop on a repeated problem
NEG_HAPPINESS_PENALTY = 0.10  # γ.happiness drop when the op confused/frightened
NEG_FEAR = 0.20               # γ.fear when the op frightened
NEG_CONFUSION = 0.15          # β.confusion when the op confused
RPG_BOOST_BASE = 0.04         # baseline happiness for a high stateful value
RPG_BOOST_SLOPE = 1.0 / 4000.0  # per-unit scaling of the value
RPG_BOOST_CAP = 0.15          # max extra happiness from a high value


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


# Real StateMatrix4D axis schemas (from core/engine/state_matrix.py). Used so
# we only ever write keys that actually exist on an axis.
_AXIS_SCHEMA = {
    "alpha": {"energy", "comfort", "arousal", "rest_need", "tension"},
    "beta": {"curiosity", "focus", "confusion", "learning", "clarity"},
    "gamma": {
        "happiness", "sadness", "anger", "fear", "disgust",
        "surprise", "trust", "anticipation", "calm",
    },
    "delta": {"attention", "bond", "trust", "presence", "engagement"},
    "epsilon": {"logic", "precision", "abstraction", "certainty", "complexity", "fatigue"},
    "theta": {
        "novelty", "complexity", "ambiguity", "dimension_fit",
        "creation_urge", "theta_negativity", "correction_urge", "audit_intensity",
    },
}


def apply_ripple_to_state(
    state_matrix: Any, ripple: Dict[str, Any], scale: float = 1.0
) -> None:
    """Apply a single ripple dict onto the real StateMatrix4D, fully.

    Unlike the old ``cognitive_pipeline._apply_ripple_to_state`` (which only
    touched arousal / focus / happiness), this applies the ENTIRE ripple schema
    including ε.logic/complexity and the negative-valence triggers (fear /
    confusion / overload). Every write is clamped and validated against the
    axis schema, so no spurious dimension keys are created.
    """
    if not state_matrix or not ripple:
        return

    def _add(axis_name: str, key: str, delta: float) -> None:
        axis = getattr(state_matrix, axis_name, None)
        if axis is None or not hasattr(axis, "values"):
            return
        if key not in _AXIS_SCHEMA.get(axis_name, set()):
            return
        axis.values[key] = _clamp(axis.values.get(key, 0.5) + delta * scale)

    ed = ripple.get("epsilon_delta") or 0.0
    if ed:
        _add("epsilon", "logic", min(ed, 1.0) * 0.10)
        _add("epsilon", "complexity", min(ed, 1.0) * 0.05)

    if ripple.get("alpha_arousal"):
        _add("alpha", "arousal", ripple["alpha_arousal"])
    if ripple.get("alpha_tension"):
        _add("alpha", "tension", ripple["alpha_tension"])

    if ripple.get("beta_focus"):
        _add("beta", "focus", ripple["beta_focus"])
    if ripple.get("beta_confusion"):
        _add("beta", "confusion", ripple["beta_confusion"])
    if ripple.get("beta_clarity"):
        _add("beta", "clarity", ripple["beta_clarity"])

    if ripple.get("gamma_excitement"):
        _add("gamma", "happiness", ripple["gamma_excitement"])
    if ripple.get("gamma_surprise"):
        _add("gamma", "surprise", ripple["gamma_surprise"])
    if ripple.get("gamma_sadness"):
        _add("gamma", "sadness", ripple["gamma_sadness"])

    if ripple.get("delta_engagement"):
        _add("delta", "engagement", ripple["delta_engagement"])
        _add("delta", "bond", ripple["delta_engagement"] * 0.5)

    # --- Negative-valence triggers (real cognitive-affective responses) ---
    if ripple.get("confusion"):
        _add("beta", "confusion", 0.20)
        _add("beta", "clarity", -0.15)
        _add("gamma", "surprise", 0.10)
    if ripple.get("fear"):
        _add("gamma", "fear", 0.30)
        _add("epsilon", "certainty", -0.30)
        _add("alpha", "tension", 0.20)
    if ripple.get("overload"):
        _add("epsilon", "fatigue", 0.20)
        _add("gamma", "surprise", 0.20)
        _add("beta", "focus", -0.20)
        _add("beta", "confusion", 0.30)


class DomainRippleEngine(ABC):
    """Base class for a domain engine that can compute + ripple + cognize.

    Subclasses only need to implement ``domain``, ``attributes``,
    ``can_handle``, ``compute`` and ``make_ripples``. Classification and the
    bounded-cognition deltas are shared.
    """

    domain: str = "generic"
    # Stateful attribute terms that make a computation "meaningful" (RPG stats,
    # physical quantities, chemical species — domain specific).
    attributes: set = set()
    # A numeric value at/above this is considered "high" → extra happiness.
    high_threshold: float = 50.0

    # --- computation -------------------------------------------------------
    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """Return True if this engine owns the given text."""

    @abstractmethod
    def compute(self, text: str) -> Optional[float]:
        """Return the numeric result, or None if not applicable."""

    @abstractmethod
    def make_ripples(self, text: str, value: float) -> List[Dict[str, Any]]:
        """Return domain-specific ripple dicts (see module docstring schema)."""

    # --- shared classification --------------------------------------------
    def classify(self, text: str, value: Optional[float], recent) -> Dict[str, Any]:
        lowered = text.lower()
        words = set(re.findall(r"[a-zA-Z一-鿿]+", lowered))
        attribute = next((w for w in words if w in self.attributes), None)
        is_question = bool(
            re.search(
                r"[？?]|多少|等于|等於|幾|what|how many|calculate|compute|solve|find",
                lowered,
            )
        )
        pure_expr = re.sub(r"[\d\s\+\-\*/%\(\)\^]", "", text).strip()
        is_pure_arithmetic = len(pure_expr) == 0
        # For non-math domains, a computation that names a quantity is meaningful
        # even without an explicit question marker.
        meaningful = bool(attribute) or is_question or (
            self.domain != "math" and value is not None and not is_pure_arithmetic
        )
        is_repetition = text.strip() in (recent or set())
        return {
            "meaningful": meaningful,
            "attribute": attribute,
            "is_question": is_question,
            "is_pure_arithmetic": is_pure_arithmetic,
            "is_repetition": is_repetition,
            "domain": self.domain,
        }

    # --- shared bounded cognition -----------------------------------------
    def cognition_deltas(
        self, cls: Dict[str, Any], value: float, ripples: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Bounded, meaningful-only cognitions. Returns {} for stateless math."""
        if not cls.get("meaningful"):
            return {}

        deltas: Dict[str, float] = {}
        negative = any(
            r.get("fear") or r.get("confusion") or r.get("overload") for r in (ripples or [])
        )

        if negative:
            # Confusing / frightening operation → no joy, mild negative affect.
            deltas["gamma_happiness"] = deltas.get("gamma_happiness", 0.0) - NEG_HAPPINESS_PENALTY
            deltas["gamma_fear"] = NEG_FEAR
            deltas["beta_confusion"] = NEG_CONFUSION
        elif cls.get("is_repetition"):
            # Repeated problem → lower interest / enthusiasm (no joy).
            deltas["beta_focus"] = deltas.get("beta_focus", 0.0) - REPEAT_FOCUS_PENALTY
            deltas["gamma_excitement"] = (
                deltas.get("gamma_excitement", 0.0) - REPEAT_EXCITE_PENALTY
            )
            deltas["beta_clarity"] = deltas.get("beta_clarity", 0.0) - REPEAT_CLARITY_PENALTY
        elif cls.get("is_question"):
            # Freshly solved problem (a posed question) → joy + slight excitement.
            deltas["gamma_happiness"] = deltas.get("gamma_happiness", 0.0) + JOY_ON_CORRECT
            deltas["gamma_excitement"] = (
                deltas.get("gamma_excitement", 0.0) + EXCITEMENT_ON_CORRECT
            )
        # else: meaningful but not a question and not repeated (e.g. a stateful
        # attribute update that is not a "problem to solve") → no joy, only the
        # high-value happiness below + the transient waiting cognition.

        # High stateful value (RPG / domain attribute) → scaled happiness.
        # This is SEPARATE from "joy at solving": a big stat/quantity is happy
        # regardless of whether it was a posed problem.
        if cls.get("attribute") is not None and abs(value) >= self.high_threshold:
            boost = min(RPG_BOOST_CAP, RPG_BOOST_BASE + abs(value) * RPG_BOOST_SLOPE)
            deltas["gamma_happiness"] = deltas.get("gamma_happiness", 0.0) + boost

        # Transient waiting / attending cognition while resolving.
        deltas["beta_focus"] = deltas.get("beta_focus", 0.0) + WAITING_FOCUS
        deltas["gamma_anticipation"] = (
            deltas.get("gamma_anticipation", 0.0) + WAITING_ANTICIPATION
        )
        return deltas


class MathDomainEngine(DomainRippleEngine):
    """Arithmetic domain. Wraps MathRippleEngine for the ripple *shape*."""

    domain = "math"
    attributes = {
        "hp", "mp", "atk", "def", "str", "int", "dex", "lvl", "level",
        "exp", "gold", "sp", "ap",
    }

    def __init__(self, state_matrix=None):
        self.state_matrix = state_matrix
        try:
            from ai.memory.math_ripple_engine import MathRippleEngine

            self._engine = MathRippleEngine(state_matrix=state_matrix)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug("MathDomainEngine: ripple engine unavailable: %s", e)
            self._engine = None

    def can_handle(self, text: str) -> bool:
        from services.math_verifier import compute_arithmetic

        return compute_arithmetic(text) is not None

    def compute(self, text: str) -> Optional[float]:
        from services.math_verifier import compute_arithmetic

        return compute_arithmetic(text)

    def make_ripples(self, text: str, value: float) -> List[Dict[str, Any]]:
        if self._engine is None:
            return []
        try:
            analysis = self._engine.analyze_expression(text, cascade=False)
            return analysis.get("ripples", []) or []
        except Exception as e:  # pragma: no cover - defensive
            logger.debug("MathDomainEngine: ripple analysis failed: %s", e)
            return []


# ---------------------------------------------------------------------------
# Physics domain — real (minimal) kinematics / force / energy quantities.
# ---------------------------------------------------------------------------
_PHYSICS_KEYWORDS = {
    "velocity": "speed", "speed": "speed", "速度": "speed",
    "acceleration": "accel", "加速度": "accel",
    "force": "force", "力": "force",
    "mass": "mass", "質量": "mass",
    "distance": "dist", "displacement": "dist", "距離": "dist", "位移": "dist",
    "time": "time", "時間": "time",
    "energy": "energy", "能量": "energy",
    "momentum": "momentum", "動量": "momentum",
    "pressure": "pressure", "壓力": "pressure", "压强": "pressure",
}


class PhysicsDomainEngine(DomainRippleEngine):
    """Physics domain: a computation that names a physical quantity.

    The numeric value is the embedded arithmetic (computed by MathVerifier);
    the ripple shape is chosen from the dominant physical quantity so that,
    e.g., a force computation tenses the body while a velocity computation
    arouses it.
    """

    domain = "physics"
    attributes = set(_PHYSICS_KEYWORDS.keys())
    high_threshold = 100.0

    def can_handle(self, text: str) -> bool:
        lowered = text.lower()
        has_kw = any(k in lowered for k in _PHYSICS_KEYWORDS)
        has_num = bool(re.search(r"\d", text))
        return has_kw and has_num

    def compute(self, text: str) -> Optional[float]:
        from services.math_verifier import compute_arithmetic

        return compute_arithmetic(text)

    def _dominant_quantity(self, text: str) -> str:
        lowered = text.lower()
        for kw, kind in _PHYSICS_KEYWORDS.items():
            if kw in lowered:
                return kind
        return "speed"

    def make_ripples(self, text: str, value: float) -> List[Dict[str, Any]]:
        kind = self._dominant_quantity(text)
        mag = abs(value)
        ripple: Dict[str, Any] = {"epsilon_delta": min(0.3, 0.05 + mag / 5000.0)}
        if kind in ("speed", "accel"):
            ripple["alpha_arousal"] = min(0.5, 0.1 + mag / 2000.0)
            ripple["gamma_excitement"] = min(0.4, 0.05 + mag / 3000.0)
            ripple["beta_focus"] = 0.15
        elif kind == "force":
            ripple["alpha_tension"] = min(0.5, 0.1 + mag / 2000.0)
            ripple["gamma_fear"] = 0.10
            ripple["beta_focus"] = 0.10
        elif kind in ("energy", "momentum"):
            ripple["gamma_excitement"] = min(0.5, 0.1 + mag / 2000.0)
            ripple["epsilon_delta"] = min(0.4, 0.1 + mag / 3000.0)
        elif kind in ("mass", "dist", "pressure"):
            ripple["epsilon_delta"] = min(0.4, 0.1 + mag / 4000.0)
            ripple["beta_clarity"] = 0.10
        else:  # time
            ripple["beta_clarity"] = 0.15
            ripple["beta_focus"] = 0.05
        return [ripple]


# ---------------------------------------------------------------------------
# Chemistry domain — real (minimal) molar mass + ideal gas from a formula.
# ---------------------------------------------------------------------------
_ATOMIC_WEIGHTS = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81,
    "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180,
    "Na": 22.990, "Mg": 24.305, "Al": 26.982, "Si": 28.085, "P": 30.974,
    "S": 32.06, "Cl": 35.45, "Ar": 39.948, "K": 39.098, "Ca": 40.078,
    "Ti": 47.867, "Cr": 51.996, "Mn": 54.938, "Fe": 55.845, "Ni": 58.693,
    "Cu": 63.546, "Zn": 65.38, "Br": 79.904, "Ag": 107.868, "I": 126.904,
    "Ba": 137.327, "Au": 196.967, "Hg": 200.592, "Pb": 207.2, "U": 238.029,
}
_FORMULA_RE = re.compile(r"([A-Z][a-z]?)(\d*)")
_CHEM_WORDS = {"mol", "mole", "molar", "莫耳", "摩爾", "formula", "化學", "chemical"}


class ChemistryDomainEngine(DomainRippleEngine):
    """Chemistry domain: molar mass + ideal gas from a chemical formula."""

    domain = "chemistry"
    attributes = _CHEM_WORDS
    high_threshold = 100.0  # molar mass (g/mol) considered "large"

    def _parse_formula(self, formula: str) -> Optional[Dict[str, int]]:
        counts: Dict[str, int] = {}
        for sym, num in _FORMULA_RE.findall(formula):
            if sym not in _ATOMIC_WEIGHTS:
                return None
            counts[sym] = counts.get(sym, 0) + (int(num) if num else 1)
        return counts or None

    def _molar_mass(self, formula: str) -> Optional[float]:
        counts = self._parse_formula(formula)
        if not counts:
            return None
        return sum(_ATOMIC_WEIGHTS[s] * n for s, n in counts.items())

    def can_handle(self, text: str) -> bool:
        # Require a valid chemical formula token (all symbols known elements).
        for m in re.finditer(r"(?:[A-Z][a-z]?\d*)+", text):
            if self._parse_formula(m.group(0)):
                return True
        return False

    def compute(self, text: str) -> Optional[float]:
        for m in re.finditer(r"(?:[A-Z][a-z]?\d*)+", text):
            mm = self._molar_mass(m.group(0))
            if mm is not None:
                return mm
        return None

    def make_ripples(self, text: str, value: float) -> List[Dict[str, Any]]:
        # A reaction / transformation → anticipation + learning + mild joy of
        # discovery, and a logic bump on ε.
        return [
            {
                "epsilon_delta": min(0.4, 0.1 + value / 4000.0),
                "beta_learning": 0.15,
                "gamma_anticipation": 0.10,
                "gamma_excitement": 0.08,
            }
        ]


# ---------------------------------------------------------------------------
# Registry + router
# ---------------------------------------------------------------------------
DOMAIN_REGISTRY: List[DomainRippleEngine] = [
    ChemistryDomainEngine(),  # formula detected first (most specific)
    PhysicsDomainEngine(),
    MathDomainEngine(),
]


def route_domain(
    text: str, recent=None
) -> Tuple[Optional[DomainRippleEngine], Optional[float], Dict[str, Any]]:
    """Pick the engine that owns ``text`` and return (engine, value, classify).

    Returns (None, None, {}) when the text is not a domain computation at all
    (e.g. plain chit-chat). ``recent`` is the repetition-tracking collection.
    """
    for engine in DOMAIN_REGISTRY:
        if engine.can_handle(text):
            value = engine.compute(text)
            if value is None:
                continue
            cls = engine.classify(text, value, recent)
            return engine, value, cls
    return None, None, {}
