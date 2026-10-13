# =============================================================================
# ANGELA-MATRIX: [L1] [αβγδ] [A] [L0]
# =============================================================================
"""RealtimeSync wire-level event discriminators and module-control routing.

Regression coverage for three defects that used to cancel each other out:

* ``SyncEventType`` was integer-valued (``auto()``) but ``vision_service``
  built events by *value* — ``SyncEventType("module_control")`` raised
  ``ValueError`` on every dispatch.
* ``RealtimeSync.broadcast_event`` wrapped every client callback in
  ``try/except`` and only logged, so that ``ValueError`` was swallowed and the
  module on/off switch never reached either service.
* ``audio_service`` read ``event.type`` (the field is ``event_type``), so its
  handler branch was dead code even once the enum was fixed.
"""

import asyncio
import uuid

import pytest
from core.sync.realtime_sync import SyncEvent, SyncEventType, sync_manager


def _event(event_type: SyncEventType, data: dict, source: str = "test") -> SyncEvent:
    return SyncEvent(id=str(uuid.uuid4()), event_type=event_type, data=data, source=source)


class TestSyncEventTypeDiscriminators:
    """``SyncEventType("<value>")`` must resolve for every emit-able kind."""

    @pytest.mark.parametrize(
        ("value", "member"),
        [
            ("status_change", "STATUS_CHANGE"),
            ("data_update", "DATA_UPDATE"),
            ("system_event", "SYSTEM_EVENT"),
            ("module_control", "MODULE_CONTROL"),
            ("wallpaper_object_injection", "WALLPAPER_OBJECT_INJECTION"),
        ],
    )
    def test_lookup_by_value(self, value, member):
        assert SyncEventType(value).name == member

    def test_module_control_value_is_wire_stable(self):
        assert SyncEventType.MODULE_CONTROL.value == "module_control"
        assert SyncEventType.WALLPAPER_OBJECT_INJECTION.value == "wallpaper_object_injection"

    def test_serialisation_uses_member_name(self):
        event = _event(SyncEventType.MODULE_CONTROL, {"module": "vision", "enabled": False})
        assert event.to_dict()["event_type"] == "MODULE_CONTROL"
        assert event.to_dict()["data"] == {"module": "vision", "enabled": False}

    def test_wallpaper_event_does_not_raise_in_vision_handler(self):
        """The wallpaper broadcast used to raise before leaving the service."""
        from services.vision_service import VisionService

        handler = VisionService.__new__(VisionService)
        handler.enabled = True
        event = _event(
            SyncEventType.WALLPAPER_OBJECT_INJECTION,
            {"name": "cat", "position": {"x": 1, "y": 2, "z": 0}},
            source="vision_service",
        )
        asyncio.run(VisionService._handle_sync_event(handler, event))
        assert handler.enabled is True  # unrelated event must not flip state


class TestModuleControlRouting:
    """The endpoint's event type and the services' expectations must agree."""

    @pytest.mark.asyncio
    async def test_vision_handler_toggles_on_module_control(self):
        from services.vision_service import VisionService

        vision = VisionService.__new__(VisionService)
        vision.enabled = True
        await VisionService._handle_sync_event(
            vision,
            _event(SyncEventType.MODULE_CONTROL, {"module": "vision", "enabled": False}),
        )
        assert vision.enabled is False

        await VisionService._handle_sync_event(
            vision,
            _event(SyncEventType.MODULE_CONTROL, {"module": "vision", "enabled": True}),
        )
        assert vision.enabled is True

    @pytest.mark.asyncio
    async def test_audio_handler_ignores_other_modules(self):
        from services.audio_service import AudioService

        audio = AudioService.__new__(AudioService)
        audio.enabled = True
        await AudioService._handle_sync_event(
            audio,
            _event(SyncEventType.MODULE_CONTROL, {"module": "vision", "enabled": False}),
        )
        assert audio.enabled is True

        await AudioService._handle_sync_event(
            audio,
            _event(SyncEventType.MODULE_CONTROL, {"module": "audio", "enabled": False}),
        )
        assert audio.enabled is False

    @pytest.mark.asyncio
    async def test_endpoint_emits_module_control_event(self):
        """``mobile.py`` must emit the discriminator vision/audio listen for."""
        from unittest.mock import AsyncMock, patch

        from api.v1.endpoints import mobile

        captured: dict = {}

        def _capture(event):
            captured["event"] = event

        with patch("core.sync.realtime_sync.sync_manager") as mock_sm:
            mock_sm.broadcast_event = AsyncMock(side_effect=_capture)
            result = await mobile.mobile_module_control({"module": "vision", "enabled": False})

        assert result["status"] == "success"
        event = captured["event"]
        assert event.event_type is SyncEventType.MODULE_CONTROL
        assert event.data == {"module": "vision", "enabled": False}

        # and that discriminator must actually reach the consumer branches
        from services.audio_service import AudioService
        from services.vision_service import VisionService

        vision = VisionService.__new__(VisionService)
        vision.enabled = True
        audio = AudioService.__new__(AudioService)
        audio.enabled = True
        await VisionService._handle_sync_event(vision, event)
        await AudioService._handle_sync_event(audio, event)
        assert vision.enabled is False
        assert audio.enabled is True  # "audio" module untouched

    @pytest.mark.asyncio
    async def test_broadcast_reaches_every_registered_client(self):
        seen: list = []

        async def _probe(event):
            seen.append(event)

        await sync_manager.initialize()
        await sync_manager.register_client("_test_probe", _probe)
        try:
            await sync_manager.broadcast_event(
                _event(SyncEventType.MODULE_CONTROL, {"module": "audio", "enabled": False})
            )
        finally:
            await sync_manager.unregister_client("_test_probe")

        assert len(seen) == 1
        assert seen[0].event_type is SyncEventType.MODULE_CONTROL

    @pytest.mark.asyncio
    async def test_broken_client_does_not_stop_the_broadcast(self):
        """A failing client must not prevent later clients from being notified."""
        seen: list = []

        async def _boom(event):
            raise RuntimeError("deliberate client failure")

        async def _probe(event):
            seen.append(event)

        await sync_manager.initialize()
        await sync_manager.register_client("_test_boom", _boom)
        await sync_manager.register_client("_test_probe_ok", _probe)
        try:
            await sync_manager.broadcast_event(_event(SyncEventType.SYSTEM_EVENT, {}))
        finally:
            await sync_manager.unregister_client("_test_boom")
            await sync_manager.unregister_client("_test_probe_ok")

        assert len(seen) == 1


class TestModuleControlEndToEnd:
    """The wire, the endpoint and the service instance must be connected.

    The unit tests above prove each hop in isolation; this one proves they are
    actually joined in a running app.  They were not: VisionService and
    AudioService construct at *import* time with no event loop, so their
    ``create_task(_init_sync_listener())`` was skipped, ``sync_manager._clients``
    stayed empty and ``POST /mobile/module-control`` broadcast to nobody.
    """

    def test_listeners_are_registered_at_startup(self):
        from core.sync.realtime_sync import sync_manager
        from fastapi.testclient import TestClient
        from services.main_api_server import app

        with TestClient(app):
            clients = sync_manager.get_status()["clients"]
            assert "vision_service" in clients, "vision never subscribed to sync events"
            assert "audio_service" in clients, "audio never subscribed to sync events"
            assert sync_manager.get_status()["initialized"] is True

    def test_module_control_reaches_the_live_vision_instance(self):
        from api.v1.endpoints import vision as vision_ep
        from fastapi.testclient import TestClient
        from services.main_api_server import app

        with TestClient(app) as client:
            original = vision_ep._vision_service.enabled
            try:
                r = client.post(
                    "/api/v1/mobile/module-control",
                    json={"module": "vision", "enabled": False},
                )
                assert r.status_code == 200
                assert r.json()["status"] == "success"
                assert (
                    vision_ep._vision_service.enabled is False
                ), "module-control broadcast never reached the vision service"

                # and a status probe must not silently flip it back on
                probe = client.get("/api/v1/vision/control")
                assert probe.status_code == 200
                assert probe.json()["enabled"] is False

                r_on = client.post(
                    "/api/v1/mobile/module-control",
                    json={"module": "vision", "enabled": True},
                )
                assert r_on.status_code == 200
                assert vision_ep._vision_service.enabled is True
            finally:
                vision_ep._vision_service.set_enabled(original)
