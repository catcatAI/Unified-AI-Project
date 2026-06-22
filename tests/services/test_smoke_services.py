"""P10-1: Smoke tests for service modules — verify importability."""


def test_import_websocket_manager():
    from services.websocket_manager import ConnectionManager
    m = ConnectionManager()
    assert m is not None


def test_import_math_verifier():
    from services.math_verifier import MathVerifier
    v = MathVerifier()
    assert v is not None


def test_import_vision_service():
    from services.vision_service import VisionService
    assert VisionService is not None
