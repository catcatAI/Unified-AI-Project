"""Model Registry Module - Fixed Version

Provides model registration and profile management.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List
import logging
logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """Model profile for registry"""
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
        return asdict(self)


class ModelRegistry:
    """
    Model registry for tracking available models.
    """
    
    def __init__(self, model_configs: Dict[str, Any]):
        self.model_configs = model_configs
    
    def _is_available(self, cfg) -> bool:
        """Check if model is available"""
        # Check if API key is present for cloud providers
        provider = cfg.provider
        if hasattr(provider, 'value'):
            provider_str = provider.value
        else:
            provider_str = str(provider)
        
        # Local providers don't need API keys
        local_providers = ['ollama', 'llamacpp', 'local']
        is_local = any(lp in provider_str.lower() for lp in local_providers)
        
        if is_local:
            return cfg.enabled
        
        # Cloud providers require api_key
        return cfg.enabled and bool(getattr(cfg, 'api_key', None))
    
    def list_profiles(self) -> List[ModelProfile]:
        """List all model profiles"""
        profiles = []
        for model_id, cfg in self.model_configs.items():
            # Determine provider string
            if hasattr(cfg.provider, 'value'):
                provider_str = cfg.provider.value
            elif hasattr(cfg.provider, 'name'):
                provider_str = cfg.provider.name
            else:
                provider_str = str(cfg.provider)
            
            capabilities = {
                "json_mode": any(p in provider_str.lower() for p in ['openai', 'anthropic']),
                "tool_use": any(p in provider_str.lower() for p in ['openai', 'anthropic', 'azure']),
                "vision": any(p in provider_str.lower() for p in ['google', 'openai']),
            }
            
            profiles.append(ModelProfile(
                model_id=model_id,
                provider=provider_str,
                model_name=cfg.model_name,
                enabled=cfg.enabled,
                available=self._is_available(cfg),
                context_window=cfg.context_window,
                max_tokens=cfg.max_tokens,
                cost_per_1k_tokens=getattr(cfg, 'cost_per_1k_tokens', 0.0),
                capabilities=capabilities
            ))
        return profiles
    
    def list_models(self):
        """Alias for list_profiles for compatibility"""
        return self.list_profiles()
    
    def profiles_dict(self) -> List[Dict[str, Any]]:
        """Return profiles as list of dictionaries"""
        return [p.to_dict() for p in self.list_profiles()]
