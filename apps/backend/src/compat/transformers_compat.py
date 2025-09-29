"""
Transformers库兼容性模块
解决Transformers与Keras 3的兼容性问题
"""

import os
import logging

# 设置环境变量以解决Keras兼容性问题
os.environ['TF_USE_LEGACY_KERAS'] = '1'

# 尝试导入tf-keras
try:
    import tf_keras as keras
    logging.info("Successfully imported tf-keras")
    KERAS_AVAILABLE = True
except ImportError:
    try:
        # 如果tf-keras不可用，尝试使用tensorflow.keras
        import tensorflow.keras as keras
        logging.info("Using tensorflow.keras")
        KERAS_AVAILABLE = True
    except ImportError:
        # 如果都不可用，设置标志以便后续处理
        keras = None
        KERAS_AVAILABLE = False
        logging.warning("Could not import keras backend")

def ensure_transformers_compatibility():
    """
    确保Transformers库的兼容性
    """
    try:
        # 尝试导入Transformers相关模块
        from transformers import __version__ as transformers_version
        logging.info(f"Transformers version: {transformers_version}")
        
        # 检查是否需要特殊处理
        if not KERAS_AVAILABLE:
            logging.warning("Keras backend not available, some features may be limited")
            
        return True
    except Exception as e:
        logging.error(f"Error ensuring transformers compatibility: {e}")
        return False

# 在模块加载时自动执行兼容性检查
ensure_transformers_compatibility

# 为SentenceTransformer提供兼容性处理
def import_sentence_transformers():
    """安全导入SentenceTransformer"""
    try:
        # 先确保环境变量已设置
        os.environ['TF_USE_LEGACY_KERAS'] = '1'
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer, True
    except (ImportError, ValueError) as e:
        logging.error(f"Could not import SentenceTransformer: {e}")
        return None, False

# 为Transformers pipeline提供兼容性处理
def import_transformers_pipeline():
    """安全导入Transformers pipeline"""
    try:
        # 先确保环境变量已设置
        os.environ['TF_USE_LEGACY_KERAS'] = '1'
        from transformers import pipeline
        return pipeline, True
    except (ImportError, ValueError) as e:
        logging.error(f"Could not import transformers pipeline: {e}")
        return None, False