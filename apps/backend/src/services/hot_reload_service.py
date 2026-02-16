from __future__ import annotations
import asyncio
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, TYPE_CHECKING
from unittest.mock import Mock


# Mock core_services and other dependencies for syntax validation
class MockCoreServices:
    DEFAULT_AI_ID = "mock_ai_id"

    def get_services(self):
        return {}

    def llm_interface_instance(self):
        return Mock()

    def hsp_connector_instance(self):
        return Mock()

    def get_multi_llm_service(self):
        return Mock()

    def tool_dispatcher_instance(self):
        return Mock()

    def dialogue_manager_instance(self):
        return Mock()

    def personality_manager_instance(self):
        return Mock()

    def emotion_system_instance(self):
        return Mock()

    def trust_manager_instance(self):
        return Mock()

    def service_discovery_instance(self):
        return Mock()

    hsp_connector_instance = Mock()
    llm_interface_instance = Mock()


core_services = MockCoreServices()


class HSPConnector:  # Mock
    def __init__(self, ai_id, broker_address, broker_port):
        pass

    async def connect(self):
        return True

    async def disconnect(self):
        pass

    async def subscribe(self, topic, callback):
        pass

    def register_on_capability_advertisement_callback(self, callback):
        pass


logger = logging.getLogger(__name__)

_hot_reload_service_singleton: Optional["HotReloadService"] = None


def get_hot_reload_service() -> "HotReloadService":
    global _hot_reload_service_singleton
    if _hot_reload_service_singleton is None:
        _hot_reload_service_singleton = HotReloadService()
    return _hot_reload_service_singleton


class HotReloadService:
    """
    Provides minimal, safe hot-reload and hot-drain primitives that work with the
    project's global singleton service model.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._draining: bool = False

    async def begin_draining(self) -> Dict[str, Any]:
        async with self._lock:
            self._draining = True
            return {"draining": self._draining}

    async def end_draining(self) -> Dict[str, Any]:
        async with self._lock:
            self._draining = False
            return {"draining": self._draining}

    async def status(self) -> Dict[str, Any]:
        services = core_services.get_services()
        hsp = core_services.hsp_connector_instance
        mcp = core_services.mcp_connector_instance

        hsp_status: Optional[Dict[str, Any]] = None
        mcp_status: Optional[Dict[str, Any]] = None

        try:
            if hsp is not None and hasattr(hsp, "get_communication_status"):
                hsp_status = hsp.get_communication_status()
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            hsp_status = {"error": "failed to get HSP status"}

        try:
            if mcp is not None and hasattr(mcp, "get_communication_status"):
                mcp_status = mcp.get_communication_status()
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            mcp_status = {"error": "failed to get MCP status"}

        metrics: Dict[str, Any] = {
            "hsp": {},
            "mcp": {},
            "learning": {},
            "memory": {},
            "lis": {},
        }

        return {
            "draining": self._draining,
            "services_initialized": {k: (v is not None) for k, v in services.items()},
            "hsp": hsp_status,
            "mcp": mcp_status,
            "metrics": metrics,
        }

    async def reload_llm(
        self, llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        async with self._lock:
            old_llm = core_services.llm_interface_instance
            close_ok = True
            if old_llm:
                try:
                    await old_llm.close()
                except Exception as e:
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    close_ok = False

            try:
                new_llm = core_services.get_multi_llm_service()
            except Exception as e:
                logger.error(f"Error in {__name__}: {e}", exc_info=True)
                return {
                    "reloaded": False,
                    "error": f"Failed to construct new LLM service: {e}",
                }

            core_services.llm_interface_instance = new_llm

            td = core_services.tool_dispatcher_instance
            if td is not None:
                try:
                    if hasattr(td, "set_llm_service"):
                        td.set_llm_service(new_llm)  # type ignore[attr-defined]
                    else:
                        setattr(td, "llm_service", new_llm)
                except Exception as e:
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    pass

            dm = core_services.dialogue_manager_instance
            if dm is not None:
                try:
                    if hasattr(dm, "set_llm_interface"):
                        dm.set_llm_interface(new_llm)  # type ignore[attr-defined]
                    else:
                        setattr(dm, "llm_interface", new_llm)
                except Exception as e:
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    pass

            return {"reloaded": True, "old_closed": close_ok}

    async def reload_personality(
        self, profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        async with self._lock:
            try:
                pm = core_services.personality_manager_instance
                if pm is None:
                    return {
                        "reloaded": False,
                        "error": "PersonalityManager not initialized",
                    }
                ok = pm.reload_personality(profile_name)
                dm = core_services.dialogue_manager_instance
                es = core_services.emotion_system_instance
                if dm is not None and hasattr(dm, "personality_manager"):
                    setattr(dm, "personality_manager", pm)
                if (
                    es is not None
                    and hasattr(es, "personality_profile")
                    and hasattr(pm, "current_personality")
                ):
                    try:
                        es.personality_profile = pm.current_personality()
                    except Exception as e:
                        logger.error(f"Error in {__name__}: {e}", exc_info=True)
                        pass

                return {
                    "reloaded": bool(ok),
                    "profile": (pm.current_personality or {}).get("profile_name"),
                }
            except Exception as e:
                logger.error(f"Error in {__name__}: {e}", exc_info=True)
                return {"reloaded": False, "error": str(e)}

    async def reload_hsp(self) -> Dict[str, Any]:
        async with self._lock:
            old_hsp = core_services.hsp_connector_instance
            services = core_services.get_services()
            sdm = services.get("service_discovery")
            ai_id = getattr(core_services, "DEFAULT_AI_ID", None)

            if old_hsp is None:
                return {
                    "reloaded": False,
                    "error": "No existing HSP connector to reload.",
                }

            broker_address = getattr(old_hsp, "broker_address", None)
            broker_port = getattr(old_hsp, "broker_port", None)
            if broker_address is None or broker_port is None:
                return {
                    "reloaded": False,
                    "error": "Cannot infer HSP broker settings from existing connector.",
                }

            try:
                # Assuming HSPConnector is defined elsewhere and is importable
                new_hsp = HSPConnector(
                    ai_id=old_hsp.ai_id,
                    broker_address=broker_address,
                    broker_port=broker_port,
                )
                connected = await new_hsp.connect()
                if not connected:
                    return {
                        "reloaded": False,
                        "error": "New HSP connector failed to connect.",
                    }

                # Re-subscribe minimal topics used in core_services.initialize_services()
                await new_hsp.subscribe(
                    f"hsp/capabilities/advertisements/general/#", lambda p, s, e: None
                )
                await new_hsp.subscribe(
                    f"hsp/results/{old_hsp.ai_id}/#", lambda p, s, e: None
                )
                await new_hsp.subscribe(
                    f"hsp/knowledge/facts/general/#", lambda p, s, e: None
                )

                core_services.hsp_connector_instance = new_hsp

                if sdm is not None:
                    new_hsp.register_on_capability_advertisement_callback(
                        sdm.process_capability_advertisement
                    )  # type ignore[arg-type]

                try:
                    await old_hsp.disconnect()
                except Exception as e:
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    pass

                return {"reloaded": True}
            except Exception as e:
                logger.error(f"Error in {__name__}: {e}", exc_info=True)
                return {"reloaded": False, "error": str(e)}
