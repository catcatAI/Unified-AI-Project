"""上下文系统实用工具"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# Angela Matrix: [L2:MEM] [L4:CTX] Context system utilities

import hashlib
import json
import logging
import zlib

try:
    from cryptography.fernet import Fernet

    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    logging.warning("cryptography module not available, context encryption disabled", exc_info=True)
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def serialize_context(context) -> bytes:
    """
    序列化上下文对象

    Args:
        context: 上下文对象

    Returns:
        bytes: 序列化后的字节数据
    """
    try:
        context_dict = {
            "context_id": context.context_id,
            "context_type": (
                context.context_type.value
                if hasattr(context.context_type, "value")
                else context.context_type
            ),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "status": context.status.value if hasattr(context.status, "value") else context.status,
            "metadata": context.metadata,
            "content": context.content,
            "version": context.version,
            "tags": context.tags,
        }

        json_str = json.dumps(context_dict, ensure_ascii=False)
        return json_str.encode("utf-8")
    except Exception as e:  # broad exception acceptable: data parsing should be resilient
        logger.error(f"Failed to serialize context {context.context_id}: {e}", exc_info=True)
        raise


def deserialize_context(data: bytes) -> Optional["Context"]:
    """
    反序列化上下文对象

    Args:
        data: 序列化后的字节数据

    Returns:
        Context: 反序列化后的上下文对象
    """
    try:
        from .storage.base import Context, ContextStatus, ContextType

        json_str = data.decode("utf-8")
        context_dict = json.loads(json_str)

        context = Context(
            context_id=context_dict["context_id"],
            context_type=ContextType(context_dict["context_type"]),
        )
        context.created_at = datetime.fromisoformat(context_dict["created_at"])
        context.updated_at = datetime.fromisoformat(context_dict["updated_at"])
        context.status = ContextStatus(context_dict["status"])
        context.metadata = context_dict.get("metadata", {})
        context.content = context_dict.get("content", {})
        context.version = context_dict.get("version", "1.0")
        context.tags = context_dict.get("tags", [])

        return context
    except Exception as e:  # broad exception acceptable: data parsing should be resilient
        logger.error(f"Failed to deserialize context: {e}", exc_info=True)
        raise


def compress_context_data(data: bytes) -> bytes:
    """
    压缩上下文数据

    Args:
        data: 要压缩的字节数据

    Returns:
        bytes: 压缩后的字节数据
    """
    try:
        return zlib.compress(data)
    except Exception as e:  # broad exception acceptable: data parsing should be resilient
        logger.error(f"Failed to compress context data: {e}", exc_info=True)
        raise


def decompress_context_data(data: bytes) -> bytes:
    """
    解压缩上下文数据

    Args:
        data: 要解压缩的字节数据

    Returns:
        bytes: 解压缩后的字节数据
    """
    try:
        return zlib.decompress(data)
    except Exception as e:  # broad exception acceptable: data parsing should be resilient
        logger.error(f"Failed to decompress context data: {e}", exc_info=True)
        raise


def encrypt_context_data(data: bytes, key: Optional[bytes] = None) -> bytes:
    """
    加密上下文数据

    Args:
        data: 要加密的字节数据
        key: 加密密钥(可选, 32-byte URL-safe base64-encoded)

    Returns:
        bytes: 加密后的字节数据
    """
    try:
        if key is None:
            logger.warning("No encryption key provided, returning raw data", exc_info=True)
            return data

        if not FERNET_AVAILABLE:
            raise ValueError("Fernet not available")

        fernet = Fernet(key)
        return fernet.encrypt(data)
    except Exception as e:
        logger.error(f"Failed to encrypt context data: {e}", exc_info=True)
        raise


def decrypt_context_data(data: bytes, key: Optional[bytes] = None) -> bytes:
    """
    解密上下文数据

    Args:
        data: 要解密的字节数据
        key: 解密密钥(可选, 32-byte URL-safe base64-encoded)

    Returns:
        bytes: 解密后的字节数据
    """
    try:
        if key is None:
            logger.warning("No decryption key provided, returning raw data", exc_info=True)
            return data

        if not FERNET_AVAILABLE:
            raise ValueError("Fernet not available")

        fernet = Fernet(key)
        return fernet.decrypt(data)
    except Exception as e:
        logger.error(f"Failed to decrypt context data: {e}", exc_info=True)
        raise


def calculate_context_hash(context) -> str:
    """
    计算上下文的哈希值

    Args:
        context: 上下文对象

    Returns:
        str: 上下文的哈希值(SHA256)
    """
    try:
        # 序列化上下文
        serialized_data = serialize_context(context)

        # 计算哈希值
        hash_object = hashlib.sha256(serialized_data)
        return hash_object.hexdigest()
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Failed to calculate context hash: {e}", exc_info=True)
        raise


def validate_context(context) -> bool:
    """
    验证上下文对象的有效性

    Args:
        context: 上下文对象

    Returns:
        bool: 验证是否通过
    """
    try:
        # 检查必需字段
        if not context.context_id:
            logger.error("Context ID is required", exc_info=True)
            return False

        if not context.context_type:
            logger.error("Context type is required", exc_info=True)
            return False

        if context.created_at > datetime.now():
            logger.error("Context created_at cannot be in the future", exc_info=True)
            return False

        if context.updated_at > datetime.now():
            logger.error("Context updated_at cannot be in the future", exc_info=True)
            return False

        if context.created_at > context.updated_at:
            logger.error("Context created_at cannot be later than updated_at", exc_info=True)
            return False

        return True
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Failed to validate context: {e}", exc_info=True)
        return False


def merge_contexts(context1, context2) -> "Context":
    """
    合并两个上下文对象

    Args:
        context1: 第一个上下文对象
        context2: 第二个上下文对象

    Returns:
        Context: 合并后的上下文对象
    """
    try:
        from .storage.base import Context

        merged_context = Context(
            context_id=f"{context1.context_id}+{context2.context_id}",
            context_type=context1.context_type,
        )

        # 合并时间戳(取较新的)
        merged_context.created_at = min(context1.created_at, context2.created_at)
        merged_context.updated_at = max(context1.updated_at, context2.updated_at)

        # 合并元数据
        merged_context.metadata = {**context1.metadata, **context2.metadata}

        # 合并内容
        merged_context.content = {**context1.content, **context2.content}

        # 合并标签
        merged_context.tags = list(set(context1.tags + context2.tags))

        # 合并版本信息
        merged_context.version = f"{context1.version}-{context2.version}"

        return merged_context
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Failed to merge contexts: {e}", exc_info=True)
        raise


def filter_context_content(content: Dict[Any, Any], allowed_keys: List[Any]) -> Dict[Any, Any]:
    """
    过滤上下文内容, 只保留允许的键

    Args:
        content: 原始内容字典
        allowed_keys: 允许的键列表

    Returns:
        Dict[Any, Any]: 过滤后的内容字典
    """
    try:
        filtered_content = {}
        for key in allowed_keys:
            if key in content:
                filtered_content[key] = content[key]
        return filtered_content
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Failed to filter context content: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    from .storage.base import Context, ContextType

    test_context = Context("test-1", ContextType.MEMORY)
    serialized = serialize_context(test_context)
    print(f"Serialized context size: {len(serialized)} bytes")

    deserialized = deserialize_context(serialized)
    if deserialized:
        print(f"Deserialized context ID: {deserialized.context_id}")
    else:
        print("Deserialized context is None")

    context_hash = calculate_context_hash(test_context)
    print(f"Context hash: {context_hash}")

    is_valid = validate_context(test_context)
    print(f"Context is valid: {is_valid}")

    merged = merge_contexts(test_context, deserialized)
    print(f"Merged context ID: {merged.context_id}")
