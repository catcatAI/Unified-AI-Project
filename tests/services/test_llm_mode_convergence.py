"""
ANGELA-MATRIX: [L4] [β] [B] [L3]
The two LLM modes must not shadow each other.

``deployment.mode`` gates the backend *categories* (local / local+llm / llm /
auto); ``settings.llm_mode`` selects the *strategy* (standard / auto). They
shared one variable, and ``deployment.mode`` won: with the shipped config
(``deployment.mode: local``) the strategy was pinned to "local", so the
documented way to turn auto-selection on (``settings.llm_mode: auto``) never
took effect and the auto-selector never ran.
"""

import pytest
from services.llm.router import AngelaLLMService


def _service(config: dict) -> AngelaLLMService:
    service = object.__new__(AngelaLLMService)
    service.config = config
    return service


class TestLLMModeResolution:
    def test_shipped_config_keeps_the_standard_strategy(self):
        service = _service({"deployment": {"mode": "local"}, "settings": {"llm_mode": "standard"}})
        assert service.deployment_mode == "local"
        assert service.llm_mode == "standard"

    def test_settings_llm_mode_auto_is_honoured(self):
        """The defect: deployment.mode used to shadow the strategy."""
        service = _service({"deployment": {"mode": "local"}, "settings": {"llm_mode": "auto"}})
        assert service.deployment_mode == "local"
        assert service.llm_mode == "auto"

    def test_deployment_auto_opens_the_categories_and_the_strategy(self):
        service = _service({"deployment": {"mode": "auto"}, "settings": {"llm_mode": "standard"}})
        assert service.deployment_mode == "auto"
        assert service.llm_mode == "auto"
        assert service._allowed_types() == frozenset({"local", "cloud"})

    @pytest.mark.parametrize(
        "mode,expected",
        [
            ("local", frozenset({"local"})),
            ("local+llm", frozenset({"local", "cloud"})),
            ("llm", frozenset({"cloud"})),
            ("auto", frozenset({"local", "cloud"})),
        ],
    )
    def test_the_category_gate_follows_deployment_mode(self, mode, expected):
        service = _service({"deployment": {"mode": mode}})
        assert service._allowed_types() == expected

    def test_a_service_built_without_init_still_resolves(self):
        """Several call sites build the service with object.__new__."""
        service = object.__new__(AngelaLLMService)
        assert service.deployment_mode == "local"
        assert service.llm_mode == "standard"
