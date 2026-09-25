# ANGELA-MATRIX: L3 [βδ] [A] [L2-L6]

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _safe_status(entry: Any) -> Dict[str, Any]:
    try:
        getter = getattr(entry, "get_status", None)
        value = getter() if callable(getter) else None
        return value if isinstance(value, dict) else {}
    except Exception as exc:
        logger.debug("capability status unavailable: %s", exc)
        return {}


def _capability_ids(agent: Any) -> List[str]:
    raw = getattr(agent, "capabilities", None)
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, (list, tuple, set)):
        return []
    result: List[str] = []
    seen = set()
    for item in raw:
        if isinstance(item, dict):
            value = item.get("capability_id") or item.get("name")
        else:
            value = item
        value = str(value or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _agent_methods(entry: Any, status: Dict[str, Any]) -> List[str]:
    nested = status.get("agent_status")
    source = nested if isinstance(nested, dict) else status
    values = source.get("available_methods", [])
    if not isinstance(values, (list, tuple, set)):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _collect_agents() -> List[Dict[str, Any]]:
    try:
        from api.lifespan import get_agent_manager

        manager = get_agent_manager()
    except Exception as exc:
        logger.debug("agent manager unavailable for capability catalog: %s", exc)
        return []

    registered = getattr(manager, "agents", None)
    if not isinstance(registered, dict):
        return []

    result: List[Dict[str, Any]] = []
    for agent_id, entry in sorted(registered.items(), key=lambda item: str(item[0])):
        agent = getattr(entry, "agent", entry)
        status = _safe_status(entry)
        nested = status.get("agent_status")
        status = nested if isinstance(nested, dict) else status
        capabilities = _capability_ids(agent)
        methods = _agent_methods(entry, status)
        enabled = status.get("enabled")
        state = "disabled" if enabled is False else "registered"
        result.append(
            {
                "id": str(agent_id),
                "state": state,
                "capabilities": capabilities,
                "methods": methods,
            }
        )
    return result


def _collect_backends(llm_service: Any) -> List[Dict[str, Any]]:
    backends = getattr(llm_service, "backends", None)
    if not isinstance(backends, dict):
        return []
    active_type = getattr(llm_service, "active_backend_type", None)
    active_name = getattr(active_type, "value", None)
    result = []
    for backend_type, backend in sorted(backends.items(), key=lambda item: str(item[0])):
        name = getattr(backend_type, "value", str(backend_type))
        model = getattr(backend, "model", None) or getattr(backend, "model_name", None)
        result.append(
            {
                "name": str(name),
                "model": str(model or "unknown"),
                "active": str(name) == str(active_name),
            }
        )
    return result


def _collect_handlers(llm_service: Any) -> List[str]:
    bus = getattr(llm_service, "model_bus", None)
    handler_map = getattr(bus, "_handler_map", None)
    if isinstance(handler_map, dict):
        return sorted(str(key) for key in handler_map)
    handlers = getattr(bus, "_handlers", None)
    if isinstance(handlers, dict):
        return sorted(str(key) for key in handlers)
    return []


def _collect_registered_services() -> List[str]:
    try:
        from core.interfaces.service_registry import get_registry

        return sorted(str(name) for name in get_registry().service_names)
    except Exception as exc:
        logger.debug("service registry unavailable for capability catalog: %s", exc)
        return []


def _collect_core_modules() -> List[str]:
    try:
        import api.lifespan as lifespan
    except Exception as exc:
        logger.debug("lifespan unavailable for capability catalog: %s", exc)
        return []

    names = []
    for attr in (
        "_digital_life_instance",
        "_agent_manager_instance",
        "_bio_integrator_instance",
        "_crisis_system_instance",
        "_causal_reasoning_instance",
        "_lifecycle_instance",
        "_heartbeat_instance",
        "_training_coordinator_instance",
        "_proactive_instance",
        "_chat_service_instance",
    ):
        if getattr(lifespan, attr, None) is not None:
            names.append(attr.strip("_"))
    return names


def build_capability_snapshot(llm_service: Optional[Any] = None) -> Dict[str, Any]:
    if llm_service is None:
        try:
            from core.interfaces.service_registry import get_registry

            llm_service = get_registry().get("angela_llm_service")
        except Exception as exc:
            logger.debug("LLM service unavailable for capability catalog: %s", exc)
    return {
        "agents": _collect_agents(),
        "backends": _collect_backends(llm_service),
        "handlers": _collect_handlers(llm_service),
        "services": _collect_registered_services(),
        "core_modules": _collect_core_modules(),
    }


def _format_names(values: List[str], limit: int = 18) -> str:
    if len(values) > limit:
        return "、".join(values[:limit]) + f"…（共 {len(values)} 項）"
    return "、".join(values)


def render_capability_response(snapshot: Dict[str, Any]) -> str:
    lines = ["我剛才直接讀取目前這個 runtime 的註冊狀態，不是用記憶模板回答："]

    backends = snapshot.get("backends", [])
    if backends:
        active = next((item["name"] for item in backends if item.get("active")), "unknown")
        details = [f"{item['name']}／{item['model']}" for item in backends]
        lines.append(f"• 語言模型：{_format_names(details)}；目前 active={active}")

    agents = snapshot.get("agents", [])
    if agents:
        lines.append(f"• 已註冊專業代理（{len(agents)}）：")
        for item in agents:
            values = item.get("capabilities") or item.get("methods") or []
            suffix = f"（{item.get('state', 'registered')}，{len(values)} 項）"
            lines.append(f"  - {item.get('id', 'unknown')}{suffix}：{_format_names(values)}")

    handlers = snapshot.get("handlers", [])
    if handlers:
        lines.append(f"• 已註冊工具／handlers：{_format_names(handlers)}")

    core_modules = snapshot.get("core_modules", [])
    if core_modules:
        lines.append(f"• 已啟動核心模組：{_format_names(core_modules)}")

    services = snapshot.get("services", [])
    if services:
        lines.append(f"• Service registry：{_format_names(services)}")

    if len(lines) == 1:
        return "目前這個 runtime 尚未註冊可盤點的能力；我不會把未啟用的功能說成已可用。"
    lines.append("清單每次提問都重新讀取；未啟用的功能我不會說成已可用。")
    return "\n".join(lines)
