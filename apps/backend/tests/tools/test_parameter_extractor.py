import unittest
from unittest.mock import patch, MagicMock

# 修复导入路径
from apps.backend.src.tools.parameter_extractor.extractor import ParameterExtractor

class TestParameterExtractor(unittest.TestCase):

    @patch('apps.backend.src.tools.parameter_extractor.extractor.hf_hub_download')
    def test_download_model_parameters(self, mock_hf_hub_download):
        # Arrange
        mock_hf_hub_download.return_value = "/fake/path/pytorch_model.bin"
        extractor = ParameterExtractor(repo_id="bert-base-uncased")

        # Act
        result = extractor.download_model_parameters(filename="pytorch_model.bin")

        # Assert
        mock_hf_hub_download.assert_called_once_with(
            repo_id="bert-base-uncased",
            filename="pytorch_model.bin",
            cache_dir="model_cache"  # 使用默认值
        )
        self.assertEqual(result, "/fake/path/pytorch_model.bin")

    def test_map_parameters(self):
        # Arrange
        extractor = ParameterExtractor(repo_id="bert-base-uncased")
        source_params = {
            "bert.embeddings.word_embeddings.weight": 1,
            "bert.pooler.dense.weight": 2,
            "bert.pooler.dense.bias": 3,
            "some.other.param": 4,
        }
        mapping_rules = {
            "bert.embeddings.word_embeddings.weight": "embeddings.weight",
            "bert.pooler.dense.weight": "pooler.weight",
        }

        # Act
        mapped_params = extractor.map_parameters(source_params, mapping_rules)

        # Assert
        expected_params = {
            "embeddings.weight": 1,
            "pooler.weight": 2,
        }
        self.assertEqual(mapped_params, expected_params)

    def test_load_parameters_to_model(self):
        # Arrange
        extractor = ParameterExtractor(repo_id="bert-base-uncased")
        model = MagicMock()
        model.load_state_dict = MagicMock()
        params = {"param1": 1, "param2": 2}

        # Act
        extractor.load_parameters_to_model(model, params)

        # Assert
        model.load_state_dict.assert_called_once_with(params)

if __name__ == '__main__':
    unittest.main()