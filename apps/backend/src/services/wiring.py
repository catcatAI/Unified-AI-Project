"""
ANGELA-MATRIX: [L3-L5] [βγ] [A] [L3]
Wiring module: cross-service dependency injection during startup.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def initialize_all_services(manager) -> tuple:
    """Initialize services and link components during startup."""
    from api.lifespan import (
        get_desktop_interaction,
        get_action_executor,
        get_vision_service,
        get_audio_service,
        get_tactile_service,
        get_abc_key_manager,
        get_digital_life,
        get_economy_manager,
    )

    desktop_interaction = get_desktop_interaction()
    action_executor = get_action_executor()
    vision_service = get_vision_service()
    audio_service = get_audio_service()
    tactile_service = get_tactile_service()
    abc_key_manager = get_abc_key_manager()
    digital_life = get_digital_life()
    economy_manager = get_economy_manager()

    from api.v1.endpoints import pet
    from api.v1.endpoints._deps import set_economy_manager as _set_econ

    pet_manager = pet.get_pet_manager()
    digital_life.broadcast_callback = manager.broadcast
    pet.set_biological_integrator(digital_life.biological_integrator)
    pet.set_economy_manager(economy_manager)
    _set_econ(economy_manager)

    try:
        from services.hot_reload_service import get_hot_reload_service
        from core.security.security_audit import get_security_audit
        get_hot_reload_service()
        get_security_audit()
        logger.info("[Lifecycle] HotReloadService and SecurityAudit activated and ready.")
    except Exception as e:
        logger.warning(f"[Lifecycle] Failed to activate management assets: {e}", exc_info=True)

    async def pet_broadcast_wrapper(event_type, data) -> None:
        await manager.broadcast(
            {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    pet_manager.broadcast_callback = pet_broadcast_wrapper

    def bio_event_callback(event_name, event_data) -> None:
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(
                        {
                            "type": "biological_event",
                            "data": {"event": event_name, "data": event_data},
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    loop,
                )
        except Exception as e:
            logger.error(f"Failed to bridge biological event: {e}", exc_info=True)

    if hasattr(digital_life.biological_integrator, "register_event_callback"):
        digital_life.biological_integrator.register_event_callback(bio_event_callback)

    # C3: register plugin system and wire bio event → on_bio_event hook
    try:
        from core.plugin import plugin_manager
        from core.interfaces.service_registry import get_registry
        get_registry().register("plugin_manager", plugin_manager)

        if hasattr(digital_life.biological_integrator, "register_event_callback"):
            original_callback = bio_event_callback
            def _plugin_aware_callback(event_name, event_data) -> None:
                try:
                    import asyncio as _aio
                    _aio.create_task(
                        plugin_manager.execute_hook("on_bio_event", {
                            "event": event_name, "data": event_data
                        })
                    )
                except Exception as e:
                    logger.warning(f"Plugin bio event callback failed for {event_name}: {e}", exc_info=True)
                original_callback(event_name, event_data)
            digital_life.biological_integrator.register_event_callback(_plugin_aware_callback)
        logger.info("[C3] Plugin system registered and bio hooks wired")
    except Exception as e:
        logger.warning(f"[C3] Plugin system wiring skipped: {e}", exc_info=True)

    return (
        desktop_interaction,
        action_executor,
        vision_service,
        audio_service,
        tactile_service,
        abc_key_manager,
        digital_life,
        economy_manager,
    )


async def initialize_module_manager(
    registry,
    scan_paths: Optional[list] = None,
) -> "ModuleManager":
    """Initialize ModuleManager and start all discovered modules."""
    from core.system.module_manager import ModuleManager

    if scan_paths is None:
        scan_paths = [Path(__file__).resolve().parent.parent / "modules"]
    manager = ModuleManager(registry=registry, scan_paths=scan_paths)
    await manager.start()

    # Wire modules that provide services into the ServiceRegistry
    registry.register("module_manager", manager)
    for name, entry in manager.list_modules().items():
        registry.register(f"module.{name}", entry.instance)
    logger.info(f"[ModuleManager] {len(manager.list_modules())} modules started and registered")
    return manager
