"""
测试模块 - test_vision_service

自动生成的测试模块，用于验证系统功能。
"""

import unittest
import pytest

from apps.backend.src.services.vision_service import VisionService

class TestVisionService(unittest.TestCase):

    @pytest.mark.timeout(15)
    
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_01_initialization(self) -> None:
        """Test Vision service initialization."""
        service = VisionService()
        self.assertIsNotNone(service)
        # Check that service has required attributes
        self.assertTrue(hasattr(service, 'config'))
        print("TestVisionService.test_01_initialization PASSED")

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_02_analyze_image(self) -> None:
        """Test image analysis."""
        service = VisionService()
        dummy_image = b"dummy_image_bytes"
        features = ["captioning", "object_detection", "ocr"]
        # Fix: properly await the coroutine
        analysis = await service.analyze_image(dummy_image, features=features)

        self.assertIn("caption", analysis)
        self.assertIn("A mock image of a captioning, object_detection, ocr.", analysis["caption"])

        self.assertIn("objects", analysis)
        self.assertIsInstance(analysis["objects"], list)

        self.assertIn("ocr_text", analysis)
        self.assertIn("Mock OCR text for image with length", analysis["ocr_text"])

        analysis_none = await service.analyze_image(None) # Test with None input
        self.assertIn("error", analysis_none)
        print("TestVisionService.test_02_analyze_image PASSED")

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_03_compare_images(self) -> None:
        """Test image comparison."""
        service = VisionService()
        dummy_image1 = b"dummy1"
        dummy_image2 = b"dummy2"

        results = set()
        for _ in range(10):
            # Fix: properly await the coroutine
            similarity = await service.compare_images(dummy_image1, dummy_image2)
            self.assertIsInstance(similarity, dict)  # compare_images now returns a dict
            self.assertIn("similarity_score", similarity)
            score = similarity["similarity_score"]
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            results.add(score)

        self.assertGreater(len(results), 1, "Expected multiple different similarity scores.")

        similarity_none1 = await service.compare_images(None, dummy_image2)
        self.assertIn("error", similarity_none1)
        similarity_none2 = await service.compare_images(dummy_image1, None)
        self.assertIn("error", similarity_none2)
        print("TestVisionService.test_03_compare_images PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)