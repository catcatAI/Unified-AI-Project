from apps.backend.src.core.system.module_manager.events import EventBus, HealthMonitor
from apps.backend.src.core.system.module_manager.models import ModuleStatus, HealthStatus


def test_event_bus_subscribe_and_emit():
    bus = EventBus()
    received = []

    def handler(**data):
        received.append(data)

    bus.on("test.event", handler)
    bus.emit("test.event", key="value", num=42)
    assert len(received) == 1
    assert received[0] == {"key": "value", "num": 42}


def test_event_bus_multiple_handlers():
    bus = EventBus()
    results = []

    def h1(**data):
        results.append("h1")

    def h2(**data):
        results.append("h2")

    bus.on("test.event", h1)
    bus.on("test.event", h2)
    bus.emit("test.event")
    assert results == ["h1", "h2"]


def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    def handler(**data):
        received.append(True)

    bus.on("test.event", handler)
    bus.off("test.event", handler)
    bus.emit("test.event")
    assert received == []


def test_event_bus_no_handlers():
    bus = EventBus()
    bus.emit("nonexistent.event")


def test_event_bus_clear():
    bus = EventBus()
    results = []

    def h1(**data):
        results.append("h1")

    def h2(**data):
        results.append("h2")

    bus.on("event.a", h1)
    bus.on("event.b", h2)
    bus.clear()
    bus.emit("event.a")
    bus.emit("event.b")
    assert results == []


def test_event_bus_multiple_events():
    bus = EventBus()
    received_a = []
    received_b = []

    def handler_a(**data):
        received_a.append(data)

    def handler_b(**data):
        received_b.append(data)

    bus.on("event.a", handler_a)
    bus.on("event.b", handler_b)
    bus.emit("event.a", x=1)
    bus.emit("event.b", y=2)
    assert len(received_a) == 1
    assert received_a[0] == {"x": 1}
    assert len(received_b) == 1
    assert received_b[0] == {"y": 2}


def test_health_monitor_check_ok():
    bus = EventBus()
    hm = HealthMonitor(bus)
    hm.check("test", ModuleStatus.RUNNING, alive=True)
    hs = hm.get_status("test")
    assert hs is not None
    assert hs.alive is True
    assert hs.status == ModuleStatus.RUNNING


def test_health_monitor_check_fail():
    bus = EventBus()
    hm = HealthMonitor(bus)
    hm.check("test", ModuleStatus.DEAD, alive=False, error="crashed")
    hs = hm.get_status("test")
    assert hs is not None
    assert hs.alive is False
    assert hs.status == ModuleStatus.DEAD
    assert hs.error == "crashed"


def test_health_monitor_get_status():
    bus = EventBus()
    hm = HealthMonitor(bus)
    hm.check("mod_a", ModuleStatus.RUNNING, alive=True)
    hs = hm.get_status("mod_a")
    assert isinstance(hs, HealthStatus)
    assert hs.name == "mod_a"
    assert hm.get_status("nonexistent") is None


def test_health_monitor_get_all_statuses():
    bus = EventBus()
    hm = HealthMonitor(bus)
    hm.check("mod_a", ModuleStatus.RUNNING, alive=True)
    hm.check("mod_b", ModuleStatus.STOPPED, alive=False)
    all_statuses = hm.get_all_statuses()
    assert len(all_statuses) == 2
    assert "mod_a" in all_statuses
    assert "mod_b" in all_statuses
    assert all_statuses["mod_a"].alive is True
    assert all_statuses["mod_b"].alive is False


def test_health_monitor_event_on_ok():
    bus = EventBus()
    hm = HealthMonitor(bus)
    received = []

    def handler(**data):
        received.append(data)

    bus.on("test.health_ok", handler)
    hm.check("test", ModuleStatus.RUNNING, alive=True)
    assert len(received) == 1
    assert "status" in received[0]
    assert received[0]["status"].alive is True


def test_health_monitor_event_on_fail():
    bus = EventBus()
    hm = HealthMonitor(bus)
    received = []

    def handler(**data):
        received.append(data)

    bus.on("test.health_fail", handler)
    hm.check("test", ModuleStatus.DEAD, alive=False, error="timeout")
    assert len(received) == 1
    assert "status" in received[0]
    assert received[0]["status"].alive is False
    assert received[0]["status"].error == "timeout"
