"""Tests for integrations/enhanced_rovo_dev_connector.py"""
import pytest


class TestEnhancedRovoDevConnector:
    """Tests for EnhancedRovoDevConnector"""

    def test_import(self):
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        assert EnhancedRovoDevConnector is not None

    def test_import_components(self):
        from integrations.enhanced_rovo_dev_connector import (
            CircuitBreaker,
            EndpointConfig,
            EnhancedRovoDevConnector,
            RetryConfig,
        )
        assert RetryConfig is not None
        assert EndpointConfig is not None
        assert CircuitBreaker is not None

    def test_instantiation(self):
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        instance = EnhancedRovoDevConnector(config={})
        assert instance is not None

    def test_retry_config_defaults(self):
        from integrations.enhanced_rovo_dev_connector import RetryConfig
        cfg = RetryConfig()
        assert cfg.max_retries == 3
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 60.0
        assert cfg.backoff_factor == 2.0
        assert 429 in cfg.retry_on_status
        assert 503 in cfg.retry_on_status

    def test_endpoint_config(self):
        from integrations.enhanced_rovo_dev_connector import EndpointConfig
        ep = EndpointConfig(primary_url="https://test.com/api")
        assert ep.primary_url == "https://test.com/api"
        assert ep.timeout == 30.0
        assert ep.backup_urls == []

    def test_endpoint_config_with_backups(self):
        from integrations.enhanced_rovo_dev_connector import EndpointConfig
        ep = EndpointConfig(
            primary_url="https://primary.com",
            backup_urls=["https://backup1.com", "https://backup2.com"],
            timeout=10.0,
        )
        assert len(ep.backup_urls) == 2
        assert ep.timeout == 10.0

    def test_circuit_breaker_defaults(self):
        from integrations.enhanced_rovo_dev_connector import CircuitBreaker
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.state == "closed"

    def test_circuit_breaker_initial_state(self):
        from integrations.enhanced_rovo_dev_connector import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        assert cb.state == "closed"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_rovo_alias_to_enhanced(self):
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        from integrations.rovo_dev_connector import RovoDevConnector
        assert RovoDevConnector is EnhancedRovoDevConnector
