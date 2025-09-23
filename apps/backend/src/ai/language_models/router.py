from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .registry import ModelRegistry, ModelProfile

# Use absolute imports instead of relative imports when running as a script
try:
    # Try relative imports first (for when running with uvicorn)
    from ...services.multi_llm_service import ModelProvider
except ImportError:
    # Fall back to absolute imports (for when running as a script)
    from core.services.multi_llm_service import ModelProvider


@dataclass
class RoutingPolicy:
    task_type: str  # translation|code|reasoning|image|vision|general
    input_chars: int = 0
    needs_tools: bool = False
    needs_vision: bool = False
    latency_target: Optional[float] = None
    cost_ceiling: Optional[float] = None


class PolicyRouter:
    """
    Simple heuristic-based router. Scores models based on:
    - Capability match (tools/json/vision)
    - Context window >= input size heuristic
    - Provider/task defaults
    - Cost/latency (if provided)
    """

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def route(self, policy: RoutingPolicy) -> Dict[str, Any]:
        candidates: List[ModelProfile] = [p for p in self.registry.list_profiles() if p.enabled and p.available]
        if not candidates:
            return {"error": "no_available_models", "candidates": []}

        scored: List[Dict[str, Any]] = []
        for p in candidates:
            score = 0.0
            # 1) Capability matching
            if policy.needs_tools and p.capabilities.get("tool_use"):
                score += 2.0
            if policy.needs_vision and p.capabilities.get("vision"):
                score += 2.0
            # JSON mode is useful for structured tasks
            if p.capabilities.get("json_mode") and policy.task_type in ("code", "reasoning"):
                score += 1.0
            
            # 2) Context/window heuristic: prefer larger windows for large input
            if p.context_window >= max(1024, policy.input_chars // 2):
                score += 1.0
            if p.max_tokens >= 1024:
                score += 0.5

            # 3) Task bias per provider (simplified)
            if policy.task_type == "translation":
                if p.provider in (ModelProvider.OPENAI.value, ModelProvider.GOOGLE.value, ModelProvider.ANTHROPIC.value):
                    score += 1.0
            elif policy.task_type == "code":
                if p.provider in (ModelProvider.ANTHROPIC.value, ModelProvider.OPENAI.value):
                    score += 1.2
            elif policy.task_type == "reasoning":
                if p.provider in (ModelProvider.OPENAI.value, ModelProvider.ANTHROPIC.value):
                    score += 1.0
            elif policy.task_type == "image":
                # In this phase, we assume image gen is proxied via the existing image endpoint, routing TBD.
                score += 0.5

            # 4) Cost/latency hints (if provided)
            if policy.cost_ceiling is not None:
                # prefer cheaper than ceiling
                if p.cost_per_1k_tokens <= policy.cost_ceiling:
                    score += 0.5
            if policy.latency_target is not None:
                # no real latency telemetry yet; award small neutral score
                score += 0.1

            scored.append({"model_id": p.model_id, "score": round(score, 3), "profile": p.to_dict()})

        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0]
        return {"best": best, "candidates": scored}