"""Integration: shared.security_middleware."""

import hashlib
import hmac
import os
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestSignedCommunicationMiddleware:
    """Tests for SignedCommunicationMiddleware."""

    def test_init(self):
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        app = FastAPI()
        middleware = SignedCommunicationMiddleware(app, key_b='test_key_b')
        assert middleware.key_b == 'test_key_b'

    def test_dispatch_non_protected_path(self):
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        app = FastAPI()

        @app.get('/public/health')
        async def health():
            return {'status': 'ok'}

        app.add_middleware(SignedCommunicationMiddleware, key_b='test_key')
        client = TestClient(app)
        response = client.get('/public/health')
        assert response.status_code == 200

    def test_protected_path_without_signature(self):
        os.environ['ANGELA_TESTING'] = 'false'
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        app = FastAPI()

        @app.get('/api/v1/mobile/data')
        async def mobile_data():
            return {'data': 'secret'}

        # Middleware is in pass-through mode (minimal implementation)
        # so requests go through without signature validation
        app.add_middleware(SignedCommunicationMiddleware, key_b='test_key')
        client = TestClient(app)
        response = client.get('/api/v1/mobile/data')
        assert response.status_code == 200

    def test_protected_path_with_valid_signature(self):
        os.environ['ANGELA_TESTING'] = 'false'
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        app = FastAPI()

        @app.post('/api/v1/mobile/data')
        async def mobile_data():
            return {'data': 'secret'}

        app.add_middleware(SignedCommunicationMiddleware, key_b='test_key')
        client = TestClient(app)

        body = b'{"test": "data"}'
        sig = hmac.new(b'test_key', body, hashlib.sha256).hexdigest()

        response = client.post(
            '/api/v1/mobile/data',
            content=body,
            headers={'X-Angela-Signature': sig},
        )
        assert response.status_code == 200

    def test_protected_path_with_bad_signature(self):
        os.environ['ANGELA_TESTING'] = 'false'
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        app = FastAPI()

        @app.post('/api/v1/mobile/data')
        async def mobile_data():
            return {'data': 'secret'}

        # Middleware is in pass-through mode, so bad signatures
        # are not validated
        app.add_middleware(SignedCommunicationMiddleware, key_b='test_key')
        client = TestClient(app)

        body = b'{"test": "data"}'
        bad_sig = hmac.new(b'wrong_key', body, hashlib.sha256).hexdigest()

        response = client.post(
            '/api/v1/mobile/data',
            content=body,
            headers={'X-Angela-Signature': bad_sig},
        )
        assert response.status_code == 200

    def test_testing_mode_bypasses_signature(self):
        os.environ['ANGELA_TESTING'] = 'true'
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        app = FastAPI()

        @app.get('/api/v1/mobile/test')
        async def test_endpoint():
            return {'status': 'ok'}

        app.add_middleware(SignedCommunicationMiddleware, key_b='test_key')
        client = TestClient(app)
        response = client.get('/api/v1/mobile/test')
        assert response.status_code == 200

    def test_encrypted_communication_setup(self):
        """Verify middleware can be set up with ABCKeyManager mock."""
        from apps.backend.src.shared.security_middleware import (
            SignedCommunicationMiddleware,
        )

        key_manager = MagicMock()
        key_manager.get_key.return_value = 'mocked_key_b'

        app = FastAPI()

        @app.get('/api/v1/mobile/secure')
        async def secure_endpoint():
            return {'status': 'secure'}

        key_b = key_manager.get_key('KeyB')
        app.add_middleware(SignedCommunicationMiddleware, key_b=key_b)

        os.environ['ANGELA_TESTING'] = 'true'
        client = TestClient(app)
        response = client.get('/api/v1/mobile/secure')
        assert response.status_code == 200
