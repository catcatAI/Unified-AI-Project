#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言生成工具
用于生成文本内容
"""

import os
import sys
from typing import Optional, Any
import logging
logger = logging.getLogger(__name__)

# 添加src目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 添加兼容性导入
try:
    # 设置环境变量以解决Keras兼容性问题
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    
    # 使用我们的兼容性模块
    try:
        from src.compat.transformers_compat import import_transformers_pipeline
        pipeline, TRANSFORMERS_AVAILABLE = import_transformers_pipeline()
        if not TRANSFORMERS_AVAILABLE:
            print("Warning: Could not import transformers pipeline")
    except ImportError as e:
        print(f"Warning: Could not import transformers_compat: {e}")
        pipeline = None
        TRANSFORMERS_AVAILABLE = False
except Exception as e:
    print(f"Warning: Error during transformers import: {e}")
    pipeline = None
    TRANSFORMERS_AVAILABLE = False


class NaturalLanguageGenerationTool:
    """自然语言生成工具类"""
    
    def __init__(self):
        """初始化工具"""
        self.pipeline = pipeline
        self.available = TRANSFORMERS_AVAILABLE
    
    def generate_text(self, prompt: str, max_length: int = 100, num_return_sequences: int = 1) -> Optional[str]:
        """
        从提示生成文本

        Args:
            prompt: 用于生成文本的提示
            max_length: 生成文本的最大长度
            num_return_sequences: 要生成的序列数量

        Returns:
            生成的文本
        """
        if not self.available or self.pipeline is None:
            print("Warning: Text generation pipeline is not available")
            return None
        
        try:
            generator = self.pipeline("text-generation", max_length=max_length, num_return_sequences=num_return_sequences)
            result = generator(prompt)
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', prompt)
            return result
        except Exception as e:
            print(f"Error during text generation: {e}")
            return None
    
    def save_model(self, model: Any, model_path: str) -> bool:
        """
        将模型保存到文件

        Args:
            model: 要保存的模型
            model_path: 将保存模型的文件路径

        Returns:
            保存是否成功
        """
        try:
            model.save_pretrained(model_path)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_path: str) -> Optional[Any]:
        """
        从文件加载模型

        Args:
            model_path: 保存模型的文件路径

        Returns:
            加载的模型
        """
        if not self.available:
            print("Warning: Transformers is not available")
            return None
        
        try:
            return self.pipeline("text-generation", model=model_path)
        except Exception as e:
            print(f"Error loading model: {e}")
            return None


# 创建全局实例
nl_tool = NaturalLanguageGenerationTool()


def generate_text(prompt: str, max_length: int = 100) -> Optional[str]:
    """
    从提示生成文本（便捷函数）

    Args:
        prompt: 用于生成文本的提示
        max_length: 生成文本的最大长度

    Returns:
        生成的文本
    """
    return nl_tool.generate_text(prompt, max_length=max_length)


def save_model(model: Any, model_path: str) -> bool:
    """
    将模型保存到文件（便捷函数）

    Args:
        model: 要保存的模型
        model_path: 将保存模型的文件路径

    Returns:
        保存是否成功
    """
    return nl_tool.save_model(model, model_path)


def load_model(model_path: str) -> Optional[Any]:
    """
    从文件加载模型（便捷函数）

    Args:
        model_path: 保存模型的文件路径

    Returns:
        加载的模型
    """
    return nl_tool.load_model(model_path)


if __name__ == "__main__":
    # 示例用法
    print("自然语言生成工具 - 示例用法")
    
    if not TRANSFORMERS_AVAILABLE:
        print("Transformers不可用，跳过示例")
    else:
        test_prompt = "Once upon a time"
        result = generate_text(test_prompt, max_length=50)
        print(f"提示: {test_prompt}")
        print(f"结果: {result}")
