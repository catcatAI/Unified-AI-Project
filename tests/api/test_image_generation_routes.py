"""
Tests for image_generation_routes API endpoints.

Covers:
- Route import and registration (5 /image/ routes)
- Error responses when models are unavailable
- Response model structure
"""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


def _raise_runtime(message: str):
    """Build a callable that raises RuntimeError(message) when called."""

    def _inner(*_args, **_kwargs):
        raise RuntimeError(message)

    return _inner


@pytest.mark.asyncio
class TestImageGenerationRoutes:
    """Verify route registration and structure."""

    async def test_module_importable(self):
        """Module imports without error."""
        from api.routes import image_generation_routes

        assert image_generation_routes is not None

    async def test_router_exported(self):
        """Module exports a router with routes."""
        from api.routes.image_generation_routes import router

        assert router is not None
        assert len(router.routes) >= 5  # At least 5 standardized routes

    async def test_has_standardized_endpoints(self):
        """Router has the new standardized /image/ endpoints."""
        from api.routes.image_generation_routes import router

        paths = {r.path for r in router.routes}
        standardized = {
            "/image/generate",
            "/image/recognize",
            "/image/reconstruct",
            "/image/interpolate",
            "/image/status",
        }
        for ep in standardized:
            assert ep in paths, f"Missing standardized endpoint: {ep}"

    async def test_router_http_methods(self):
        """Verify HTTP methods on each route."""
        from api.routes.image_generation_routes import router

        route_map = {}
        for r in router.routes:
            methods = set(r.methods) if hasattr(r, "methods") else {"GET"}
            route_map[r.path] = methods

        # Standardized POST endpoints
        assert "POST" in route_map.get("/image/generate", set())
        assert "POST" in route_map.get("/image/recognize", set())
        assert "POST" in route_map.get("/image/reconstruct", set())
        assert "POST" in route_map.get("/image/interpolate", set())
        assert "GET" in route_map.get("/image/status", set())


@pytest.mark.asyncio
class TestImageGenerationModels:
    """Verify behavior when models are unavailable."""

    async def test_generate_image_fails_when_pipeline_unavailable(self, monkeypatch):
        """POST /image/generate returns 503 when the GVV pipeline is unavailable.

        NOTE: this test used to pass *because* the route could never load the
        pipeline — its models_dir resolved to apps/models (one level too high),
        so every real call was a 503. The unavailability is now injected
        explicitly so the degradation contract stays covered independently of
        whether the model files are present on the machine running the tests.
        """
        import api.routes.image_generation_routes as routes

        monkeypatch.setattr(
            routes,
            "_generate_image",
            _raise_runtime("GVV pipeline not available"),
        )
        req = routes.GenerateImageRequest(text="test", canvas_size=128)
        with pytest.raises(HTTPException) as exc_info:
            await routes.image_generate(req)
        assert exc_info.value.status_code == 503

    async def test_generate_image_uses_the_pipeline_owner(self, monkeypatch):
        """The route delegates to gvv_generator instead of an inline pipeline."""
        import api.routes.image_generation_routes as routes

        seen = {}

        def _fake_generate(text, canvas_size, num_iterations, learning_rate):
            seen.update(
                text=text,
                canvas_size=canvas_size,
                num_iterations=num_iterations,
                learning_rate=learning_rate,
            )
            return {
                "image_base64": "QUJD",
                "width": 32,
                "height": 32,
                "metrics": {"concept": "circle"},
            }

        monkeypatch.setattr(routes, "_generate_image", _fake_generate)
        req = routes.GenerateImageRequest(text="a red circle", canvas_size=32)
        result = await routes.image_generate(req)

        assert seen["text"] == "a red circle"
        assert seen["canvas_size"] == 32
        assert result.image_base64 == "QUJD"
        assert result.metrics["concept"] == "circle"

    async def test_recognize_image_fails_without_gvv(self):
        """POST /image/recognize returns 503 when GVV pipeline not available."""
        from api.routes.image_generation_routes import RecognizeImageRequest, image_recognize

        req = RecognizeImageRequest(image_base64="AAAA")
        with pytest.raises(HTTPException) as exc_info:
            await image_recognize(req)
        assert exc_info.value.status_code in (503, 400)

    async def test_reconstruct_image_fails_without_model(self):
        """POST /image/reconstruct returns 503 when ThreeLayerVisual not available."""
        from api.routes.image_generation_routes import ReconstructImageRequest, image_reconstruct

        req = ReconstructImageRequest(image_base64="AAAA")
        with pytest.raises(HTTPException) as exc_info:
            await image_reconstruct(req)
        assert exc_info.value.status_code in (503, 500)

    async def test_interpolate_image_fails_without_model(self):
        """POST /image/interpolate returns 503 when ThreeLayerVisual not available."""
        from api.routes.image_generation_routes import InterpolateRequest, image_interpolate

        req = InterpolateRequest(class_a=0, class_b=1)
        with pytest.raises(HTTPException) as exc_info:
            await image_interpolate(req)
        assert exc_info.value.status_code in (503, 500)

    async def test_status_works_without_models(self):
        """GET /image/status returns status dict even without models."""
        from api.routes.image_generation_routes import image_status

        result = await image_status()
        assert isinstance(result, dict)
        assert "gvv_available" in result
        assert "three_layer_available" in result
        assert result["pipeline"] == "gvv"
        # Availability must reflect the real state of the pipeline owner, not a
        # hardcoded False: the model files ARE present in this repo, and status
        # must not trigger lazy initialization either.
        from ai.multimodal.generator import gvv_generator

        assert result["gvv_available"] is gvv_generator.gvv_initialized()
        assert isinstance(result["vocab_size"], int)
        assert isinstance(result["concept_count"], int)


@pytest.mark.asyncio
class TestImageGenerationResponseModels:
    """Verify Pydantic response models structure."""

    async def test_generate_image_response_model(self):
        """GenerateImageResponse has correct fields."""
        from api.routes.image_generation_routes import GenerateImageResponse

        fields = set(GenerateImageResponse.model_fields.keys())
        expected = {"image_base64", "width", "height", "metrics"}
        assert expected.issubset(fields), f"Missing fields: {expected - fields}"

    async def test_recognize_image_response_model(self):
        """RecognizeImageResponse has correct fields."""
        from api.routes.image_generation_routes import RecognizeImageResponse

        fields = set(RecognizeImageResponse.model_fields.keys())
        expected = {"predicted_class", "confidence", "class_scores"}
        assert expected.issubset(fields), f"Missing fields: {expected - fields}"

    async def test_reconstruct_image_response_model(self):
        """ReconstructImageResponse has correct fields."""
        from api.routes.image_generation_routes import ReconstructImageResponse

        fields = set(ReconstructImageResponse.model_fields.keys())
        expected = {"image_base64", "width", "height", "metrics"}
        assert expected.issubset(fields), f"Missing fields: {expected - fields}"

    async def test_interpolate_response_model(self):
        """InterpolateResponse has correct fields."""
        from api.routes.image_generation_routes import InterpolateResponse

        fields = set(InterpolateResponse.model_fields.keys())
        expected = {"images", "width", "height", "metrics"}
        assert expected.issubset(fields), f"Missing fields: {expected - fields}"

    async def test_generate_image_request_model(self):
        """GenerateImageRequest has correct fields with defaults."""
        from api.routes.image_generation_routes import GenerateImageRequest

        req = GenerateImageRequest(text="hello")
        assert req.text == "hello"
        assert req.canvas_size == 128  # default
        assert req.num_iterations == 30  # default
        assert req.learning_rate == 0.008  # default
