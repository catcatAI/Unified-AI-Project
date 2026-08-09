# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 主幹線五個註冊表（matrix/axis/module/dictionary/translator）
#       （§6 module structure — registry.py）
# 維度: ζ 連通維度（跨模組耦合、同步狀態）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸主幹線註冊表概念
#
# =============================================================================

"""主幹線註冊表（§6 registry.py）。

五個註冊表：
- matrix：狀態矩陣實例（`StateMatrix4D` 等）。
- axis：座標軸（維度）註冊與讀寫存取。
- module：已註冊的元件/模組（Router、ChatService、ED3NEngine…）。
- dictionary：字典（DictionaryLayer / VectorDictionary…）。
- translator：轉譯器（§5.3 TranslationRule）。

主幹線為「薄註冊表 + 路由」，不持有業務邏輯；此處僅做註冊/查詢/登出。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.backbone.contracts import TranslationRule


class RegistryError(RuntimeError):
    """註冊表錯誤（重複註冊 / 未知鍵）。"""


class _BaseRegistry:
    """通用註冊表基底。"""

    def __init__(self, name: str, allow_replace: bool = False) -> None:
        self.name = name
        self.allow_replace = allow_replace
        self._items: Dict[str, Any] = {}

    def register(self, key: str, item: Any) -> None:
        if key in self._items and not self.allow_replace:
            raise RegistryError(f"Duplicate {self.name} registration: {key}")
        self._items[key] = item

    def unregister(self, key: str) -> bool:
        return self._items.pop(key, None) is not None

    def get(self, key: str, default: Any = None) -> Any:
        return self._items.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._items

    def keys(self) -> List[str]:
        return list(self._items.keys())

    def all(self) -> Dict[str, Any]:
        return dict(self._items)

    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()


class MatrixRegistry(_BaseRegistry):
    """狀態矩陣實例註冊表。

    主矩陣（`StateMatrix4D`）可經 `register("state_matrix4d", m)` 註冊；
    `primary()` 回傳第一個註冊的矩陣（視為主要）。
    """

    def __init__(self) -> None:
        super().__init__("matrix", allow_replace=True)

    def primary(self) -> Any:
        if not self._items:
            return None
        return next(iter(self._items.values()))


class AxisRegistry(_BaseRegistry):
    """座標軸（維度）註冊表。

    每個維度（alpha/beta/gamma/delta/epsilon/theta/zeta/eta）可註冊對應的
    座標軸物件；`read`/`write` 提供統一存取。若未註冊則回傳 None / 忽略。
    """

    def __init__(self) -> None:
        super().__init__("axis", allow_replace=True)

    def read(self, axis: str, key: Optional[str] = None, default: Any = None) -> Any:
        obj = self._items.get(axis)
        if obj is None:
            return default
        try:
            if key is not None:
                return obj.get(key, default)
            return obj
        except AttributeError:
            return default

    def write(self, axis: str, key: str, value: Any) -> bool:
        """以統一 API 寫入軸值（不直接改 `.values[]`，§8 繞過 API 修正）。

        優先呼叫物件的 `set`/`update` 方法；若物件為 dict 則更新鍵。
        """
        obj = self._items.get(axis)
        if obj is None:
            return False
        try:
            if hasattr(obj, "set") and callable(obj.set):
                obj.set(key, value)
                return True
            if hasattr(obj, "update") and callable(obj.update):
                obj.update({key: value})
                return True
            if isinstance(obj, dict):
                obj[key] = value
                return True
        except Exception:
            return False
        return False

    def update(self, axis: str, data: Dict[str, Any]) -> bool:
        """一次寫入多個軸值。"""
        obj = self._items.get(axis)
        if obj is None:
            return False
        try:
            if hasattr(obj, "update") and callable(obj.update):
                obj.update(data)
                return True
            if isinstance(obj, dict):
                obj.update(data)
                return True
        except Exception:
            return False
        return False


class ModuleRegistry(_BaseRegistry):
    """元件/模組註冊表。

    註冊 `Router`、`ChatService`、`ED3NEngine` 等既有單例，讓主幹線可統一
    路由至對應元件。註冊時可附 `on_mount`/`on_unmount` 回呼（§4 掛載機制）。
    """

    def __init__(self) -> None:
        super().__init__("module", allow_replace=True)
        self._mount_hooks: Dict[str, Callable[[], None]] = {}
        self._unmount_hooks: Dict[str, Callable[[], None]] = {}

    def register(
        self,
        key: str,
        item: Any,
        on_mount: Optional[Callable[[], None]] = None,
        on_unmount: Optional[Callable[[], None]] = None,
    ) -> None:
        super().register(key, item)
        if on_mount is not None:
            self._mount_hooks[key] = on_mount
        if on_unmount is not None:
            self._unmount_hooks[key] = on_unmount

    def mount(self, key: str) -> bool:
        if key not in self._items:
            return False
        hook = self._mount_hooks.get(key)
        if hook is not None:
            try:
                hook()
            except Exception:
                return False
        return True

    def unmount(self, key: str) -> bool:
        if key not in self._items:
            return False
        hook = self._unmount_hooks.get(key)
        if hook is not None:
            try:
                hook()
            except Exception:
                return False
        return True


class DictionaryRegistry(_BaseRegistry):
    """字典註冊表（DictionaryLayer / VectorDictionary / 其他語義字典）。

    `register(name, dict_instance)`；`lookup(name)` 取得字典實例。
    也可註冊 `Mountable` 字典以支援按需掛載（§4.4）。
    """

    def __init__(self) -> None:
        super().__init__("dictionary", allow_replace=True)
        self._mountables: Dict[str, Any] = {}

    def register_mountable(self, key: str, mountable: Any) -> None:
        self._mountables[key] = mountable

    def is_mountable(self, key: str) -> bool:
        return key in self._mountables

    def get_mountable(self, key: str, default: Any = None) -> Any:
        return self._mountables.get(key, default)


class TranslatorRegistry(_BaseRegistry):
    """轉譯器註冊表（§5.3）。

    `register(name, rule)` 接受實作 `TranslationRule` 協定的物件，或簡單的
    `(can_translate, translate)` 可呼叫對。
    """

    def __init__(self) -> None:
        super().__init__("translator", allow_replace=False)

    def register_rule(self, name: str, rule: Any) -> None:
        """註冊 TranslationRule 協定物件。"""
        super().register(name, rule)

    def register_func(
        self,
        name: str,
        can_translate: Callable[[str, str, str], bool],
        translate: Callable[..., Any],
    ) -> None:
        """以可呼叫對註冊簡易轉譯器。"""

        def _make_rule() -> Any:
            rule_name = name

            class _FuncRule:
                @property
                def name(self) -> str:
                    return rule_name

                def can_translate(self, source: str, target: str, direction: str) -> bool:
                    return can_translate(source, target, direction)

                def translate(self, data: Any, direction: str = "down", **kwargs: Any) -> Any:
                    return translate(data, direction=direction, **kwargs)

            return _FuncRule()

        super().register(name, _make_rule())

    def find(self, source: str, target: str, direction: str) -> Optional[Any]:
        """尋找第一個可處理 source→target/direction 的轉譯器。"""
        for rule in self._items.values():
            try:
                if rule.can_translate(source, target, direction):
                    return rule
            except Exception:
                continue
        return None


class BackboneRegistries:
    """主幹線五個註冊表的聚合容器（§6）。"""

    def __init__(self) -> None:
        self.matrices = MatrixRegistry()
        self.axes = AxisRegistry()
        self.modules = ModuleRegistry()
        self.dictionaries = DictionaryRegistry()
        self.translators = TranslatorRegistry()

    def clear_all(self) -> None:
        self.matrices.clear()
        self.axes.clear()
        self.modules.clear()
        self.dictionaries.clear()
        self.translators.clear()
