# Angela AI - Docstring 风格指南

本文档定义了 Angela AI 项目的代码注释规范，确保代码文档的一致性和可读性。

## 概述

Angela AI 使用 **Google 风格**的 docstring，这是 Python 社区广泛接受的文档字符串格式。

## 基本格式

### 单行 Docstring

```python
def function_name():
    """单行摘要描述。"""
    pass
```

### 多行 Docstring

```python
def function_name():
    """摘要描述。

    更详细的描述可以在这里添加。

    Args:
        param1: 第一个参数的描述。

    Returns:
        返回值的描述。
    """
    pass
```

## 模块 Docstring

```python
"""
Angela AI - Module Name
模块简短描述。

详细描述模块的功能和用途。

Classes:
    ClassName: 类的描述。

Functions:
    function_name: 函数的描述。

Example:
    >>> module.function_name()
    'result'
"""

import ...
```

## 类 Docstring

```python
class ClassName:
    """类的简短描述。

    详细描述类的功能、用途和行为。

    Attributes:
        attribute1: 属性的描述。
        attribute2: 另一个属性的描述。

    Methods:
        method1: 方法1的描述。
        method2: 方法2的描述。

    Example:
        >>> obj = ClassName()
        >>> obj.method1()
        'result'
    """

    def __init__(self, param1: str):
        """初始化 ClassName 实例。

        Args:
            param1: 第一个参数的描述。

        Raises:
            ValueError: 如果参数无效。
        """
        self.attribute1 = param1
```

## 函数 Docstring

### 标准函数

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """函数的简短描述。

    详细描述函数的功能和行为。

    Args:
        param1: 第一个参数的描述。
        param2: 第二个参数的描述，默认值为 0。

    Returns:
        bool: 返回值的描述。

    Raises:
        ValueError: 如果参数无效。
        RuntimeError: 如果运行时出错。

    Example:
        >>> function_name("test", 5)
        True
    """
    return True
```

### 异步函数

```python
async def async_function(param1: str) -> Dict[str, Any]:
    """异步函数的简短描述。

    详细描述异步函数的功能和行为。

    Args:
        param1: 参数的描述。

    Returns:
        Dict[str, Any]: 返回字典的描述。

    Example:
        >>> await async_function("test")
        {"key": "value"}
    """
    return {"key": "value"}
```

## 参数类型

使用 Python 类型注解（type hints）来指定参数和返回值的类型。

```python
from typing import Dict, List, Optional, Union, Any

def complex_function(
    items: List[str],
    mapping: Optional[Dict[str, int]] = None,
    flag: bool = True
) -> Dict[str, Union[str, int]]:
    """使用类型注解的函数。

    Args:
        items: 字符串列表。
        mapping: 可选的字符串到整数的映射。
        flag: 布尔标志。

    Returns:
        包含字符串和整数的字典。
    """
    return {"items": len(items), "flag": flag}
```

## 常用节

### Args

```python
Args:
    param1: 参数描述。
    param2: 可选参数，默认为默认值。
    param3: 可选参数，如果没有提供则为 None。
```

### Returns

```python
Returns:
    str: 返回字符串描述。
    int: 返回整数描述。
    Optional[str]: 返回可选字符串。
```

### Raises

```python
Raises:
    ValueError: 如果参数值无效。
    TypeError: 如果参数类型错误。
    RuntimeError: 如果运行时出错。
    ConnectionError: 如果连接失败。
```

### Attributes

```python
Attributes:
    name: 对象的名称。
    value: 存储的值。
```

### Examples

```python
Example:
    >>> obj = ClassName("test")
    >>> obj.method()
    'result'

    更复杂的示例:

    >>> items = ["a", "b", "c"]
    >>> function_name(items)
    {'count': 3, 'items': ['a', 'b', 'c']}
```

### Notes

```python
Notes:
    这是关于函数或类的额外信息。

    可以跨越多行。

    用于解释复杂的行为或使用场景。
```

### Todo

```python
Todo:
    * 实现功能 X
    * 添加支持 Y
    * 优化性能 Z
```

## 常见场景

### 类方法

```python
class MyClass:
    def method(self, param: str) -> None:
        """类方法的描述。

        Args:
            param: 参数描述。

        Note:
            self 是实例对象，不需要在 Args 中列出。
        """
        pass

    @classmethod
    def class_method(cls, param: int) -> bool:
        """类方法的描述。

        Args:
            param: 参数描述。

        Returns:
            返回值描述。
        """
        return True

    @staticmethod
    def static_method(param: float) -> str:
        """静态方法的描述。

        Args:
            param: 参数描述。

        Returns:
            返回值描述。
        """
        return str(param)
```

### 属性

```python
class MyClass:
    @property
    def name(self) -> str:
        """str: 名称属性的描述。"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """设置名称属性。

        Args:
            value: 新的名称值。

        Raises:
            ValueError: 如果名称为空。
        """
        if not value:
            raise ValueError("Name cannot be empty")
        self._name = value
```

### 异常类

```python
class CustomError(Exception):
    """自定义异常的描述。

    Attributes:
        message: 错误消息。
        code: 错误代码。
    """

    def __init__(self, message: str, code: int = 0):
        """初始化 CustomError。

        Args:
            message: 错误消息。
            code: 错误代码，默认为 0。
        """
        super().__init__(message)
        self.code = code
```

### 上下文管理器

```python
class ContextManager:
    """上下文管理器的描述。"""

    def __enter__(self):
        """进入上下文。

        Returns:
            上下文管理器实例。
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文。

        Args:
            exc_type: 异常类型。
            exc_val: 异常值。
            exc_tb: 异常跟踪。

        Returns:
            bool: 如果处理了异常则为 True，否则为 False。
        """
        return False
```

## 格式规则

1. **缩进**: Docstring 的内容应该与函数体对齐。
2. **换行**: 使用空行分隔不同的节。
3. **类型注解**: 优先使用类型注解而不是在描述中重复类型。
4. **引用代码**: 使用 `>>>` 前缀表示代码示例。
5. **特殊字符**: 使用反斜杠转义特殊字符。

## 最佳实践

1. **简洁准确**: 摘要应该简洁但准确。
2. **完整描述**: 描述函数的功能、参数、返回值和可能的异常。
3. **提供示例**: 对于复杂的函数，提供使用示例。
4. **保持更新**: 代码变更时同步更新 docstring。
5. **避免重复**: 如果类型注解已经清楚，不要在描述中重复。

## 工具

使用以下工具检查和格式化 docstring:

```bash
# 安装 pydocstyle
pip install pydocstyle

# 检查 docstring
pydocstyle apps/backend/src/

# 格式化 docstring (使用 docformatter)
pip install docformatter
docformatter --in-place --recursive apps/backend/src/
```

## 示例

### 完整示例

```python
"""
Angela AI - HAM Memory Module
分层关联记忆系统实现。

该模块实现了 HAM (Hierarchical Associative Memory) 记忆系统，
包括记忆存储、检索和管理功能。

Classes:
    HAMMemoryManager: 主记忆管理器。
    HAMImportanceScorer: 重要性评分器。
    HAMQueryEngine: 查询引擎。

Example:
    >>> from apps.backend.src.ai.memory.ham_memory import HAMMemoryManager
    >>> manager = HAMMemoryManager()
    >>> await manager.store("Test memory", {"speaker": "user"})
    'mem_id_123'
"""

from typing import Dict, List, Optional, Any


class HAMMemoryManager:
    """分层关联记忆管理器。

    该类管理 Angela AI 的记忆系统，支持分层存储和语义检索。

    Attributes:
        core_memory: 核心记忆存储。
        vector_store: 向量存储。
        importance_scorer: 重要性评分器。

    Example:
        >>> manager = HAMMemoryManager()
        >>> await manager.initialize()
        >>> mem_id = await manager.store("Hello", {})
        >>> memories = await manager.retrieve("Hello")
    """

    def __init__(self):
        """初始化 HAMMemoryManager。

        创建必要的组件和存储结构。
        """
        self.core_memory = {}
        self.vector_store = None
        self.importance_scorer = None

    async def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """存储记忆到记忆系统。

        Args:
            content: 要存储的内容。
            metadata: 可选的元数据，包括说话者、时间等信息。

        Returns:
            str: 生成的记忆 ID。

        Raises:
            ValueError: 如果内容为空。
            MemoryError: 如果存储失败。

        Example:
            >>> manager = HAMMemoryManager()
            >>> mem_id = await manager.store("Hello world", {"speaker": "user"})
            >>> print(mem_id)
            'mem_abc123'
        """
        if not content:
            raise ValueError("Content cannot be empty")

        metadata = metadata or {}
        mem_id = self._generate_id()

        self.core_memory[mem_id] = {
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }

        return mem_id

    async def retrieve(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """检索相关记忆。

        Args:
            query: 查询文本。
            limit: 返回的最大记忆数量，默认为 10。

        Returns:
            包含相关记忆的列表，每个记忆是包含内容和元数据的字典。

        Raises:
            ValueError: 如果查询为空。

        Example:
            >>> manager = HAMMemoryManager()
            >>> memories = await manager.retrieve("hello", limit=5)
            >>> len(memories)
            3
        """
        if not query:
            raise ValueError("Query cannot be empty")

        # 实现检索逻辑
        return []

    def _generate_id(self) -> str:
        """生成唯一的记忆 ID。

        Returns:
            str: 格式化的记忆 ID。
        """
        import uuid
        return f"mem_{uuid.uuid4().hex[:12]}"
```

## 检查清单

提交代码前，确保:

- [ ] 所有公共函数和类都有 docstring
- [ ] Docstring 使用 Google 风格格式
- [ ] 所有参数都在 Args 节中描述
- [ ] 返回值在 Returns 节中描述
- [ ] 可能的异常在 Raises 节中描述
- [ ] 复杂函数包含 Example 节
- [ ] Docstring 与代码实现保持同步
- [ ] 通过 pydocstyle 检查

## 参考资源

- [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
- [PEP 257 -- Docstring Conventions](https://peps.python.org/pep-0257/)
- [pydocstyle](https://pydocstyle.readthedocs.io/)