"""
参数提取器 - 从外部模型提取、映射和加载参数
"""

import os
from typing import Dict, Any, Optional

# 尝试导入huggingface_hub
try:
    from huggingface_hub import hf_hub_download
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False


class ParameterExtractor:
    """参数提取器"""

    def __init__(self, repo_id: str) -> None:
        """
        初始化参数提取器

        Args:
            repo_id: Hugging Face Hub仓库ID
        """
        self.repo_id = repo_id

    def download_model_parameters(self, filename: str, cache_dir: str = "model_cache") -> Optional[str]:
        """
        从Hugging Face Hub下载模型参数

        Args:
            filename: 参数文件名
            cache_dir: 缓存目录

        Returns:
            下载文件路径
        """
        if not HF_HUB_AVAILABLE:
            print("huggingface_hub不可用")
            return None

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        try:
            return hf_hub_download(
                repo_id=self.repo_id,
                filename=filename,
                cache_dir=cache_dir
            )
        except Exception as e:
            print(f"下载失败: {e}")
            return None

    def map_parameters(self, source_params: Dict[str, Any], mapping_rules: Dict[str, str]) -> Dict[str, Any]:
        """
        将源模型参数映射到目标模型

        Args:
            source_params: 源模型参数
            mapping_rules: 映射规则

        Returns:
            映射后的参数
        """
        mapped_params = {}

        for source_key, target_key in mapping_rules.items():
            if source_key in source_params:
                mapped_params[target_key] = source_params[source_key]

        return mapped_params

    def load_parameters_to_model(self, model: Any, params: Dict[str, Any]):
        """
        将参数加载到模型中

        Args:
            model: 目标模型
            params: 参数字典
        """
        if hasattr(model, "load_state_dict"):
            model.load_state_dict(params)
        else:
            for key, value in params.items():
                if hasattr(model, key):
                    setattr(model, key, value)