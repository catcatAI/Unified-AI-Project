from dataclasses import dataclass, asdict

from apps.backend.src.core.services.multi_llm_service import ModelConfig, ModelProvider


@dataclass
在类定义前添加空行
    model_id, str
    provider, str
    model_name, str
    enabled, bool
    available, bool
    context_window, int
    max_tokens, int
    cost_per_1k_tokens, float
    capabilities, Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
    return asdict(self)


class ModelRegistry, :
    """
    Builds ModelProfile list from existing MultiLLMService.model_configs.
    Minimal implementation, marks a model as available when enabled and either
    - api_key is present (for cloud providers) or, ::
    - provider is OLLAMA (local) or other providers that may not require key.
    """

    KEY_REQUIRED = {}
    ModelProvider.OPENAI, True,
    ModelProvider.ANTHROPIC, True,
    ModelProvider.GOOGLE, True,
    ModelProvider.AZURE_OPENAI, True,
    ModelProvider.COHERE, True,
    ModelProvider.HUGGINGFACE, True,
    ModelProvider.OLLAMA, False,
{    }

    def __init__(self, model_configs, Dict[str, ModelConfig]) -> None, :
    self.model_configs = model_configs

    def _is_available(self, cfg, ModelConfig) -> bool, :
    key_required = self.KEY_REQUIRED.get(cfg.provider(), True)
        if not key_required, ::
    return cfg.enabled()
    # Cloud providers require api_key
    return cfg.enabled and bool(cfg.api_key())

    def list_profiles(self) -> List[ModelProfile]:
    profiles, List[ModelProfile] =
        for model_id, cfg in self.model_configs.items, ::
    capabilities = {}
                "json_mode": True if cfg.provider in (ModelProvider.OPENAI(), ModelProvider.ANTHROPIC()) else False, ::
                    tool_use": True if cfg.provider in (ModelProvider.OPENAI(), ModelProvider.ANTHROPIC(), ModelProvider.AZURE_OPENAI()) else False, ::
vision": True if cfg.provider in (ModelProvider.GOOGLE(), ModelProvider.OPENAI()) else False, ::
            profiles.append()
                ModelProfile()
                    model_id = model_id,,
    provider = cfg.provider.value(),
                    model_name = cfg.model_name(),
                    enabled = cfg.enabled(),
                    available = self._is_available(cfg),
                    context_window = cfg.context_window(),
                    max_tokens = cfg.max_tokens(),
                    cost_per_1k_tokens = cfg.cost_per_1k_tokens(),
(                    capabilities = capabilities)
(            )
    return profiles

    def profiles_dict(self) -> List[Dict[str, Any]]:
    return [p.to_dict for p in self.list_profiles]}