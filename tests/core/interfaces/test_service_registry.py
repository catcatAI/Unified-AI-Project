"""ServiceRegistry unit tests — matches actual API (register/get/unregister/clear)."""

from core.interfaces.service_registry import get_registry


def test_registry_is_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_register_and_get_with_value():
    reg = get_registry()
    reg.register("test_val", 42)
    assert reg.get("test_val") == 42
    reg.unregister("test_val")


def test_register_overwrites_existing():
    reg = get_registry()
    reg.register("overwrite_test", 1)
    reg.register("overwrite_test", 2)
    assert reg.get("overwrite_test") == 2
    reg.unregister("overwrite_test")


def test_register_and_get_with_object():
    reg = get_registry()
    obj = {"key": "value"}
    reg.register("test_obj", obj)
    assert reg.get("test_obj") is obj
    reg.unregister("test_obj")


def test_get_nonexistent_returns_none():
    reg = get_registry()
    assert reg.get("nonexistent_key") is None


def test_unregister_nonexistent_does_not_raise():
    reg = get_registry()
    reg.unregister("key_that_never_existed")


def test_clear_removes_all():
    reg = get_registry()
    reg.register("a", 1)
    reg.register("b", 2)
    reg.clear()
    assert reg.get("a") is None
    assert reg.get("b") is None


def test_get_with_type_check():
    reg = get_registry()
    reg.register("typed_val", 42)
    assert reg.get("typed_val", expected_type=int) == 42
    reg.unregister("typed_val")


def test_register_and_get_multiple():
    reg = get_registry()
    reg.register("svc_a", "alpha")
    reg.register("svc_b", "beta")
    assert reg.get("svc_a") == "alpha"
    assert reg.get("svc_b") == "beta"
    reg.clear()
