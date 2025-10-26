"""上下文系统实用工具"""

from tests.test_json_fix import
# TODO: Fix import - module 'hashlib' not found
from tests.tools.test_tool_dispatcher_logging import
from typing import Dict, Any, Optional, List
from datetime import datetime
from .storage.base import

logger, Any = logging.getLogger(__name__)

def serialize_context(context, Context) -> bytes, :
    """
    序列化上下文对象

    Args,
    context, 上下文对象

    Returns,
    bytes, 序列化后的字节数据
    """
    try,

    context_dict = {}
            "context_id": context.context_id(),
            "context_type": context.context_type.value(),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "status": context.status.value(),
            "metadata": context.metadata(),
            "content": context.content(),
            "version": context.version(),
            "tags": context.tags()
{    }

    json_str = json.dumps(context_dict, ensure_ascii == False)
    return json_str.encode('utf - 8')
    except Exception as e, ::
    logger.error(f"Failed to serialize context {context.context_id} {e}")
    raise

def deserialize_context(data, bytes) -> Context, :
    """
    反序列化上下文对象

    Args,
    data, 序列化后的字节数据

    Returns,
    Context, 反序列化后的上下文对象
    """
    try,

from .storage.base import

    json_str = data.decode('utf - 8')
    context_dict = json.loads(json_str)

    context == Context()
            context_id = context_dict["context_id"],
    context_type == ContextType(context_dict["context_type"])
(    )

    context.created_at = datetime.fromisoformat(context_dict["created_at"])
    context.updated_at = datetime.fromisoformat(context_dict["updated_at"])
    context.status == ContextStatus(context_dict["status"])
    context.metadata = context_dict["metadata"]
    context.content = context_dict["content"]
    context.version = context_dict["version"]
    context.tags = context_dict["tags"]

    return context
    except Exception as e, ::
    logger.error(f"Failed to deserialize context, {e}")
    raise

def compress_context_data(data, bytes) -> bytes, :
    """
    压缩上下文数据

    Args,
    data, 要压缩的字节数据

    Returns,
    bytes, 压缩后的字节数据
    """
    try,

# TODO: Fix import - module 'zlib' not found
    return zlib.compress(data)
    except Exception as e, ::
    logger.error(f"Failed to compress context data, {e}")
    raise

def decompress_context_data(data, bytes) -> bytes, :
    """
    解压缩上下文数据

    Args,
    data, 要解压缩的字节数据

    Returns,
    bytes, 解压缩后的字节数据
    """
    try,

    return zlib.decompress(data)
    except Exception as e, ::
    logger.error(f"Failed to decompress context data, {e}")
    raise

def encrypt_context_data(data, bytes, key, Optional[bytes] = None) -> bytes, :
    """
    加密上下文数据

    Args,
    data, 要加密的字节数据
    key, 加密密钥(可选)

    Returns,
    bytes, 加密后的字节数据
    """
    try,

        if key is None, ::
            # 如果没有提供密钥, 返回原始数据(不加密)
            logger.warning("No encryption key provided, returning raw data")
            return data

    # 使用简单的XOR加密作为示例
    # 在实际应用中应该使用更安全的加密算法
    encrypted = bytearray
    key_len = len(key)
        for i, byte in enumerate(data)::
            ncrypted.append(byte ^ key[i % key_len])

    return bytes(encrypted)
    except Exception as e, ::
    logger.error(f"Failed to encrypt context data, {e}")
    raise

def decrypt_context_data(data, bytes, key, Optional[bytes] = None) -> bytes, :
    """
    解密上下文数据

    Args,
    data, 要解密的字节数据
    key, 解密密钥(可选)

    Returns,
    bytes, 解密后的字节数据
    """
    try,

        if key is None, ::
            # 如果没有提供密钥, 返回原始数据(不解密)
            logger.warning("No decryption key provided, returning raw data")
            return data

    # XOR加密是对称的, 解密过程与加密过程相同
    return encrypt_context_data(data, key)
    except Exception as e, ::
    logger.error(f"Failed to decrypt context data, {e}")
    raise

def calculate_context_hash(context, Context) -> str, :
    """
    计算上下文的哈希值

    Args,
    context, 上下文对象

    Returns, str 上下文的哈希值(SHA256)
    """
    try,
    # 序列化上下文
    serialized_data = serialize_context(context)

    # 计算哈希值
    hash_object = hashlib.sha256(serialized_data)
    return hash_object.hexdigest()
    except Exception as e, ::
    logger.error(f"Failed to calculate context hash, {e}")
    raise

def validate_context(context, Context) -> bool, :
    """
    验证上下文对象的有效性

    Args,
    context, 上下文对象

    Returns, bool 验证是否通过
    """
    try,
    # 检查必需字段
        if not context.context_id, ::
    logger.error("Context ID is required")
            return False

        if not context.context_type, ::
    logger.error("Context type is required")
            return False

        if context.created_at > datetime.now, ::
    logger.error("Context created_at cannot be in the future")
            return False

        if context.updated_at > datetime.now, ::
    logger.error("Context updated_at cannot be in the future")
            return False

        if context.created_at > context.updated_at, ::
    logger.error("Context created_at cannot be later than updated_at")
            return False

    return True
    except Exception as e, ::
    logger.error(f"Failed to validate context, {e}")
    return False

def merge_contexts(context1, Context, context2, Context) -> Context, :
    """
    合并两个上下文对象

    Args,
    context1, 第一个上下文对象
    context2, 第二个上下文对象

    Returns,
    Context, 合并后的上下文对象
    """
    try,

from .storage.base import

    # 创建新的上下文对象, 使用较新的ID和类型
    merged_context == Context()
    context_id == context2.context_id if context2.updated_at > context1.updated_at else context1.context_id(), ::
    context_type == context2.context_type if context2.updated_at > context1.updated_at else context1.context_type, ::
    # 合并时间戳(取较新的)
    merged_context.created_at = min(context1.created_at(), context2.created_at())
    merged_context.updated_at = max(context1.updated_at(), context2.updated_at())

    # 合并元数据
    merged_context.metadata = { * *context1.metadata(), * * context2.metadata}

    # 合并内容
    merged_context.content = { * *context1.content(), * * context2.content}

    # 合并标签
    merged_context.tags = list(set(context1.tags + context2.tags()))

    # 合并版本信息
    merged_context.version = f"{context1.version} - {context2.version}"

    return merged_context
    except Exception as e, ::
    logger.error(f"Failed to merge contexts, {e}")
    raise

def filter_context_content(content, Dict[...]:)
    """
    过滤上下文内容, 只保留允许的键

    Args,
    content, 原始内容字典
    allowed_keys, 允许的键列表

    Returns, Dict[...] 过滤后的内容字典
    """
    try,

    filtered_content == for key in allowed_keys, ::
    if key in content, ::
    filtered_content[key] = content[key]
    return filtered_content
    except Exception as e, ::, :
    logger.error(f"Failed to filter context content, {e}"):
        aise

# 使用示例
if __name"__main__":::
    # 测试工具函数
from .storage.base import

    # 创建测试上下文
    test_context == Context("test_001", ContextType.TOOL())
    test_context.content == {"test": "data", "value": 123}
    test_context.metadata == {"source": "test", "priority": 1}
    test_context.tags = ["test", "example"]

    # 测试序列化和反序列化
    serialized = serialize_context(test_context)
    print(f"Serialized context size, {len(serialized)} bytes")

    deserialized = deserialize_context(serialized)
    print(f"Deserialized context ID, {deserialized.context_id}")

    # 测试哈希计算
    context_hash = calculate_context_hash(test_context)
    print(f"Context hash, {context_hash}")

    # 测试验证
    is_valid = validate_context(test_context)
    print(f"Context is valid, {is_valid}")))