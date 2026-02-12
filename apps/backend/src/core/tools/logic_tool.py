# =============================================================================
# ANGELA-MATRIX: L6[执行层] β [A] L2+
# =============================================================================
#
# 职责: 逻辑工具，提供逻辑推理和计算功能
# 维度: 主要涉及 β (认知) 维度
# 安全: 使用 Key A (后端控制)
# 成熟度: L2+ 等级
#
# =============================================================================

import os
import sys
import logging
from typing import Dict, Any, List, Optional

# 添加 src 到路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 導入安全求值器
try:
    from src.core.security.secure_eval import safe_eval, EvalResult
    SECURE_EVAL_AVAILABLE = True
except ImportError:
    SECURE_EVAL_AVAILABLE = False
    logger.warning("安全求值器不可用，將使用備用方案")

logger = logging.getLogger("logic_tool")

# Add the src directory to the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

class LogicTool:
    """逻辑工具"""

    def __init__(self):
        self.parser_evaluator = None
        self.nn_model_evaluator = None
        self.nn_char_to_token = None
        self.tensorflow_import_error = None

    def evaluate_logic(self, logic_statement: str) -> Dict[str, Any]:
        """
        評估邏輯語句

        使用安全求值器來防止代碼注入攻擊。

        Args:
            logic_statement: 邏輯語句字符串

        Returns:
            Dict[str, Any]: 評估結果
        """
        try:
            if SECURE_EVAL_AVAILABLE:
                # 使用安全求值器
                eval_result = safe_eval(logic_statement)

                if eval_result.success:
                    return {
                        'success': True,
                        'result': eval_result.result,
                        'statement': logic_statement
                    }
                else:
                    return {
                        'success': False,
                        'error': eval_result.error,
                        'statement': logic_statement
                    }
            else:
                # 備用方案：使用受限的 eval（僅允許布爾和數字）
                # 注意：這不是完全安全的，僅作為臨時備用
                allowed_names = {
                    'True': True,
                    'False': False,
                    'None': None,
                }
                result = eval(logic_statement, {"__builtins__": None}, allowed_names)
                return {
                    'success': True,
                    'result': result,
                    'statement': logic_statement
                }
        except Exception as e:
            logger.error(f"邏輯評估錯誤: {e}, 語句: {logic_statement}")
            return {
                'success': False,
                'error': str(e),
                'statement': logic_statement
            }

    def validate_logic(self, logic_statement: str) -> Dict[str, Any]:
        """验证逻辑语句"""
        # 简化实现
        return {
            'valid': True,
            'statement': logic_statement
        }

    def parse_logic(self, logic_statement: str) -> Dict[str, Any]:
        """解析逻辑语句"""
        # 简化实现
        return {
            'parsed': True,
            'components': [],
            'statement': logic_statement
        }

# 全局实例
_logic_tool: Optional[LogicTool] = None

def get_logic_tool() -> LogicTool:
    """获取全局逻辑工具实例"""
    global _logic_tool
    if _logic_tool is None:
        _logic_tool = LogicTool()
    return _logic_tool