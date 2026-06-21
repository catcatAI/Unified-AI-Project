"""Tests for MultimodalED3NAdapter — ED3N bidirectional wiring."""

import numpy as np
import pytest


@pytest.fixture
def adapter():
    from ai.multimodal.multimodal_ed3n_adapter import MultimodalED3NAdapter
    return MultimodalED3NAdapter()


class TestMultimodalED3NAdapter:

    def test_retrieve_returns_empty_on_no_query(self, adapter):
        entries = adapter.retrieve_multimodal()
        assert entries == []

    def test_inject_into_context_adds_multimodal_entries(self, adapter):
        ctx = {"existing": True}
        result = adapter.inject_into_context(ctx)
        assert result["existing"] is True
        assert "multimodal_entries" in result
        assert isinstance(result["multimodal_entries"], list)

    def test_inject_into_context_without_context(self, adapter):
        result = adapter.inject_into_context({})
        assert "multimodal_entries" in result

    def test_inject_into_context_none_context(self, adapter):
        result = adapter.inject_into_context(None)
        assert "multimodal_entries" in result

    def test_index_then_retrieve_by_latent(self, adapter):
        latent = [0.1] * 64
        adapter.index_image_for_retrieval(
            b"fake_image_data", key="test_img", label="test image",
            metadata={"source": "test"}
        )
        # Directly inject latent to make searchable
        adapter.rag_engine.index_latent(latent, "test_latent", modality="test",
                                        metadata={"label": "latent entry"})
        entries = adapter.retrieve_multimodal(latent=latent, top_k=5)
        assert len(entries) >= 1
        entry = entries[0]
        assert "key" in entry
        assert "surface_forms" in entry
        assert "contexts" in entry
        assert "confidence" in entry

    def test_index_image_for_retrieval(self, adapter):
        result = adapter.index_image_for_retrieval(
            b"test_image", "img_001", label="test"
        )
        assert result is False  # dummy image data fails encoding

    def test_index_audio_for_retrieval(self, adapter):
        # May succeed or fail depending on encoder's PCM detection;
        # ensure no exception is raised
        adapter.index_audio_for_retrieval(
            b"test_audio", "aud_001", label="test"
        )

    def test_save_load_roundtrip(self, adapter, tmp_path):
        fpath = str(tmp_path / "test_index.npy")
        adapter.save_index(fpath)
        count = adapter.load_index(fpath)
        assert count == 0

    def test_rag_engine_property(self, adapter):
        from ai.multimodal.multimodal_rag_engine import MultimodalRAGEngine
        assert isinstance(adapter.rag_engine, MultimodalRAGEngine)

    def test_to_ed3n_entries_format(self, adapter):
        entries = adapter.retrieve_multimodal(latent=[0.5] * 64, top_k=3)
        for e in entries:
            assert "surface_forms" in e
            assert isinstance(e["surface_forms"], dict)
            assert "contexts" in e
            assert isinstance(e["contexts"], list)
            assert "confidence" in e
            assert 0.0 <= e["confidence"] <= 1.0


class TestED3NEngineAdapterWiring:

    def test_set_multimodal_adapter(self):
        from ai.ed3n.ed3n_engine import ED3NEngine
        from ai.multimodal.multimodal_ed3n_adapter import MultimodalED3NAdapter
        engine = ED3NEngine(auto_load_presets=False, auto_load_dictionaries=False)
        adapter = MultimodalED3NAdapter()
        engine.set_multimodal_adapter(adapter)
        assert engine.multimodal_adapter is adapter

    def test_process_multimodal_with_adapter_no_crash(self):
        from ai.ed3n.ed3n_engine import ED3NEngine
        from ai.multimodal.multimodal_ed3n_adapter import MultimodalED3NAdapter
        engine = ED3NEngine(auto_load_presets=False, auto_load_dictionaries=False)
        engine.set_multimodal_adapter(MultimodalED3NAdapter())
        result = engine.process_multimodal(text="hello", image_data=b"test_img")
        assert isinstance(result, str)
        assert len(result) > 0