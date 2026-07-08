"""
Transformers库兼容性模块
解决Transformers与Keras 3的兼容性问题
"""

import logging
import os

logger = logging.getLogger(__name__)

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
        logging.warning("Could not import Keras backend (neither tf_keras nor tensorflow.keras)", exc_info=True)


def ensure_transformers_compatibility() -> bool:
    """
    确保Transformers库的兼容性
    """
    try:
        from transformers import __version__ as transformers_version

        logging.info(f"Transformers version: {transformers_version}")

        if not KERAS_AVAILABLE:
            logging.warning(
                "Keras backend not available, some features of Transformers may be limited"
            )

        return True
    except ImportError as e:
        logging.error(f"Transformers library not found: {e}", exc_info=True)
        return False
    except Exception as e:  # broad exception acceptable: network error should not crash operation
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
        logging.error(f"Error ensuring transformers compatibility: {e}", exc_info=True)

        return False


# 兼容性檢查改為被動調用，不在 module 載入時自動執行
# ensure_transformers_compatibility()


def _import_with_timeout(import_fn, timeout=60):
    """Import a module with a timeout to prevent hanging."""
    try:
        from concurrent.futures import ThreadPoolExecutor, TimeoutError

        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(import_fn).result(timeout=timeout)
    except (ImportError, ValueError, TimeoutError) as e:
        raise ImportError(f"Import timed out: {e}")


def safe_import_sentence_transformer() -> tuple:
    """安全导入SentenceTransformer"""
    try:
        os.environ["TF_USE_LEGACY_KERAS"] = "1"
        result = _import_with_timeout(
            lambda: __import__("sentence_transformers", fromlist=["SentenceTransformer"])
        )
        SentenceTransformer = result.SentenceTransformer
        return SentenceTransformer, True
    except (ImportError, ValueError) as e:
        logging.error(f"Could not import SentenceTransformer: {e}", exc_info=True)
        return None, False


def safe_import_pipeline() -> tuple:
    """安全导入Transformers pipeline"""
    try:
        os.environ["TF_USE_LEGACY_KERAS"] = "1"
        result = _import_with_timeout(
            lambda: __import__("transformers", fromlist=["pipeline"])
        )
        pipeline = result.pipeline
        return pipeline, True
    except (ImportError, ValueError) as e:
        logging.error(f"Could not import transformers pipeline: {e}", exc_info=True)
        return None, False
