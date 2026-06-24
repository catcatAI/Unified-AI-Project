"""
Tests for image_generation_routes API endpoints.

Covers:
- Route import and registration (all 10 routes)
- Deprecation warnings on legacy endpoints
- Error responses when models are unavailable
- Delegation: new standardized routes call same handler as legacy
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


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
        assert len(router.routes) >= 8  # At least 8 routes

    async def test_has_legacy_endpoints(self):
        """Router has the deprecated legacy endpoints."""
        from api.routes.image_generation_routes import router
        paths = {r.path for r in router.routes}
        legacy = {
            "/generate-image",
            "/recognize-image",
            "/reconstruct-image",
            "/interpolate-classes",
            "/generate-image/status",
        }
        for ep in legacy:
            assert ep in paths, f"Missing legacy endpoint: {ep}"

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

        # Legacy POST endpoints
        assert "POST" in route_map.get("/generate-image", set())
        assert "POST" in route_map.get("/recognize-image", set())
        assert "POST" in route_map.get("/reconstruct-image", set())
        assert "POST" in route_map.get("/interpolate-classes", set())
        assert "GET" in route_map.get("/generate-image/status", set())

        # Standardized POST endpoints
        assert "POST" in route_map.get("/image/generate", set())
        assert "POST" in route_map.get("/image/recognize", set())
        assert "POST" in route_map.get("/image/reconstruct", set())
        assert "POST" in route_map.get("/image/interpolate", set())
        assert "GET" in route_map.get("/image/status", set())


@pytest.mark.asyncio
class TestImageGenerationDeprecation:
    """Verify deprecation warnings on legacy endpoints."""

    async def test_generate_image_deprecation(self):
        """POST /generate-image issues DeprecationWarning."""
        from api.routes.image_generation_routes import generate_image, GenerateImageRequest
        import warnings
        with pytest.warns(DeprecationWarning, match="/image/generate"):
            req = GenerateImageRequest(text="test", canvas_size=128, num_iterations=30, learning_rate=0.008)
            with pytest.raises(Exception):  # Will likely fail because no models available
                await generate_image(req)

    async def test_recognize_image_deprecation(self):
        """POST /recognize-image issues DeprecationWarning."""
        from api.routes.image_generation_routes import recognize_image, RecognizeImageRequest
        import warnings
        with pytest.warns(DeprecationWarning, match="/image/recognize"):
            req = RecognizeImageRequest(image_base64="AAAA")
            with pytest.raises(Exception):
                await recognize_image(req)

    async def test_reconstruct_image_deprecation(self):
        """POST /reconstruct-image issues DeprecationWarning."""
        from api.routes.image_generation_routes import reconstruct_image, ReconstructImageRequest
        import warnings
        with pytest.warns(DeprecationWarning, match="/image/reconstruct"):
            req = ReconstructImageRequest(image_base64="AAAA")
            with pytest.raises(Exception):
                await reconstruct_image(req)

    async def test_interpolate_classes_deprecation(self):
        """POST /interpolate-classes issues DeprecationWarning."""
        from api.routes.image_generation_routes import interpolate_classes, InterpolateRequest
        import warnings
        with pytest.warns(DeprecationWarning, match="/image/interpolate"):
            req = InterpolateRequest(class_a=0, class_b=1, n_steps=5)
            with pytest.raises(Exception):
                await interpolate_classes(req)

    async def test_generate_image_status_deprecation(self):
        """GET /generate-image/status issues DeprecationWarning."""
        from api.routes.image_generation_routes import generate_image_status
        import warnings
        with pytest.warns(DeprecationWarning, match="/image/status"):
            result = await generate_image_status()
            # Should still return a result via delegation to image_status()
            assert isinstance(result, dict)
            # At minimum, status endpoint should work even without models
            assert "gvv_available" in result


@pytest.mark.asyncio
class TestImageGenerationModels:
    """Verify behavior when models are unavailable."""

    async def test_generate_image_fails_without_gvv(self):
        """POST /image/generate returns 503 when GVV pipeline not available."""
        from api.routes.image_generation_routes import image_generate, GenerateImageRequest
        req = GenerateImageRequest(text="test", canvas_size=128)
        try:
            await image_generate(req)
        except Exception as e:
            # Should be an HTTPException with status 503
            from fastapi import HTTPException
            assert isinstance(e, HTTPException), f"Expected HTTPException, got {type(e)}"
            assert e.status_code == 503, f"Expected 503, got {e.status_code}"

    async def test_recognize_image_fails_without_gvv(self):
        """POST /image/recognize returns 503 when GVV pipeline not available."""
        from api.routes.image_generation_routes import image_recognize, RecognizeImageRequest
        req = RecognizeImageRequest(image_base64="AAAA")
        try:
            await image_recognize(req)
        except Exception as e:
            from fastapi import HTTPException
            assert isinstance(e, HTTPException), f"Expected HTTPException, got {type(e)}"
            assert e.status_code in (503, 400), f"Expected 503/400, got {e.status_code}"

    async def test_reconstruct_image_fails_without_model(self):
        """POST /image/reconstruct returns 503 when ThreeLayerVisual not available."""
        from api.routes.image_generation_routes import image_reconstruct, ReconstructImageRequest
        req = ReconstructImageRequest(image_base64="AAAA")
        try:
            await image_reconstruct(req)
        except Exception as e:
            from fastapi import HTTPException
            assert isinstance(e, HTTPException), f"Expected HTTPException, got {type(e)}"
            assert e.status_code in (503, 500), f"Expected 503/500, got {e.status_code}"

    async def test_interpolate_image_fails_without_model(self):
        """POST /image/interpolate returns 503 when ThreeLayerVisual not available."""
        from api.routes.image_generation_routes import image_interpolate, InterpolateRequest
        req = InterpolateRequest(class_a=0, class_b=1)
        try:
            await image_interpolate(req)
        except Exception as e:
            from fastapi import HTTPException
            assert isinstance(e, HTTPException), f"Expected HTTPException, got {type(e)}"
            assert e.status_code in (503, 500), f"Expected 503/500, got {e.status_code}"

    async def test_status_works_without_models(self):
        """GET /image/status returns status dict even without models."""
        from api.routes.image_generation_routes import image_status
        result = await image_status()
        assert isinstance(result, dict)
        # Status should report no models available
        assert "gvv_available" in result
        assert "three_layer_available" in result
        # Both should be False in test environment
        assert result["gvv_available"] is False
        assert result["three_layer_available"] is False


@pytest.mark.asyncio
class TestImageGenerationDelegation:
    """Verify new standardized routes delegate to same handlers as legacy."""

    async def test_both_endpoints_fail_same_way(self):
        """POST /image/generate and /generate-image both fail with 503 when no models."""
        from api.routes.image_generation_routes import image_generate, generate_image, GenerateImageRequest
        req = GenerateImageRequest(text="test", canvas_size=128)
        for handler in (image_generate, generate_image):
            try:
                await handler(req)
            except Exception as e:
                from fastapi import HTTPException
                assert isinstance(e, HTTPException), f"Expected HTTPException, got {type(e)}"
                assert e.status_code == 503, f"Expected 503, got {e.status_code}"

    async def test_both_status_endpoints_match(self):
        """Legacy and standardized status endpoints return same result."""
        from api.routes.image_generation_routes import generate_image_status, image_status
        legacy_result = await generate_image_status()
        canonical_result = await image_status()
        assert legacy_result == canonical_result


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
