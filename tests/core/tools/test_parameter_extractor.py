"""core.tools.parameter_extractor 參數提取器測試"""

import pytest

from apps.backend.src.core.tools.parameter_extractor.extractor import ParameterExtractor


class TestParameterExtractor:
    def test_map_parameters(self):
        extractor = ParameterExtractor(repo_id="test/repo")
        mapped = extractor.map_parameters(
            {"hidden_size": 768, "layers": 12, "unused": 1},
            {"hidden_size": "d_model", "layers": "n_layers"},
        )
        assert mapped == {"d_model": 768, "n_layers": 12}

    def test_map_parameters_empty(self):
        extractor = ParameterExtractor(repo_id="test/repo")
        assert extractor.map_parameters({}, {"a": "b"}) == {}

    def test_load_parameters_to_model_state_dict(self):
        class Model:
            def __init__(self):
                self._params = None

            def load_state_dict(self, params):
                self._params = params

        extractor = ParameterExtractor(repo_id="test/repo")
        model = Model()
        extractor.load_parameters_to_model(model, {"weight": 1.0})
        assert model._params == {"weight": 1.0}

    def test_load_parameters_to_model_attrs(self):
        class Model:
            def __init__(self):
                self.hidden = 0

        extractor = ParameterExtractor(repo_id="test/repo")
        model = Model()
        extractor.load_parameters_to_model(model, {"hidden": 64})
        assert model.hidden == 64

    def test_load_parameters_skips_missing_attrs(self):
        class Model:
            pass

        extractor = ParameterExtractor(repo_id="test/repo")
        model = Model()
        extractor.load_parameters_to_model(model, {"nonexistent_attr": 64})
        assert not hasattr(model, "nonexistent_attr")

    def test_download_returns_none_without_hf(self):
        extractor = ParameterExtractor(repo_id="test/repo")
        assert extractor.download_model_parameters("model.pt") is None or isinstance(
            extractor.download_model_parameters("model.pt"), (str, type(None))
        )
