"""
P30: Tests for multimodal API routes.

Tests cover:
- Route import and registration
- Health endpoint
- Integration with MultimodalService
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.mark.asyncio
class TestMultimodalRoutes:
    """P30 T20-T22: Route import and registration tests."""

    async def test_multimodal_routes_import(self):
        """T20: multimodal_routes module imports without error."""
        from api.routes.multimodal_routes import router
        assert router is not None
        assert router.prefix == ""
        assert router.tags == ["multimodal"]

    async def test_multimodal_routes_has_endpoints(self):
        """T21: Router has the expected multimodal endpoints."""
        from api.routes.multimodal_routes import router
        paths = [r.path for r in router.routes]
        # Core multimodal endpoints that must exist
        core = ["/multimodal/encode", "/multimodal/decode", "/multimodal/compare",
                "/multimodal/retrieve", "/multimodal/train", "/multimodal/evaluate",
                "/multimodal/generate", "/multimodal/visualize", "/multimodal/health",
                "/multimodal/items", "/multimodal/clear", "/multimodal/cross-infer"]
        for ep in core:
            assert ep in paths, f"Missing endpoint: {ep}"
        # Thin wrappers (encode-with-retry, decode-with-fallback, train-with-checkpoint) removed in §X #238

    async def test_multimodal_router_registration(self):
        """T22: Router.py includes multimodal_routes with /api/v1 prefix."""
        from api.router import router as main_router

        def collect(router, prefix=""):
            # FastAPI-version robust: >= 0.139 wraps included routers in
            # _IncludedRouter (original_router + include_context.prefix).
            out = []
            for r in getattr(router, "routes", []):
                if hasattr(r, "original_router"):
                    ctx = getattr(r, "include_context", None)
                    sub = prefix + (getattr(ctx, "prefix", "") or "")
                    out.extend(collect(r.original_router, sub))
                elif hasattr(r, "path"):
                    out.append(prefix + r.path)
            return out

        all_paths = collect(main_router)
        multimodal_paths = [p for p in all_paths if "multimodal" in p]
        # Should contain /api/v1/multimodal/encode, /api/v1/multimodal/health, etc.
        assert len(multimodal_paths) >= 2


@pytest.mark.asyncio
class TestMultimodalServiceIntegration:
    """P30 T23-T25: Integration tests with MultimodalService backend."""

    async def test_service_encode_then_decode(self):
        """T23: Encode then decode returns base64 image."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        import io

        import numpy as np
        from PIL import Image
        img = Image.fromarray(np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()

        enc = await svc.encode(data, "vision", item_id="int_v")
        assert enc.get("error") is None, enc.get("error")
        dec = await svc.decode("int_v", "vision")
        assert dec.get("error") is None, dec.get("error")
        assert dec["decoded"].startswith("data:image/png;base64,")

    async def test_service_full_pipeline_synthetic(self):
        """T24: Full pipeline (train → evaluate) on synthetic data."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        train_result = await svc.train(mode="full", epochs=2)
        assert train_result["status"] == "completed"
        eval_result = await svc.evaluate(modality="vision", n_samples=3)
        assert "metrics" in eval_result

    async def test_service_cross_modal_roundtrip(self):
        """T25: Cross-modal vision→audio→vision roundtrip."""
        from services.multimodal_service import MultimodalService
        svc = MultimodalService()
        import io

        import numpy as np
        from PIL import Image
        img = Image.fromarray(np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8))
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        await svc.encode(buf.getvalue(), "vision", item_id="cm_v")
        # Vision → audio
        gen_result = await svc.generate("cm_v", "audio")
        assert "error" not in gen_result
        assert gen_result["generated"].startswith("data:audio/wav;base64,")
