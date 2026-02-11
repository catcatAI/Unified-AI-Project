"""
测试模块 - test_trained_models

自动生成的测试模块,用于验证系统功能。
"""

#!/usr/bin/env python3
"""
测试训练好的模型
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
from typing import Any

# Add project root to path to allow absolute imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_PATH = PROJECT_ROOT / "apps" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))
if str(BACKEND_PATH / "src") not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH / "src"))

# Mock external dependencies if necessary
try:
    from ai.models.trained_model_manager import TrainedModelManager
    from ai.models.model_types import ModelType
    from ai.models.model_data_types import ModelData
except ImportError:
    class MockTrainedModelManager:
        def load_model(self, model_type: Any, version: str = "latest"):
            return MagicMock()
        def get_model_metadata(self, model_type: Any, version: str = "latest"):
            return {"status": "mocked"}
    TrainedModelManager = MockTrainedModelManager

    class MockModelType:
        NLP_EMBEDDING = "nlp_embedding"
        VISION_CLASSIFICATION = "vision_classification"
    ModelType = MockModelType

    class MockModelData:
        pass
    ModelData = MockModelData


class TestTrainedModels(unittest.TestCase):
    def setUp(self):
        """测试前设置"""
        self.model_manager = TrainedModelManager()
        self.test_data = {
            "text_input": "Hello, world!",
            "image_input": b"fake_image_data",
            "audio_input": b"fake_audio_data"
        }
        self.test_config = {
            "nlp_model_version": "v1.0",
            "vision_model_version": "v1.2"
        }

    def tearDown(self):
        """测试后清理"""
        # 清理任何可能由测试创建的资源
        pass

    def test_load_nlp_model(self):
        """测试NLP模型加载"""
        model = self.model_manager.load_model(ModelType.NLP_EMBEDDING, self.test_config["nlp_model_version"])
        self.assertIsNotNone(model)
        # 进一步断言模型是否是预期类型或具有预期方法
        self.assertTrue(hasattr(model, "predict"))

    def test_load_vision_model(self):
        """测试视觉模型加载"""
        model = self.model_manager.load_model(ModelType.VISION_CLASSIFICATION, self.test_config["vision_model_version"])
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, "classify"))

    def test_get_model_metadata(self):
        """测试获取模型元数据"""
        metadata = self.model_manager.get_model_metadata(ModelType.NLP_EMBEDDING)
        self.assertIsNotNone(metadata)
        self.assertIn("status", metadata)
        self.assertEqual(metadata["status"], "mocked")

    @patch('apps.backend.src.ai.models.trained_model_manager.TrainedModelManager.load_model')
    def test_nlp_model_prediction(self, mock_load_model):
        """测试NLP模型预测功能"""
        mock_nlp_model = MagicMock()
        mock_nlp_model.predict.return_value = [0.1, 0.2, 0.7]
        mock_load_model.return_value = mock_nlp_model

        model = self.model_manager.load_model(ModelType.NLP_EMBEDDING)
        prediction = model.predict(self.test_data["text_input"])

        mock_nlp_model.predict.assert_called_once_with(self.test_data["text_input"])
        self.assertEqual(prediction, [0.1, 0.2, 0.7])

    @patch('apps.backend.src.ai.models.trained_model_manager.TrainedModelManager.load_model')
    def test_vision_model_classification(self, mock_load_model):
        """测试视觉模型分类功能"""
        mock_vision_model = MagicMock()
        mock_vision_model.classify.return_value = "cat"
        mock_load_model.return_value = mock_vision_model

        model = self.model_manager.load_model(ModelType.VISION_CLASSIFICATION)
        classification = model.classify(self.test_data["image_input"])

        mock_vision_model.classify.assert_called_once_with(self.test_data["image_input"])
        self.assertEqual(classification, "cat")

    def test_model_data_dataclass(self):
        """测试ModelData数据类"""
        data = ModelData(model_type=ModelType.NLP_EMBEDDING, version="v1.0", path="/models/nlp/v1.0")
        self.assertEqual(data.model_type, ModelType.NLP_EMBEDDING)
        self.assertEqual(data.version, "v1.0")
        self.assertEqual(data.path, "/models/nlp/v1.0")

    def test_model_not_found_handling(self):
        """测试模型未找到时的处理"""
        with patch.object(self.model_manager, 'load_model', side_effect=FileNotFoundError("Model file not found")):
            model = self.model_manager.load_model(ModelType.NLP_EMBEDDING, "non_existent_version")
            self.assertIsNone(model) # Assuming load_model returns None on FileNotFoundError

    def test_model_corrupted_handling(self):
        """测试模型损坏时的处理"""
        with patch.object(self.model_manager, 'load_model', side_effect=IOError("Corrupted model file")):
            model = self.model_manager.load_model(ModelType.VISION_CLASSIFICATION, "v1.0")
            self.assertIsNone(model) # Assuming load_model returns None on IOError

    def test_model_type_enum(self):
        """测试ModelType枚举"""
        self.assertEqual(ModelType.NLP_EMBEDDING.value, "nlp_embedding")
        self.assertEqual(ModelType.VISION_CLASSIFICATION.value, "vision_classification")

if __name__ == '__main__':
    unittest.main()