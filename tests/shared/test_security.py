import logging

logger = logging.getLogger(__name__)

from apps.backend.src.core.system.security_monitor import ABCKeyManager


def test_keys():
    km = ABCKeyManager()
    key_a = km.get_key("KeyA")
    key_b = km.get_key("KeyB")
    key_c = km.get_key("KeyC")

    assert isinstance(key_a, str) and len(key_a) > 0, "KeyA must be non-empty string"
    assert isinstance(key_b, str) and len(key_b) > 0, "KeyB must be non-empty string"
    assert isinstance(key_c, str) and len(key_c) > 0, "KeyC must be non-empty string"
    assert key_a != key_b, "KeyA and KeyB must be distinct"
    assert key_b != key_c, "KeyB and KeyC must be distinct"


if __name__ == "__main__":
    test_keys()
