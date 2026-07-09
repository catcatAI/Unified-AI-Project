"""

HookRegistry — C3: backend hook system for plugins.
Defines named hooks, registers handlers, executes them asynchronously.
"""

from core.utils import safe_error

import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Hook:
    name: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HookResult:
    hook_name: str
    handler_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None


class HookRegistry:
    """Central registry for hook definitions and handler registration."""

    def __init__(self):
        self._hooks: Dict[str, Hook] = {}
        self._handlers: Dict[str, List[tuple[str, Callable]]] = {}

    def define_hook(self, name: str, description: str = "") -> Hook:
        """Define a new hook that plugins can subscribe to."""
        hook = Hook(name=name, description=description)
        self._hooks[name] = hook
        if name not in self._handlers:
            self._handlers[name] = []
        return hook

    def get_hook(self, name: str) -> Optional[Hook]:
        """Get hook definition by name."""
        return self._hooks.get(name)

    def list_hooks(self) -> List[Dict[str, Any]]:
        """List all defined hooks with handler counts."""
        return [
            {
                "name": h.name,
                "description": h.description,
                "handler_count": len(self._handlers.get(h.name, [])),
            }
            for h in self._hooks.values()
        ]

    def register_handler(self, hook_name: str, handler_name: str, handler: Callable) -> bool:
        """Register a handler function for a hook."""
        if hook_name not in self._hooks:
            logger.warning(f"[HookRegistry] Unknown hook '{hook_name}', defining automatically", exc_info=True)
            self.define_hook(hook_name)
        self._handlers[hook_name].append((handler_name, handler))
        return True

    def unregister_handler(self, hook_name: str, handler_name: str) -> bool:
        """Remove a handler by name."""
        if hook_name not in self._handlers:
            return False
        before = len(self._handlers[hook_name])
        self._handlers[hook_name] = [
            (n, h) for n, h in self._handlers[hook_name] if n != handler_name
        ]
        return len(self._handlers[hook_name]) < before

    async def execute_pipeline(self, hook_name: str, initial_data: Any = None) -> Any:
        """Execute all handlers in sequence, passing modified data through the chain."""
        if hook_name not in self._handlers:
            return initial_data
        current = initial_data
        for handler_name, handler in self._handlers[hook_name]:
            try:
                result = handler(current)
                if inspect.iscoroutine(result):
                    result = await result
                current = result
            except Exception as e:
                logger.error(f"[HookRegistry] Pipeline handler '{handler_name}' failed: {e}", exc_info=True)
        return current

    async def execute_hook(self, hook_name: str, data: Any = None) -> List[HookResult]:
        """Execute all registered handlers for a hook asynchronously."""
        if hook_name not in self._handlers:
            return []
        results = []
        for handler_name, handler in self._handlers[hook_name]:
            try:
                result = handler(data)
                if inspect.iscoroutine(result):
                    result = await result
                results.append(HookResult(
                    hook_name=hook_name,
                    handler_name=handler_name,
                    success=True,
                    result=result,
                ))
            except Exception as e:
                logger.error(f"[HookRegistry] Handler '{handler_name}' for hook '{hook_name}' failed: {e}", exc_info=True)
                results.append(HookResult(
                    hook_name=hook_name,
                    handler_name=handler_name,
                    success=False,
                    error=safe_error(e),
                ))
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "hook_count": len(self._hooks),
            "handler_count": sum(len(h) for h in self._handlers.values()),
            "hooks": self.list_hooks(),
        }


# Singleton
hook_registry = HookRegistry()
