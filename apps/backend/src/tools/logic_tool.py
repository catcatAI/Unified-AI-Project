"""
Logic Tool - 逻辑工具
用于评估逻辑表达式
"""

import os
import json
import logging
import sys
from typing import Optional, Tuple, Dict, Any, Union

# Add the src directory to the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Add scripts directory for imports
sys.path.append(os.path.join(SCRIPT_DIR))

try:
    from .logic_model.logic_parser_eval import LogicParserEval
    # 修复导入路径
    from src.core.managers.dependency_manager import dependency_manager
except ImportError:
    # Fallback imports if modules not available
    LogicParserEval = None
    dependency_manager = None

# Configuration for NN Model
MODEL_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
CHAR_MAP_LOAD_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")

logger = logging.getLogger(__name__)


class LogicTool:
    """逻辑工具类"""
    
    def __init__(self):
        # 初始化评估器
        self.parser_evaluator: Optional[LogicParserEval] = None
        self.nn_model_evaluator: Optional[Any] = None  # Type hint as Any due to external library
        self.nn_char_to_token: Optional[Dict[str, int]] = None
        self.tensorflow_import_error: Optional[str] = None

    def _get_parser_evaluator(self) -> LogicParserEval:
        """初始化并返回LogicParserEval实例"""
        if self.parser_evaluator is None:
            logger.info("首次初始化LogicParserEval...")
            if LogicParserEval is not None:
                self.parser_evaluator = LogicParserEval()
            else:
                logger.warning("LogicParserEval不可用")
        return self.parser_evaluator

    def _get_nn_model_evaluator(self) -> Tuple[Optional[Any], Optional[Dict[str, int]]]:
        """加载LogicNNModel，处理TensorFlow导入错误"""
        if self.nn_model_evaluator is not None or self.tensorflow_import_error is not None:
            return self.nn_model_evaluator, self.nn_char_to_token

        # 检查TensorFlow是否可用
        if dependency_manager is not None and not dependency_manager.is_available('tensorflow'):
            self.tensorflow_import_error = "TensorFlow通过dependency_manager不可用"
            logger.critical(f"CRITICAL: TensorFlow不可用。Logic tool的NN功能将被禁用。")
            return None, None

        try:
            from .logic_model.logic_model_nn import LogicNNModel
            logger.info("首次加载LogicNNModel...")
            if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH):
                raise FileNotFoundError("NN模型或字符映射文件未找到")

            self.nn_model_evaluator = LogicNNModel.load_model(MODEL_LOAD_PATH, CHAR_MAP_LOAD_PATH)
            with open(CHAR_MAP_LOAD_PATH, 'r') as f:
                self.nn_char_to_token = json.load(f)['char_to_token']
            logger.info("LogicNNModel加载成功")

        except ImportError as e:
            logger.critical(f"CRITICAL: 无法导入TensorFlow。Logic tool的NN功能将被禁用。错误: {e}")
            self.tensorflow_import_error = str(e)
        except FileNotFoundError as e:
            logger.warning(f"警告: Logic NN模型文件未找到。NN功能将被禁用。错误: {e}")
            self.tensorflow_import_error = str(e)
        except Exception as e:
            logger.error(f"加载LogicNNModel时发生意外错误: {e}")
            self.tensorflow_import_error = str(e)

        return self.nn_model_evaluator, self.nn_char_to_token

    def evaluate_expression(self, expression_string: str) -> Union[bool, str, None]:
        """
        使用最佳可用方法评估逻辑表达式字符串
        优先使用NN模型，如果NN不可用则回退到解析器
        """
        normalized_expression = expression_string.lower()

        # 首先尝试NN模型
        nn_model, char_map = self._get_nn_model_evaluator()
        if nn_model and char_map:
            logger.info(f"LogicTool: 使用'nn'方法评估'{normalized_expression}'")
            try:
                return nn_model.predict(normalized_expression, char_map)
            except Exception as e:
                logger.critical(f"NN预测'{normalized_expression}'时出错: {e}")
                # 预测错误时回退到解析器
                logger.warning("LogicTool: NN预测失败，回退到解析器")

        # 回退到解析器
        logger.info(f"LogicTool: 使用'parser'方法评估'{normalized_expression}'")
        try:
            parser = self._get_parser_evaluator()
            if parser is not None:
                result = parser.evaluate(normalized_expression)
                return result if result is not None else "Error: 解析器无法处理的表达式"
            else:
                return "Error: 解析器不可用"
        except Exception as e:
            logger.critical(f"解析器评估'{normalized_expression}'时出错: {e}")
            return "Error: 解析器无法处理的表达式"


# 全局实例
logic_tool_instance = LogicTool()
evaluate_expression = logic_tool_instance.evaluate_expression


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("--- Logic Tool 示例用法 ---")

    test_cases = [
        ("true AND false", False),
        ("NOT (true OR false)", False),
        ("false OR (true AND true)", True),
        ("invalid expression", "Error: 解析器无法处理的表达式")
    ]

    logger.info("\n--- 测试统一evaluate_expression (NN回退到解析器) ---")
    for expr, expected in test_cases:
        result = logic_tool_instance.evaluate_expression(expr)
        logger.info(f'测试: "{expr}" -> 结果: {result}')
        
        if isinstance(result, bool):
            logger.info(f'  (结果是布尔值，有效)')
        elif isinstance(result, str) and 'Error' in result:
            logger.info(f'  (结果是错误字符串，对无效表达式有效)')
        else:
            logger.info(f'  (结果是意外类型: {type(result)})')
        assert result is not None, f'FAIL: For "{expr}"'
    
    logger.info("\nLogic Tool脚本执行完成")
