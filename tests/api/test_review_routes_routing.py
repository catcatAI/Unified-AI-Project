"""
Review routes must be tested through real ASGI routing.

WHY: every existing review test called the handler coroutines directly
(``review_routes.get_composite_score()``), which can never notice that
``/review/{dimension}`` was declared *above* ``/review/score`` and
``/review/summary``. Starlette resolves in declaration order, so both literals
answered HTTP 400 "Unknown review dimension" in production while the code and the
docs advertised them as live. Route-order regressions are only visible through
the router, so this file does exactly that.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.fixture
def review_client(monkeypatch):
    """An ASGI client bound to a minimal app that mounts the review router.

    Uses the real router (not the individual handlers) so declaration order —
    and therefore path shadowing — is exercised.
    """
    import httpx
    from fastapi import FastAPI

    import api.routes.review_routes as review_routes

    class _StubReport:
        def __init__(self, dimension: str) -> None:
            self.dimension = dimension
            self.score = 7.5
            self.summary = f"{dimension} ok"

        def to_dict(self):
            return {"dimension": self.dimension, "score": self.score, "summary": self.summary}

    class _StubEngine:
        DIMENSIONS = ("design", "code", "markdown", "consistency", "training")

        def run_full_review(self):
            return {d: _StubReport(d) for d in self.DIMENSIONS}

        def run_review(self, dimension: str):
            if dimension not in self.DIMENSIONS:
                raise ValueError(
                    f"Unknown review dimension: {dimension}. "
                    f"Available: {list(self.DIMENSIONS)}"
                )
            return _StubReport(dimension)

        def get_composite_score(self, reports) -> float:
            return round(sum(r.score for r in reports.values()) / len(reports), 3)

        def generate_summary(self, reports) -> str:
            return " / ".join(f"{k}={v.score}" for k, v in reports.items())

    monkeypatch.setattr(review_routes, "_get_engine", lambda: _StubEngine())
    app = FastAPI()
    app.include_router(review_routes.router, prefix="/api/v1")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestReviewRouteResolution:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "path,expect_key",
        [
            ("/api/v1/review/score", "composite_score"),
            ("/api/v1/review/summary", "summary"),
        ],
    )
    async def test_literal_endpoints_are_not_shadowed(self, review_client, path, expect_key):
        async with review_client as client:
            resp = await client.get(path)
        assert resp.status_code == 200, f"{path} was shadowed: {resp.text}"
        body = resp.json()
        assert body["success"] is True
        assert expect_key in body

    @pytest.mark.asyncio
    async def test_catch_all_dimension_still_works(self, review_client):
        async with review_client as client:
            resp = await client.get("/api/v1/review/design")
        assert resp.status_code == 200
        assert resp.json()["report"]["dimension"] == "design"

    @pytest.mark.asyncio
    async def test_unknown_dimension_is_400_not_500(self, review_client):
        async with review_client as client:
            resp = await client.get("/api/v1/review/not-a-dimension")
        assert resp.status_code == 400
        assert "Unknown review dimension" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_full_review_endpoint(self, review_client):
        async with review_client as client:
            resp = await client.get("/api/v1/review/")
        assert resp.status_code == 200
        body = resp.json()
        assert "reports" in body and "composite_score" in body

    def test_catch_all_is_declared_after_literals(self):
        """Structural guard: the parameterized route must stay last."""
        from api.routes.review_routes import router

        order = [r.path for r in router.routes]
        assert order.index("/review/{dimension}") > order.index("/review/score")
        assert order.index("/review/{dimension}") > order.index("/review/summary")
