"""
測試模組 - test_import

自動生成的測試模組,用於驗證系統功能。
"""

import sys
import os
import logging
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")
)

try:
    from ai.agents.specialized.nlp_processing_agent import NLPProcessingAgent

    print("✅ NLPProcessingAgent imported successfully")
except Exception as e:
    print(f"❌ Error importing NLPProcessingAgent: {e}")
    import traceback

    traceback.print_exc()
