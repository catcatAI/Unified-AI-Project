"""
ANGELA-MATRIX: [L3-L5] [βγ] [A] [L3]
Wiring module: cross-service dependency injection during startup.
"""

import asyncio
import logging
from datetime import datetime

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
        hot_reload = get_hot_reload_service()
        sec_audit = get_security_audit()
        logger.info("[Lifecycle] HotReloadService and SecurityAudit activated and ready.")
    except Exception as e:
        logger.warning(f"[Lifecycle] Failed to activate management assets: {e}", exc_info=True)

    async def pet_broadcast_wrapper(event_type, data):
        await manager.broadcast(
            {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    pet_manager.broadcast_callback = pet_broadcast_wrapper

    def bio_event_callback(event_name, event_data):
        try:
            loop = asyncio.get_event_loop()
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
            def _plugin_aware_callback(event_name, event_data):
                try:
                    import asyncio as _aio
                    _aio.ensure_future(
                        plugin_manager.execute_hook("on_bio_event", {
                            "event": event_name, "data": event_data
                        })
                    )
                except Exception:
                    pass
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
