"""
Transformers库兼容性模块
解决Transformers与Keras 3的兼容性问题
"""

import os
import logging

# 设置环境变量以解决Keras兼容性问题
os.environ['TF_USE_LEGACY_KERAS'] = '1'

KERAS_AVAILABLE = False

# 尝试导入Keras
try:
    import tf_keras as keras
    logging.info("Successfully imported tf_keras")
    KERAS_AVAILABLE = True
except ImportError:
    try:
        from tensorflow import keras
        logging.info("Using tensorflow.keras")
        KERAS_AVAILABLE = True
    except ImportError:
        keras = None
        KERAS_AVAILABLE = False
        logging.warning("Could not import Keras backend (neither tf_keras nor tensorflow.keras)")

def ensure_transformers_compatibility():
    """
    确保Transformers库的兼容性
    """
    try:
        from transformers import __version__ as transformers_version
        logging.info(f"Transformers version: {transformers_version}")
        
        if not KERAS_AVAILABLE:
            logging.warning("Keras backend not available, some features of Transformers may be limited")
            
        return True
    except ImportError as e:
        logging.error(f"Transformers library not found: {e}")
        return False
    except Exception as e:
        logging.error(f"Error ensuring transformers compatibility: {e}")
        return False

# 在模块加载时自动执行兼容性检查
ensure_transformers_compatibility()

def safe_import_sentence_transformer():
    """安全导入SentenceTransformer"""
    try:
        # 确保环境变量已设置
        os.environ['TF_USE_LEGACY_KERAS'] = '1'
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer, True
    except (ImportError, ValueError) as e:
        logging.error(f"Could not import SentenceTransformer: {e}")
        return None, False

def safe_import_pipeline():
    """安全导入Transformers pipeline"""
    try:
        # 确保环境变量已设置
        os.environ['TF_USE_LEGACY_KERAS'] = '1'
        from transformers import pipeline
        return pipeline, True
    except (ImportError, ValueError) as e:
        logging.error(f"Could not import transformers pipeline: {e}")
        return None, False
