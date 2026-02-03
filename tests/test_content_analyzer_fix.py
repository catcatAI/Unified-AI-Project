import unittest
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

from ai.learning.content_analyzer_module import ContentAnalyzerModule

class TestContentAnalyzerFix(unittest.TestCase):
    """
    测试模块 - test_content_analyzer_fix

    自动生成的测试模块,用于验证系统功能。
    """

    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
        self.analyzer = ContentAnalyzerModule()

    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()

    def test_content_analyzer_module_functionality(self):
        """测试ContentAnalyzerModule的功能"""
        print("Testing ContentAnalyzerModule...")

        try:
            # Test basic entity extraction
            text = "Apple Inc. is a company. Steve Jobs was a person."
            print(f"Analyzing text: {text}")

            kg_data, nx_graph = self.analyzer.analyze_content(text)

            print(f"Entities found: {len(kg_data['entities'])}")
            for entity_id, entity in kg_data['entities'].items():
                print(f"  - {entity['label']} ({entity['type']})")

            # Check if Apple Inc. is found
            apple_inc_found = any(entity['label'] == 'Apple Inc.' for entity in kg_data['entities'].values())
            if apple_inc_found:
                print("✓ Apple Inc. entity found")
            else:
                print("✗ Apple Inc. entity not found")
            
            # Check if Steve Jobs is found
            steve_jobs_found = any(entity['label'] == 'Steve Jobs' for entity in kg_data['entities'].values())
            if steve_jobs_found:
                print("✓ Steve Jobs entity found")
            else:
                print("✗ Steve Jobs entity not found")
            
            self.assertTrue(apple_inc_found and steve_jobs_found, "Both Apple Inc. and Steve Jobs entities should be found.")
            print("✓ ContentAnalyzerModule functionality test passed.")

        except Exception as e:
            print(f"✗ Error testing ContentAnalyzerModule: {e}")
            import traceback
            traceback.print_exc()
            self.fail(f"Test failed due to exception: {e}")

if __name__ == "__main__":
    unittest.main()
