"""primitives 组件与 shared_latent_space 单例重设测试"""

import numpy as np

from apps.backend.src.ai.multimodal.primitives.learnable_decomposer import LearnableDecomposer
from apps.backend.src.ai.multimodal.primitives.pixel_refiner import PixelRefiner
from apps.backend.src.ai.multimodal.shared_latent_space import (
    get_shared_latent_space,
    reset_shared_latent_space,
)


class TestLearnableDecomposer:
    def test_init(self):
        dec = LearnableDecomposer()
        assert hasattr(dec, "forward")
        assert hasattr(dec, "save")
        assert hasattr(dec, "load")

    def test_forward_returns_prediction_and_cache(self):
        dec = LearnableDecomposer()
        clip_emb = np.random.randn(512).astype(np.float32)
        sig, cache = dec.forward(clip_emb)
        assert sig.shape == (263,)
        assert 0.0 <= sig.min() and sig.max() <= 1.0
        assert set(["x", "z1", "h", "z2", "sig"]).issubset(cache.keys())

    def test_forward_deterministic(self):
        dec = LearnableDecomposer()
        clip_emb = np.random.randn(512).astype(np.float32)
        sig1, _ = dec.forward(clip_emb)
        sig2, _ = dec.forward(clip_emb)
        assert np.array_equal(sig1, sig2)


class TestPixelRefiner:
    def test_init(self):
        refiner = PixelRefiner()
        assert hasattr(refiner, "forward")
        assert hasattr(refiner, "refine")
        assert hasattr(refiner, "save")

    def test_forward_shape_and_range(self):
        refiner = PixelRefiner()
        rough_flat = np.random.rand(128 * 128 * 3).astype(np.float32) * 255.0
        refined = refiner.forward(rough_flat)
        assert refined.shape == (128 * 128 * 3,)
        assert refined.dtype == np.uint8
        assert refined.max() <= 255

    def test_refine_pil_roundtrip(self):
        from PIL import Image

        refiner = PixelRefiner()
        rough = Image.new("RGB", (128, 128), (128, 128, 128))
        refined = refiner.refine(rough)
        assert refined.size == (128, 128)


class TestResetSharedLatentSpace:
    def test_reset_returns_none_and_singleton_recreated(self):
        before = get_shared_latent_space()
        assert before is not None
        result = reset_shared_latent_space()
        assert result is None
        after = get_shared_latent_space()
        assert after is not None
        assert isinstance(after, type(before))
