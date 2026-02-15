"""
自然语言生成工具
"""

from typing import Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

# 尝试导入transformers
try:
    os.environ['TF_USE_LEGACY_KERAS'] = '1'

    try:
        from transformers import pipeline
        TRANSFORMERS_AVAILABLE = True
    except ImportError:
        logger.warning("Warning: Could not import transformers pipeline")
        TRANSFORMERS_AVAILABLE = False
except Exception as e:
    logger.error(f"Warning: Error importing transformers: {e}")
    TRANSFORMERS_AVAILABLE = False


class NaturalLanguageGenerationTool:
    """自然语言生成工具"""

    def __init__(self, model_name: str = "gpt2"):
        """初始化"""
        self.model_name = model_name
        self.pipeline = None

        if TRANSFORMERS_AVAILABLE:
            try:
                self.pipeline = pipeline("text-generation", model=model_name)
            except Exception as e:
                logger.error(f"Error loading pipeline: {e}")
                self.pipeline = None

    def generate(self, prompt: str, max_length: int = 100) -> Optional[Dict[str, Any]]:
        """生成文本"""
        if not TRANSFORMERS_AVAILABLE or self.pipeline is None:
            return {"error": "Transformers不可用"}

        try:
            result = self.pipeline(prompt, max_length=max_length, num_return_sequences=1)
            return {
                "status": "success",
                "generated_text": result[0]["generated_text"]
            }
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return {"error": str(e)}
