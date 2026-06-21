import io
import os
import tempfile

import numpy as np
import pytest
from PIL import Image
import wave


@pytest.fixture
def sample_image_bytes():
    img = Image.new("RGB", (64, 64), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_audio_bytes():
    n_samples = 8000
    samples = (np.sin(2 * np.pi * 440 * np.arange(n_samples) / 16000) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestMultimodalRetriever:

    @pytest.fixture
    def ret(self):
        from ai.multimodal.multimodal_retriever import MultimodalRetriever
        return MultimodalRetriever()

    def test_add_and_count(self, ret):
        assert ret.count() == 0
        ret.add("key1", np.ones(64, dtype=np.float32), "vision")
        assert ret.count() == 1

    def test_add_wrong_dim_ignored(self, ret):
        ret.add("bad", np.ones(10, dtype=np.float32))
        assert ret.count() == 0

    def test_search_returns_top_k(self, ret):
        rng = np.random.default_rng(42)
        for i in range(10):
            v = rng.normal(0, 1, 64).astype(np.float32)
            ret.add(f"key_{i}", v, "vision")
        query = ret.get_vector(0)
        results = ret.search(query, top_k=3)
        assert len(results) == 3
        assert results[0]["key"] == "key_0"
        assert results[0]["score"] >= results[1]["score"]

    def test_search_empty_returns_empty(self, ret):
        assert ret.search(np.ones(64)) == []

    def test_search_wrong_dim_returns_empty(self, ret):
        ret.add("k", np.ones(64, dtype=np.float32))
        assert ret.search(np.ones(10)) == []

    def test_search_by_modality_filter(self, ret):
        ret.add("v1", np.ones(64, dtype=np.float32), "vision")
        ret.add("a1", np.ones(64, dtype=np.float32), "audio")
        query = np.ones(64, dtype=np.float32)
        results = ret.search_by_modality(query, "audio", top_k=5)
        assert all(r["modality"] == "audio" for r in results)

    def test_search_by_list(self, ret):
        ret.add("k1", np.ones(64, dtype=np.float32))
        results = ret.search_by_list([1.0] * 64, top_k=1)
        assert len(results) == 1

    def test_clear(self, ret):
        ret.add("k", np.ones(64, dtype=np.float32))
        ret.clear()
        assert ret.count() == 0

    def test_save_load(self, ret):
        from ai.multimodal.multimodal_retriever import MultimodalRetriever
        ret.add("k1", np.ones(64, dtype=np.float32), "vision", {"label": "test"})
        ret.add("k2", np.zeros(64, dtype=np.float32), "audio")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "index.npy")
            ret.save(path)
            ret2 = MultimodalRetriever()
            n = ret2.load(path)
            assert n == 2
            assert ret2.get_key(0) == "k1"
            assert ret2.get_vector(1) is not None

    def test_save_load_empty(self, ret):
        from ai.multimodal.multimodal_retriever import MultimodalRetriever
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.npy")
            ret.save(path)
            ret2 = MultimodalRetriever()
            assert ret2.load(path) == 0


class TestMultimodalRAGEngine:

    @pytest.fixture
    def engine(self):
        from ai.multimodal.multimodal_rag_engine import MultimodalRAGEngine
        return MultimodalRAGEngine()

    def test_index_image(self, engine, sample_image_bytes):
        ok = engine.index_image(sample_image_bytes, "img_001", label="test")
        assert ok
        assert engine.retriever.count() == 1

    def test_index_audio(self, engine, sample_audio_bytes):
        ok = engine.index_audio(sample_audio_bytes, "aud_001", label="test")
        assert ok
        assert engine.retriever.count() == 1

    def test_index_invalid_image_returns_false(self, engine):
        ok = engine.index_image(b"", "bad")
        assert not ok

    def test_query_by_image(self, engine, sample_image_bytes):
        engine.index_image(sample_image_bytes, "img_001", label="test_img")
        results = engine.query_by_image(sample_image_bytes, top_k=3)
        assert len(results) >= 1
        assert results[0]["key"] == "img_001"
        assert "score" in results[0]

    def test_query_by_audio(self, engine, sample_audio_bytes):
        engine.index_audio(sample_audio_bytes, "aud_001", label="test_aud")
        results = engine.query_by_audio(sample_audio_bytes, top_k=3)
        assert len(results) >= 1
        assert results[0]["key"] == "aud_001"

    def test_cross_modal_query(self, engine, sample_image_bytes, sample_audio_bytes):
        engine.index_image(sample_image_bytes, "img_001", label="vision")
        engine.index_audio(sample_audio_bytes, "aud_001", label="audio")
        results = engine.query_by_image(sample_image_bytes, top_k=5)
        keys = [r["key"] for r in results]
        assert "img_001" in keys

    def test_to_ed3n_entries(self, engine, sample_image_bytes):
        engine.index_image(sample_image_bytes, "img_001", label="sunset")
        results = engine.query_by_image(sample_image_bytes, top_k=1)
        entries = engine.to_ed3n_entries(results)
        assert len(entries) == 1
        entry = entries[0]
        assert "key" in entry
        assert "surface_forms" in entry
        assert "contexts" in entry
        assert "confidence" in entry
        assert entry["key"] == "img_001"
        assert entry["surface_forms"]["en"] == "sunset"

    def test_retrieve_entries_unified(self, engine, sample_image_bytes):
        engine.index_image(sample_image_bytes, "img_001", label="test")
        entries = engine.retrieve_entries(image_data=sample_image_bytes, top_k=3)
        assert len(entries) >= 1

    def test_retrieve_entries_no_input_returns_empty(self, engine):
        assert engine.retrieve_entries() == []

    def test_save_load_index(self, engine, sample_image_bytes):
        from ai.multimodal.multimodal_rag_engine import MultimodalRAGEngine
        engine.index_image(sample_image_bytes, "img_001", label="test")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "rag_index.npy")
            engine.save_index(path)
            engine2 = MultimodalRAGEngine()
            n = engine2.load_index(path)
            assert n == 1

    def test_index_from_entry(self, engine):
        entry = {"key": "mm_vision_abc123", "value": "test"}
        latent = [0.5] * 64
        engine.index_from_entry(latent, entry)
        assert engine.retriever.count() == 1
