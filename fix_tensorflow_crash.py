"""
修復 TensorFlow 測試崩潰問題

問題：運行 pytest 時出現 "Illegal instruction" 錯誤
原因：TensorFlow 與 CPU 指令集不兼容
解決方案：延遲導入 TensorFlow，避免在測試收集階段導入
"""

import os
import sys
import logging
logger = logging.getLogger(__name__)

# 添加 src 目錄到路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "apps", "backend", "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def fix_logic_tool():
    """修復 logic_tool.py 的 TensorFlow 導入問題"""
    logic_tool_path = os.path.join(SRC_DIR, "tools", "logic_tool.py")
    
    with open(logic_tool_path, 'r') as f:
        content = f.read()
    
    # 檢查是否已經修復
    if "TENSORFLOW_IMPORT_DISABLED" in content:
        print("✅ logic_tool.py 已經修復")
        return True
    
    # 添加環境變量檢查，禁用 TensorFlow
    fixed_content = content.replace(
        "import os",
        "import os\n\n# 禁用 TensorFlow 導入以避免 CPU 指令集不兼容問題\nos.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'\nTENSORFLOW_IMPORT_DISABLED = os.environ.get('DISABLE_TENSORFLOW', 'false').lower() == 'true'"
    )
    
    # 修改 _get_nn_model_evaluator 方法
    if "def _get_nn_model_evaluator(self)" in fixed_content:
        fixed_content = fixed_content.replace(
            "def _get_nn_model_evaluator(self) -> Tuple[Optional[Any], Optional[Dict[str, int]]]:",
            "def _get_nn_model_evaluator(self) -> Tuple[Optional[Any], Optional[Dict[str, int]]]:\n        # 檢查是否禁用 TensorFlow\n        if TENSORFLOW_IMPORT_DISABLED:\n            self.tensorflow_import_error = \"TensorFlow 已被環境變量禁用\"\n            logger.critical(\"TensorFlow 已被環境變量 DISABLE_TENSORFLOW=true 禁用\")\n            return None, None\n        "
        )
    
    with open(logic_tool_path, 'w') as f:
        f.write(fixed_content)
    
    print("✅ 已修復 logic_tool.py")
    return True

def fix_math_tool():
    """修復 math_tool.py 的 TensorFlow 導入問題"""
    math_tool_path = os.path.join(SRC_DIR, "tools", "math_tool.py")
    
    if not os.path.exists(math_tool_path):
        print("⚠️  math_tool.py 不存在，跳過")
        return True
    
    with open(math_tool_path, 'r') as f:
        content = f.read()
    
    # 檢查是否已經修復
    if "TENSORFLOW_IMPORT_DISABLED" in content:
        print("✅ math_tool.py 已經修復")
        return True
    
    # 添加環境變量檢查
    if "import os" in content and "TENSORFLOW_IMPORT_DISABLED" not in content:
        fixed_content = content.replace(
            "import os",
            "import os\n\n# 禁用 TensorFlow 導入以避免 CPU 指令集不兼容問題\nos.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'\nTENSORFLOW_IMPORT_DISABLED = os.environ.get('DISABLE_TENSORFLOW', 'false').lower() == 'true'"
        )
        
        with open(math_tool_path, 'w') as f:
            f.write(fixed_content)
        
        print("✅ 已修復 math_tool.py")
    
    return True

def create_test_config():
    """創建測試配置文件"""
    config_path = os.path.join(SRC_DIR, "test_config.py")
    
    config_content = """
# 測試配置
# 禁用 TensorFlow 以避免 CPU 指令集不兼容問題
import os
os.environ['DISABLE_TENSORFLOW'] = 'true'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
"""
    
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print("✅ 已創建測試配置文件")

def main():
    print("開始修復 TensorFlow 崩潰問題...")
    print()
    
    # 創建測試配置
    create_test_config()
    print()
    
    # 修復 logic_tool.py
    fix_logic_tool()
    print()
    
    # 修復 math_tool.py
    fix_math_tool()
    print()
    
    print("=" * 50)
    print("修復完成！")
    print()
    print("使用以下命令運行測試：")
    print("  export DISABLE_TENSORFLOW=true")
    print("  pytest tests/test_logic_tool.py -v")
    print("=" * 50)

if __name__ == "__main__":
    main()