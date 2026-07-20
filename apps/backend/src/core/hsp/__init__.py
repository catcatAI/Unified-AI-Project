# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [A/B/C] [L4+]
# =============================================================================
"""
HSP (Hyperdimensional State Processing) package — core communication and
state management layer for Angela AI.

Provides:
  - connector:   HSPConnector — MQTT/local IPC communication
  - security:    HSPSecurityManager — message signing, encryption, auth
  - transport:   HSPTransport, LocalIPCTransport, MQTTTransport — transport abstraction
  - types:       HSPMessageEnvelope, HSPFactPayload, HSPTaskRequestPayload, …
  - versioning:  HSPVersionManager, HSPVersionCompatibility — version negotiation
  - performance: HSPPerformanceOptimizer — message caching, batching, metrics
  - mqtt:        MQTTSubscriptionManager — subscription tracking & lifecycle

All imports are lazy to avoid circular imports at bootstrap time.
Import directly from submodules: from core.hsp.connector import HSPConnector
"""

import importlib
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

_LAZY_HSP: dict[str, tuple[str, str]] = {
    # connector
    "HSPConnector": ("core.hsp.connector", "HSPConnector"),
    # security
    "HSPSecurityManager": ("core.hsp.security", "HSPSecurityManager"),
    "HSPSecurityContext": ("core.hsp.security", "HSPSecurityContext"),
    # transport
    "HSPTransport": ("core.hsp.transport", "HSPTransport"),
    "HSPTransportMode": ("core.hsp.transport", "HSPTransportMode"),
    "LocalIPCTransport": ("core.hsp.transport", "LocalIPCTransport"),
    "MQTTTransport": ("core.hsp.transport", "MQTTTransport"),
    "HSPTransportFactory": ("core.hsp.transport", "HSPTransportFactory"),
    # types
    "HSPMessageEnvelope": ("core.hsp.types", "HSPMessageEnvelope"),
    "HSPFactPayload": ("core.hsp.types", "HSPFactPayload"),
    "HSPTaskRequestPayload": ("core.hsp.types", "HSPTaskRequestPayload"),
    "HSPCapabilityAdvertisementPayload": ("core.hsp.types", "HSPCapabilityAdvertisementPayload"),
    "HSPStateSyncPayload": ("core.hsp.types", "HSPStateSyncPayload"),
    "HSPAckPayload": ("core.hsp.types", "HSPAckPayload"),
    "HSPErrorPayload": ("core.hsp.types", "HSPErrorPayload"),
    # versioning
    "HSPVersionInfo": ("core.hsp.versioning", "HSPVersionInfo"),
    "HSPVersionManager": ("core.hsp.versioning", "HSPVersionManager"),
    "HSPVersionCompatibility": ("core.hsp.versioning", "HSPVersionCompatibility"),
    "HSPVersionNegotiator": ("core.hsp.versioning", "HSPVersionNegotiator"),
    # performance
    "HSPPerformanceOptimizer": ("core.hsp.performance_optimizer", "HSPPerformanceOptimizer"),
    "HSPPerformanceEnhancer": ("core.hsp.performance_optimizer", "HSPPerformanceEnhancer"),
    # extensibility
    "HSPExtensionManager": ("core.hsp.extensibility", "HSPExtensionManager"),
    "HSPMessageRegistry": ("core.hsp.extensibility", "HSPMessageRegistry"),
    # mqtt
    "MQTTSubscriptionManager": ("core.hsp.mqtt_subscription_manager", "MQTTSubscriptionManager"),
    # advanced
    "HSPAdvancedPerformanceOptimizer": (
        "core.hsp.advanced_performance_optimizer",
        "HSPAdvancedPerformanceOptimizer",
    ),
}

_lazy_cache: dict[str, Any] = {}
_warned: set[str] = set()


class _HSPSentinel:
    """Sentinel returned when a lazy import fails."""

    def __init__(self, name: str) -> None:
        self._name = name
        if name not in _warned:
            logger.warning("core.hsp.%s not available", name)
            _warned.add(name)

    def __getattr__(self, attr: str) -> "_HSPSentinel":
        return _HSPSentinel(f"{self._name}.{attr}")

    def __call__(self, *args: Any, **kwargs: Any) -> "_HSPSentinel":
        return self

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<core.hsp.{self._name} (missing)>"


def __getattr__(name: str) -> Any:
    if name in _LAZY_HSP:
        if name in _lazy_cache:
            return _lazy_cache[name]
        module_path, attr = _LAZY_HSP[name]
        try:
            module = importlib.import_module(module_path)
            result = getattr(module, attr)
            _lazy_cache[name] = result
            return result
        except Exception as e:
            if name not in _warned:
                logger.debug("Failed to lazy-import %s from %s: %s", name, module_path, e)
                _warned.add(name)
            _lazy_cache[name] = None
            return None

    # Dynamic submodule import
    try:
        module = importlib.import_module(f"core.hsp.{name}")
        return module
    except ImportError:
        logger.debug("Lazy import failed for core.hsp.%s, using sentinel", name, exc_info=True)

    return _HSPSentinel(name)


def __dir__() -> List[str]:
    return sorted(__all__)


__all__ = [
    "HSPConnector",
    "HSPSecurityManager",
    "HSPSecurityContext",
    "HSPTransport",
    "HSPTransportMode",
    "LocalIPCTransport",
    "MQTTTransport",
    "HSPTransportFactory",
    "HSPMessageEnvelope",
    "HSPFactPayload",
    "HSPTaskRequestPayload",
    "HSPCapabilityAdvertisementPayload",
    "HSPStateSyncPayload",
    "HSPAckPayload",
    "HSPErrorPayload",
    "HSPVersionInfo",
    "HSPVersionManager",
    "HSPVersionCompatibility",
    "HSPVersionNegotiator",
    "HSPPerformanceOptimizer",
    "HSPPerformanceEnhancer",
    "HSPExtensionManager",
    "HSPMessageRegistry",
    "MQTTSubscriptionManager",
    "HSPAdvancedPerformanceOptimizer",
]
