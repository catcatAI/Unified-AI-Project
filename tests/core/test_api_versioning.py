"""core.api.versioning API 版本中间件与 header 工具测试"""

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from apps.backend.src.core.api.versioning import (
    APIVersionMiddleware,
    add_deprecation_header,
    add_version_header,
)


def _make_client():
    app = FastAPI()
    app.add_middleware(APIVersionMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    return TestClient(app)


class TestAPIVersionMiddleware:
    def test_default_version(self):
        client = _make_client()
        resp = client.get("/ping")
        assert resp.status_code == 200
        assert resp.headers["x-api-version"] == "v1"
        assert resp.headers["x-api-supported-versions"] == "v1"

    def test_query_param_version(self):
        client = _make_client()
        resp = client.get("/ping?version=v1")
        assert resp.status_code == 200
        assert resp.headers["x-api-version"] == "v1"

    def test_unsupported_version_rejected(self):
        client = _make_client()
        resp = client.get("/ping?version=v99")
        assert resp.status_code == 400

    def test_accept_header_version(self):
        client = _make_client()
        resp = client.get("/ping", headers={"Accept": "application/vnd.angela.v1+json"})
        assert resp.status_code == 200
        assert resp.headers["x-api-version"] == "v1"

    def test_request_state_set(self):
        from fastapi import Request

        app = FastAPI()
        app.add_middleware(APIVersionMiddleware)

        @app.get("/state")
        async def state(request: Request):
            return {"api_version": request.state.api_version}

        client = TestClient(app)
        resp = client.get("/state")
        assert resp.json() == {"api_version": "v1"}


class TestAddVersionHeader:
    def test_sets_header(self):
        response = Response()
        add_version_header(response, "v2")
        assert response.headers["x-api-version"] == "v2"


class TestAddDeprecationHeader:
    def test_sets_deprecation_headers(self):
        response = Response()
        add_deprecation_header(response, "v1")
        assert response.headers["Deprecation"] == "true"
        assert response.headers["Sunset"] == "2027-01-01"
        assert "v1" in response.headers["x-api-deprecation-notice"]

    def test_custom_sunset_date(self):
        response = Response()
        add_deprecation_header(response, "v0", sunset_date="2030-01-01")
        assert response.headers["Sunset"] == "2030-01-01"
