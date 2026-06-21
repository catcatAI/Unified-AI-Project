import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def encoder():
    from ai.multimodal.visual_encoder import VisualEncoder
    return VisualEncoder()


@pytest.fixture
def sample_image_bytes():
    img = Image.new("RGB", (64, 64), color=(128, 64, 32))
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestVisualEncoder:

    def test_encode_returns_vector(self, encoder, sample_image_bytes):
        vec = encoder.encode(sample_image_bytes)
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (256,)
        assert vec.dtype == np.float32

    def test_encode_empty_returns_zeros(self, encoder):
        vec = encoder.encode(b"")
        assert np.all(vec == 0.0)

    def test_encode_from_pil(self, encoder):
        img = Image.new("RGB", (32, 32), color=(255, 0, 0))
        vec = encoder.encode_from_pil(img)
        assert vec.shape == (256,)
        assert not np.all(vec == 0.0)

    def test_different_images_different_vectors(self, encoder):
        img1 = Image.new("RGB", (64, 64), color=(255, 0, 0))
        img2 = Image.new("RGB", (64, 64), color=(0, 255, 0))
        v1 = encoder.encode_from_pil(img1)
        v2 = encoder.encode_from_pil(img2)
        assert not np.allclose(v1, v2, atol=0.1)

    def test_vector_is_normalized(self, encoder, sample_image_bytes):
        vec = encoder.encode(sample_image_bytes)
        norm = np.linalg.norm(vec)
        assert norm > 0

    def test_same_image_same_vector(self, encoder, sample_image_bytes):
        v1 = encoder.encode(sample_image_bytes)
        v2 = encoder.encode(sample_image_bytes)
        assert np.allclose(v1, v2)
