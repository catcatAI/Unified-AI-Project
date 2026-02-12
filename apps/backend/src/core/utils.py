#!/usr/bin/env python3
"""
Angela AI - Common Utilities
公共工具模块

提供项目中常用的工具函数和类，减少代码重复。
"""

import os
import sys
import json
import time
import hashlib
import uuid
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
import asyncio


T = TypeVar('T')


# ============================================
# 路径和文件操作
# ============================================

def get_project_root() -> Path:
    """获取项目根目录"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / ".git").exists() or (current / "VERSION").exists():
            return current
        current = current.parent
    return Path.cwd()


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在，不存在则创建"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_read_file(path: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
    """安全读取文件，失败返回 None"""
    try:
        return Path(path).read_text(encoding=encoding)
    except Exception:
        return None


def safe_write_file(path: Union[str, Path], content: str, encoding: str = "utf-8") -> bool:
    """安全写入文件，失败返回 False"""
    try:
        ensure_dir(Path(path).parent)
        Path(path).write_text(content, encoding=encoding)
        return True
    except Exception:
        return False


def load_json(path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """加载 JSON 文件"""
    content = safe_read_file(path)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
    return None


def save_json(path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
    """保存 JSON 文件"""
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return safe_write_file(path, content)
    except Exception:
        return False


def get_file_hash(path: Union[str, Path], algorithm: str = "sha256") -> Optional[str]:
    """获取文件的哈希值"""
    try:
        hasher = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def get_file_size(path: Union[str, Path]) -> int:
    """获取文件大小（字节）"""
    try:
        return Path(path).stat().st_size
    except Exception:
        return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小为可读字符串"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


# ============================================
# 字符串操作
# ============================================

def generate_id(prefix: str = "", length: int = 8) -> str:
    """生成唯一 ID"""
    if prefix:
        return f"{prefix}_{uuid.uuid4().hex[:length]}"
    return uuid.uuid4().hex[:length]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def slugify(text: str) -> str:
    """将文本转换为 URL 友好的 slug"""
    import re
    # 转换为小写
    text = text.lower()
    # 替换空格和特殊字符为连字符
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    import re
    # 移除路径遍历字符
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    # 只保留字母、数字、下划线、连字符和点
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    return filename


def format_timestamp(timestamp: Optional[Union[str, float, datetime]] = None) -> str:
    """格式化时间戳为字符串"""
    if timestamp is None:
        timestamp = datetime.now()
    elif isinstance(timestamp, (str, float)):
        timestamp = datetime.fromtimestamp(float(timestamp))
    return timestamp.isoformat()


def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """解析时间戳字符串"""
    try:
        return datetime.fromisoformat(timestamp)
    except Exception:
        return None


# ============================================
# 验证操作
# ============================================

def is_valid_email(email: str) -> bool:
    """验证邮箱地址格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_url(url: str) -> bool:
    """验证 URL 格式"""
    import re
    pattern = r'^https?://[^\s/$.?#][^\s]*$'
    return re.match(pattern, url) is not None


def is_valid_uuid(uuid_str: str) -> bool:
    """验证 UUID 格式"""
    try:
        uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False


# ============================================
# 装饰器
# ============================================

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """异步重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator


def measure_time(func: Callable) -> Callable:
    """测量函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logging.debug(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return result
    return wrapper


def async_measure_time(func: Callable) -> Callable:
    """测量异步函数执行时间"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start_time
        logging.debug(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return result
    return wrapper


def cache_result(ttl: float = 60.0) -> Callable:
    """缓存结果装饰器"""
    cache: Dict[str, tuple] = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator


# ============================================
# 上下文管理器
# ============================================

@contextmanager
def timer(description: str = "Operation"):
    """计时上下文管理器"""
    start = time.time()
    yield
    elapsed = time.time() - start
    logging.info(f"{description} took {elapsed:.4f} seconds")


@contextmanager
def suppress_errors(*exceptions):
    """抑制异常的上下文管理器"""
    try:
        yield
    except exceptions:
        pass


@contextmanager
def change_dir(path: Union[str, Path]):
    """临时切换工作目录"""
    old_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_dir)


# ============================================
# 数据转换
# ============================================

def deep_merge_dict(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并字典"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(d: Dict, parent_key: str = "", sep: str = ".") -> Dict:
    """展平嵌套字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """安全类型转换"""
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值限制在指定范围内"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值"""
    return a + (b - a) * t


# ============================================
# 日志工具
# ============================================

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 格式化
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_string)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        ensure_dir(Path(log_file).parent)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ============================================
# 异步工具
# ============================================

async def run_sync(func: Callable, *args, **kwargs) -> Any:
    """在异步上下文中运行同步函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)


async def gather_with_errors(*coroutines) -> List[Any]:
    """收集所有协程结果，即使某些失败"""
    results = []
    for coro in asyncio.as_completed(coroutines):
        try:
            result = await coro
            results.append(result)
        except Exception as e:
            results.append(e)
    return results


async def timeout_after(coro: asyncio.coroutine, timeout: float) -> Any:
    """设置协程超时"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout} seconds")


# ============================================
# 类和对象工具
# ============================================

class Singleton(type):
    """单例元类"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class LazyProperty:
    """懒加载属性描述器"""
    
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
    
    def __get__(self, obj: Any, type: type = None) -> Any:
        if obj is None:
            return self
        if self.name not in obj.__dict__:
            obj.__dict__[self.name] = self.func(obj)
        return obj.__dict__[self.name]


class cached_property:
    """缓存属性描述器（兼容 Python 3.7）"""
    
    def __init__(self, func: Callable):
        self.func = func
        self.attr_name = None
    
    def __set_name__(self, owner, name):
        self.attr_name = name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.attr_name is None:
            raise TypeError("Cannot use cached_property instance without calling __set_name__")
        try:
            cache = instance.__dict__
        except AttributeError:
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.attr_name!r} property."
            )
            raise TypeError(msg) from None
        val = cache.get(self.attr_name, None)
        if val is None:
            val = self.func(instance)
            try:
                cache[self.attr_name] = val
            except TypeError:
                msg = (
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                    f"does not support item assignment for caching {self.attr_name!r} property."
                )
                raise TypeError(msg) from None
        return val


# ============================================
# 环境工具
# ============================================

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量"""
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔环境变量"""
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    return default


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数环境变量"""
    return safe_cast(os.environ.get(key), int, default)


def get_env_float(key: str, default: float = 0.0) -> float:
    """获取浮点环境变量"""
    return safe_cast(os.environ.get(key), float, default)


def get_env_list(key: str, separator: str = ",", default: Optional[List[str]] = None) -> List[str]:
    """获取列表环境变量"""
    value = os.environ.get(key)
    if value:
        return [item.strip() for item in value.split(separator)]
    return default or []


# ============================================
# 模块导出
# ============================================

__all__ = [
    # 路径和文件操作
    "get_project_root",
    "ensure_dir",
    "safe_read_file",
    "safe_write_file",
    "load_json",
    "save_json",
    "get_file_hash",
    "get_file_size",
    "format_file_size",
    
    # 字符串操作
    "generate_id",
    "truncate_text",
    "slugify",
    "sanitize_filename",
    "format_timestamp",
    "parse_timestamp",
    
    # 验证操作
    "is_valid_email",
    "is_valid_url",
    "is_valid_uuid",
    
    # 装饰器
    "retry",
    "async_retry",
    "measure_time",
    "async_measure_time",
    "cache_result",
    
    # 上下文管理器
    "timer",
    "suppress_errors",
    "change_dir",
    
    # 数据转换
    "deep_merge_dict",
    "flatten_dict",
    "safe_cast",
    "clamp",
    "lerp",
    
    # 日志工具
    "setup_logger",
    
    # 异步工具
    "run_sync",
    "gather_with_errors",
    "timeout_after",
    
    # 类和对象工具
    "Singleton",
    "LazyProperty",
    "cached_property",
    
    # 环境工具
    "get_env",
    "get_env_bool",
    "get_env_int",
    "get_env_float",
    "get_env_list",
]


if __name__ == "__main__":
    # 测试工具函数
    print(f"Project root: {get_project_root()}")
    print(f"Generated ID: {generate_id('test')}")
    print(f"Truncated text: {truncate_text('This is a very long text that should be truncated', 20)}")
    print(f"Slugified: {slugify('Hello World! This is a Test')}")
    print(f"Formatted time: {format_timestamp()}")
    print(f"Clamped value: {clamp(5, 0, 10)}")
    print(f"Interpolated: {lerp(0, 10, 0.5)}")
