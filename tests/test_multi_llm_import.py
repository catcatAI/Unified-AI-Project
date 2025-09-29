"""
测试MultiLLMService导入的脚本
"""

def test_import() -> None:
    try:
        _ = print("✓ 成功从apps.backend.src.services.multi_llm_service导入MultiLLMService")
        return True
    except ImportError as e:
        _ = print(f"✗ 无法从apps.backend.src.services.multi_llm_service导入MultiLLMService: {e}")
        return False

if __name__ == "__main__":
    _ = test_import()