"""
PriorityNegotiator — Conflict resolution for routing decisions.

Replaces hardcoded priority chains (Priority 1→3.5) with weighted fusion.
Each voter registers a callable that extracts routing preferences from
the generation context. The negotiator fuses all votes using
confidence-weighted categorical voting for routing_mode/response_style
and confidence-weighted averaging for temperature/tokens biases.

Usage:
    negotiator = PriorityNegotiator()
    negotiator.register_voter("lifecycle", lifecycle_voter_fn, weight_fn=lambda ctx: 0.8)
    result = negotiator.resolve(context)
    # result["routing_mode"] = "exploratory"  (mode with highest weighted confidence)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class VoterVote:
    """A single voter's recommendation for routing parameters.

    Attributes:
        routing_mode: Voted routing mode (None = abstain on mode)
        response_style: Voted response style (None = abstain on style)
        temperature_bias: Additive temperature adjustment
        tokens_bias: Additive max_tokens adjustment
        confidence: How confident the voter is in this vote (0.0-1.0)
    """

    routing_mode: Optional[str] = None
    response_style: Optional[str] = None
    temperature_bias: float = 0.0
    tokens_bias: int = 0
    confidence: float = 0.0


class PriorityNegotiator:
    """Weighted fusion of routing preferences from multiple system modules.

    Replaces the Priority 1→3.5 hardcoded chain in router.py with a
    weighted voting system where each module (LifeCycle, Emotion, Intent,
    Causal) registers as a voter. Categorical fields use weighted plurality;
    numeric fields use weighted averaging.
    """

    def __init__(self) -> None:
        self._voters: Dict[str, Callable[[Dict[str, Any]], Optional[VoterVote]]] = {}
        self._weight_fns: Dict[str, Callable[[Dict[str, Any]], float]] = {}

    def register_voter(
        self,
        name: str,
        vote_fn: Callable[[Dict[str, Any]], Optional[VoterVote]],
        weight_fn: Optional[Callable[[Dict[str, Any]], float]] = None,
    ) -> None:
        """Register a voter for routing negotiation.

        Args:
            name: Unique voter identifier (e.g. "lifecycle", "emotion")
            vote_fn: Callable(context) -> Optional[VoterVote]. Return None to abstain.
            weight_fn: Callable(context) -> float. Base voting weight multiplier.
                       Defaults to 1.0 if not provided.
        """
        self._voters[name] = vote_fn
        self._weight_fns[name] = weight_fn or (lambda _ctx: 1.0)

    def unregister_voter(self, name: str) -> bool:
        """Remove a previously registered voter. Returns True if removed."""
        if name in self._voters:
            del self._voters[name]
            del self._weight_fns[name]
            return True
        return False

    def resolve(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fuse all voter preferences into a single routing decision.

        Categorical fields (routing_mode, response_style) use weighted
        plurality: each voter votes for a value with weight = base_weight * confidence.
        The value with the highest total weighted vote wins.

        Numeric fields (temperature_bias, tokens_bias) use weighted averaging
        with confidence as weight.

        Args:
            context: The generation context dict used by router.py.

        Returns:
            Dict with keys:
              - routing_mode: str or None
              - response_style: str or None
              - temperature_bias: float (weighted avg)
              - tokens_bias: int (weighted avg, rounded)
              - resolved_by: str name of highest-confidence voter
              - voter_contributions: Dict[str, float] voter->final_weight
        """
        votes: Dict[str, VoterVote] = {}

        for name, vote_fn in self._voters.items():
            try:
                vote = vote_fn(context)
                if vote is not None:
                    votes[name] = vote
            except Exception:
                logger.exception(f"[PriorityNegotiator] Voter '{name}' failed")

        if not votes:
            return {
                "routing_mode": None,
                "response_style": None,
                "temperature_bias": 0.0,
                "tokens_bias": 0,
                "resolved_by": "no_voters",
                "voter_contributions": {},
            }

        # Categorical voting: routing_mode (weighted plurality)
        mode_votes: Dict[str, float] = {}
        for name, vote in votes.items():
            if vote.routing_mode:
                w = self._weight_fns[name](context) * vote.confidence
                mode_votes[vote.routing_mode] = mode_votes.get(vote.routing_mode, 0.0) + w

        winning_mode = max(mode_votes, key=mode_votes.get) if mode_votes else None

        # Categorical voting: response_style (weighted plurality)
        style_votes: Dict[str, float] = {}
        for name, vote in votes.items():
            if vote.response_style:
                w = self._weight_fns[name](context) * vote.confidence
                style_votes[vote.response_style] = style_votes.get(vote.response_style, 0.0) + w

        winning_style = max(style_votes, key=style_votes.get) if style_votes else None

        # Numeric fusion: weighted average of temperature/tokens biases
        total_conf = sum(vote.confidence for vote in votes.values())
        if total_conf > 0:
            temp_bias = sum(v.temperature_bias * v.confidence for v in votes.values()) / total_conf
            tokens_bias = int(
                sum(v.tokens_bias * v.confidence for v in votes.values()) / total_conf
            )
        else:
            temp_bias = 0.0
            tokens_bias = 0

        # Determine which voter contributed most (highest confidence * base_weight)
        contributions: Dict[str, float] = {
            n: v.confidence * self._weight_fns[n](context) for n, v in votes.items()
        }
        top_voter = max(contributions, key=contributions.get) if contributions else "none"

        return {
            "routing_mode": winning_mode,
            "response_style": winning_style,
            "temperature_bias": round(temp_bias, 3),
            "tokens_bias": tokens_bias,
            "resolved_by": top_voter,
            "voter_contributions": {n: round(c, 4) for n, c in contributions.items()},
        }


# ── Default Voter Functions ──────────────────────────────────────────


def lifecycle_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract lifecycle routing preference from context."""
    lc = context.get("lifecycle_behavior")
    if not lc:
        return None
    return VoterVote(
        routing_mode=lc.get("routing_mode"),
        response_style=lc.get("response_style"),
        confidence=lc.get("confidence", 0.5),
    )


def emotional_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract user emotional routing preference from context."""
    behavior = context.get("emotional_behavior")
    if not behavior:
        return None
    return VoterVote(
        routing_mode=behavior.get("routing_mode"),
        response_style=behavior.get("response_style"),
        confidence=behavior.get("confidence", 0.5),
    )


def intent_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract intent routing preference from context."""
    ir = context.get("intent_routing")
    if not ir:
        return None
    return VoterVote(
        routing_mode=ir.get("routing_mode"),
        response_style=ir.get("response_style"),
        confidence=ir.get("intent_strength", 0.3),
    )


def angela_emotion_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract Angela's internal emotional routing preference."""
    ae = context.get("angela_emotion")
    if not ae:
        return None
    return VoterVote(
        routing_mode=ae.get("routing_mode"),
        response_style=ae.get("response_style"),
        confidence=ae.get("emotion_intensity", 0.5),
    )


def causal_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract causal routing adjustment (temperature/tokens bias)."""
    cr = context.get("causal_routing")
    if not cr:
        return None
    conf = cr.get("causal_confidence", 0.0)
    if conf <= 0.3:
        return None
    return VoterVote(
        temperature_bias=cr.get("temperature_bias", 0.0),
        tokens_bias=cr.get("max_tokens_bias", 0),
        confidence=conf,
    )


def meta_calibration_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract MetaController calibration adjustment as temperature/tokens bias.

    MetaController's weighted adjustment reflects the system's historical
    calibration accuracy. A negative adjustment (overconfident) biases toward
    lower temperature (more conservative). A positive adjustment (underconfident)
    biases toward higher temperature (more exploratory).
    """
    mc = context.get("meta_calibration")
    if not mc:
        return None
    adj = mc.get("weighted_adjustment", 0.0)
    if abs(adj) < 0.001:
        return None
    temp_bias = round(adj * 3.0, 3)
    tokens_bias = int(adj * 200)
    confidence = min(1.0, abs(adj) * 10.0)
    return VoterVote(
        routing_mode=None,
        response_style=None,
        temperature_bias=temp_bias,
        tokens_bias=tokens_bias,
        confidence=round(confidence, 3),
    )


def heartbeat_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract Heartbeat system health as a confidence multiplier.

    When system health is low (<0.3), biases toward conservative routing
    (the system is stressed/unstable). When health is high (>0.7), allows
    more exploratory routing. The effect scales proportionally.
    """
    hb = context.get("heartbeat_health")
    if not hb:
        return None
    health = hb.get("system_health", 0.5)
    health_bias = round((health - 0.5) * 2.0, 3)
    return VoterVote(
        routing_mode="conservative" if health < 0.3 else None,
        response_style=None,
        temperature_bias=health_bias * 0.5,
        tokens_bias=int(health_bias * 50),
        confidence=abs(health_bias) + 0.3,
    )


def dli_state_voter(context: Dict[str, Any]) -> Optional[VoterVote]:
    """Extract DigitalLifeIntegrator lifecycle state as routing preference.

    The DLI lifecycle state reflects Angela's long-term developmental phase.
    Earlier states (INITIALIZING, AWAKENING) favor conservative/neutral
    routing. Later states (MATURE, RESTING) allow exploratory routing.
    DORMANT forces conservative.
    """
    dli = context.get("dli_state")
    if not dli:
        return None
    state = dli.get("life_cycle_state", "").upper()
    if state == "DORMANT":
        return VoterVote(
            routing_mode="conservative",
            response_style="minimal",
            temperature_bias=-0.3,
            tokens_bias=-100,
            confidence=0.8,
        )
    if state in ("INITIALIZING", "AWAKENING"):
        return VoterVote(
            routing_mode="neutral",
            response_style="cautious",
            confidence=0.5,
        )
    if state == "MATURE":
        return VoterVote(
            routing_mode="exploratory",
            response_style="confident",
            temperature_bias=0.1,
            tokens_bias=50,
            confidence=0.6,
        )
    return None
