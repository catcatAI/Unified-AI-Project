# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3]
# =============================================================================
"""
SelfIntrospector – simple mental health check placeholder.
Provides perform_mental_health_check used by DigitalLifeIntegrator.
"""

from typing import Any, Dict


class SelfIntrospector:
    """A lightweight introspection utility.

    In the full system this would analyse the combined state matrix and
    biological signals to detect cognitive dissonance and other anomalies.
    Here we provide a minimal deterministic implementation sufficient for
    import and basic runtime.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        # Thresholds can be overridden via config.
        self.dissonance_threshold: float = self.config.get("dissonance_threshold", 0.6)
        self.anomaly_score_key: str = self.config.get("anomaly_score_key", "dissonance_score")

    async def perform_mental_health_check(
        self, combined_state: Dict[str, Any], context: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Perform a very simple mental‑health style check.

        The function looks for a numeric *dissonance_score* in the combined
        state (if present) and flags dissonance when the score exceeds the
        configured threshold.  It also returns a list of *anomalies* – any keys
        whose value is below 0.2 (indicating a potential issue).
        """
        # Extract a score if the integrator provides one.
        score = combined_state.get(self.anomaly_score_key, 0.0)
        dissonance_detected = float(score) > self.dissonance_threshold

        # Simple anomaly detection – collect low‑value entries.
        anomalies = [
            k for k, v in combined_state.items() if isinstance(v, (int, float)) and v < 0.2
        ]

        return {
            "dissonance_detected": dissonance_detected,
            "anomalies": anomalies,
            # Mirror the original score for downstream logic.
            self.anomaly_score_key: score,
        }

    def get_introspection_prompt_injection(
        self, combined_state: Dict[str, Any], lifecycle_metrics: Dict[str, Any] | None = None
    ) -> str:
        """Build a prompt injection string summarising current internal state.

        Args:
            combined_state: Merged state matrix + biological state dict.
            lifecycle_metrics: Optional lifecycle metrics (life_intensity, c_gap, etc.).

        Returns:
            A human‑readable string suitable for prepending to Angela's LLM prompt.
        """
        lines = ["[Self-Introspection Report]"]

        # Key state values
        for key in ("arousal", "valence", "curiosity", "trust", "dissonance_score"):
            val = combined_state.get(key)
            if val is not None:
                lines.append(f"  {key}: {float(val):.3f}")

        # Lifecycle metrics
        if lifecycle_metrics:
            for key, val in lifecycle_metrics.items():
                if val is not None:
                    lines.append(f"  {key}: {float(val):.3f}")

        return "\n".join(lines)
