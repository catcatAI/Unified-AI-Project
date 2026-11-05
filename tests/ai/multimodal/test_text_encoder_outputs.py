"""TextEncoder must survive the transformers>=5 CLIP output shape.

Verified failure this guards (transformers 5.15.1): ``CLIPModel.get_text_features``
returns a ``BaseModelOutputWithPooling``, not a tensor.  ``encode_batch`` called
``text_features.cpu()``, raised AttributeError, logged a warning and returned
``None`` — ``encode()`` then returned an all-zero vector.  Every TextEncoder
consumer (multimodal bridge, ED3N text path, training pipeline) was silently
getting zeros.
"""

from unittest.mock import patch

import numpy as np
import pytest
from ai.multimodal.text_encoder import TextEncoder


class _FakeTensor:
    def __init__(self, arr: np.ndarray):
        self._arr = arr

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self._arr


class _PooledOutput:
    """Mimics transformers>=5 BaseModelOutputWithPooling."""

    def __init__(self, arr: np.ndarray):
        self.pooler_output = _FakeTensor(arr)


class _FakeProcessor:
    def __call__(self, **kwargs):
        n = len(kwargs.get("text", ["x"]))
        return {"input_ids": __import__("torch").zeros((n, 4), dtype=__import__("torch").long)}


class _FakeModel:
    def __init__(self, output):
        self._output = output

    def eval(self):
        return self

    def get_text_features(self, **kwargs):
        return self._output


@pytest.fixture(autouse=True)
def _torch_check_passes():
    with patch("ai.multimodal.text_encoder._check_torch_subprocess", return_value=True):
        yield


class TestTextEncoderOutputShapes:
    def test_pooled_output_object_yields_normalised_vectors(self):
        model = _FakeModel(_PooledOutput(np.ones((2, 512), dtype=np.float32)))
        encoder = TextEncoder()
        with patch.object(TextEncoder, "_get_clip", return_value=(model, _FakeProcessor())):
            vecs = encoder.encode_batch(["a cat", "a bus"])
        assert vecs is not None
        assert vecs.shape == (2, 512)
        assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-6)

    def test_plain_tensor_output_still_supported(self):
        import torch

        model = _FakeModel(torch.ones((2, 512)))
        encoder = TextEncoder()
        with patch.object(TextEncoder, "_get_clip", return_value=(model, _FakeProcessor())):
            vecs = encoder.encode_batch(["a cat", "a bus"])
        assert vecs is not None and vecs.shape == (2, 512)

    def test_encode_returns_a_real_not_zero_vector(self):
        model = _FakeModel(_PooledOutput(np.ones((1, 512), dtype=np.float32)))
        encoder = TextEncoder()
        with patch.object(TextEncoder, "_get_clip", return_value=(model, _FakeProcessor())):
            vec = encoder.encode("a cat")
        assert vec.shape == (512,)
        assert float(np.linalg.norm(vec)) == pytest.approx(1.0, abs=1e-6)

    def test_model_stays_on_cpu_by_default(self):
        # The device is only moved when the resolved accelerator exists; on a
        # CPU-only resolve the model must not be moved at all.
        encoder = TextEncoder()
        assert encoder._device == "cpu"
