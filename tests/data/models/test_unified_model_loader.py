"""data.models.unified_model_loader 統一模型載入器測試"""

from apps.backend.src.data.models.unified_model_loader import UnifiedModelLoader


class TestUnifiedModelLoader:
    def test_load_creates_handle(self):
        instance = UnifiedModelLoader.load_model("model_a")
        assert instance is not None
        assert instance.model_name == "model_a"

    def test_load_returns_same_instance(self):
        a1 = UnifiedModelLoader.load_model("model_b")
        a2 = UnifiedModelLoader.load_model("model_b")
        assert a1 is a2

    def test_load_with_path_and_kwargs(self):
        instance = UnifiedModelLoader.load_model("model_c", "/path/to/model", lr=0.01)
        assert instance.model_path == "/path/to/model"
        assert instance.parameters == {"lr": 0.01}

    def test_unload_model(self):
        UnifiedModelLoader.load_model("model_d")
        assert UnifiedModelLoader.unload_model("model_d") is True
        assert UnifiedModelLoader.unload_model("model_d") is False

    def test_get_loaded_models(self):
        UnifiedModelLoader.load_model("model_e")
        models = UnifiedModelLoader.get_loaded_models()
        assert "model_e" in models

    def test_register_loader(self):
        def my_loader(model_path=None, **kwargs):
            return {"custom": True, "path": model_path}

        UnifiedModelLoader.register_loader("custom_model", my_loader)
        instance = UnifiedModelLoader.load_model("custom_model", "/custom")
        assert instance == {"custom": True, "path": "/custom"}

    def test_cleanup(self):
        UnifiedModelLoader._instances.clear()
        UnifiedModelLoader._loaders.clear()
        assert UnifiedModelLoader.get_loaded_models() == {}
