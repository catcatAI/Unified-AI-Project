"""LLM Routing Policy Module - Fixed Version

Provides policy-based routing for LLM model selection.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from core.services.multi_llm_service import ModelProvider


@dataclass
class RoutingPolicy:
    """Routing policy configuration"""
    task_type: str  # translation|code|reasoning|image|vision|general
    input_chars: int = 0
    needs_tools: bool = False
    needs_vision: bool = False
    latency_target: Optional[float] = None
    cost_ceiling: Optional[float] = None


@dataclass
class ModelProfile:
    """Model profile for routing"""
    model_id: str
    provider: str
    model_name: str
    enabled: bool
    available: bool
    context_window: int
    max_tokens: int
    cost_per_1k_tokens: float
    capabilities: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'provider': self.provider,
            'model_name': self.model_name,
            'enabled': self.enabled,
            'available': self.available,
            'context_window': self.context_window,
            'max_tokens': self.max_tokens,
            'cost_per_1k_tokens': self.cost_per_1k_tokens,
            'capabilities': self.capabilities
        }


class ModelRegistry:
    """
    Model registry for tracking available models.
    Minimal implementation; marks a model as available when enabled and either
    - api_key is present (for cloud providers) or
    - provider is OLLAMA (local) or other providers that may not require key.
    """
    
    KEY_REQUIRED = {
        ModelProvider.OPENAI: True,
        ModelProvider.ANTHROPIC: True,
        ModelProvider.GOOGLE: True,
        ModelProvider.AZURE_OPENAI: True,
        ModelProvider.COHERE: True,
        ModelProvider.HUGGINGFACE: True,
        ModelProvider.OLLAMA: False,
    }
    
    def __init__(self, model_configs: Dict[str, Any]):
        self.model_configs = model_configs
    
    def _is_available(self, cfg) -> bool:
        """Check if model is available"""
        key_required = self.KEY_REQUIRED.get(cfg.provider, True)
        if not key_required:
            return cfg.enabled
        # Cloud providers require api_key
        return cfg.enabled and bool(cfg.api_key)
    
    def list_profiles(self) -> List[ModelProfile]:
        """List all model profiles"""
        profiles = []
        for model_id, cfg in self.model_configs.items():
            capabilities = {
                "json_mode": cfg.provider in (ModelProvider.OPENAI, ModelProvider.ANTHROPIC),
                "tool_use": cfg.provider in (ModelProvider.OPENAI, ModelProvider.ANTHROPIC, ModelProvider.AZURE_OPENAI),
                "vision": cfg.provider in (ModelProvider.GOOGLE, ModelProvider.OPENAI),
            }
            profiles.append(ModelProfile(
                model_id=model_id,
                provider=cfg.provider.value if hasattr(cfg.provider, 'value') else str(cfg.provider),
                model_name=cfg.model_name,
                enabled=cfg.enabled,
                available=self._is_available(cfg),
                context_window=cfg.context_window,
                max_tokens=cfg.max_tokens,
                cost_per_1k_tokens=cfg.cost_per_1k_tokens,
                capabilities=capabilities
            ))
        return profiles
    
    def list_models(self):
        """Alias for list_profiles for compatibility"""
        return self.list_profiles()
    
    def profiles_dict(self) -> List[Dict[str, Any]]:
        """Return profiles as list of dictionaries"""
        return [p.to_dict() for p in self.list_profiles()]


class PolicyRouter:
    """
    Simple heuristic-based router. Scores models based on:
    - Capability match (tools / json / vision)
    - Context window >= input size heuristic
    - Provider / task defaults
    - Cost / latency (if provided)
    """
    
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
    
    def route(self, policy: RoutingPolicy) -> Dict[str, Any]:
        """Route to best model based on policy"""
        candidates = self.registry.list_models()
        if not candidates:
            return {"error": "no_available_models", "candidates": []}
        
        scored = []
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
            
            # 2) Context window heuristic (prefer larger windows for large input)
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
                # Image gen is proxied via existing image endpoint
                score += 0.5
            
            # 4) Cost / latency hints (if provided)
            if policy.cost_ceiling is not None:
                # Prefer cheaper than ceiling
                if p.cost_per_1k_tokens <= policy.cost_ceiling:
                    score += 0.5
            if policy.latency_target is not None:
                # No real latency telemetry yet; award small neutral score
                score += 0.1
            
            scored.append({
                "model_id": p.model_id,
                "score": round(score, 3),
                "profile": p.to_dict()
            })
        
        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0] if scored else None
        return {"best": best, "candidates": scored}
