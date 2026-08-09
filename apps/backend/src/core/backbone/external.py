# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 下層「外部閘道」（§5.5.1）— ExternalGateway + call_external
#       （步驟 B3/B4: 包裝 LLM providers + 成對排程 backbone.io.submit/resolve）
# 維度: ζ 連通維度（外部服務統一進出）；η 執行維度（資源/逾時）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸外部閘道概念
#
# =============================================================================

"""下層「外部閘道」（§5.5.1 / 步驟 B3、B4）。

外部服務（LLM providers、天氣、Drive、搜尋、Atlassian、OS bridge、MCP）統一經
**下層的外部閘道**進出。元件不得直接 `import` 這些服務。

```python
backbone.register_external("llm.openai", OpenAIProvider)      # 包裝 providers/*.py
result = await backbone.call_external("llm.openai", "generate", prompt=..., ...)
# 內建: 重試 (RetryPolicy) + 熔斷 (CircuitBreaker) + rate-limit
```

成對排程（步驟 B4）：`call_external` 每次呼叫經 `backbone.io.submit/resolve`，
獲得成對追蹤與 ORPHAN 診斷；失敗/逾時對標記 ERROR/ORPHAN，永不靜默。
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from core.backbone.contracts import Envelope, EnvelopeKind

logger = logging.getLogger("angela_backbone_external")


class ExternalBackend:
    """外部服務後端的統一介面（§5.5.1）。

    任何外部服務（LLM provider、weather、drive…）包裝為此介面：
    `async call(method, **kwargs) -> Any`。方法不存在時拋 `AttributeError`。
    """

    def __init__(self, name: str, provider: Any) -> None:
        self.name = name
        self._provider = provider

    async def call(self, method: str, **kwargs: Any) -> Any:
        fn = getattr(self._provider, method, None)
        if fn is None:
            raise AttributeError(f"{self.name} has no method '{method}'")
        result = fn(**kwargs)
        if hasattr(result, "__await__"):
            return await result
        return result

    def has_method(self, method: str) -> bool:
        return callable(getattr(self._provider, method, None))


class ExternalGateway:
    """外部閘道（§5.5.1）。

    Args:
        pair_scheduler: `PairScheduler`（可選，成對追蹤 backbone.io.submit）。
        io: `BackboneIO`（可選，成對入口 backbone.io）。
        retry_policy: 重試策略（預設 `RetryPolicy` 3 次）。
        circuit_breaker: 熔斷器（預設 `CircuitBreaker` 5 次失敗）。
        rate_limit: 每秒最大呼叫數（0 = 不限）。
    """

    def __init__(
        self,
        pair_scheduler: Any = None,
        io: Any = None,
        retry_policy: Any = None,
        circuit_breaker: Any = None,
        rate_limit: int = 0,
    ) -> None:
        self.pairs = pair_scheduler
        self.io = io
        self._backends: Dict[str, ExternalBackend] = {}
        self._retry_policy = retry_policy
        self._circuit_breaker = circuit_breaker
        self._rate_limit = rate_limit
        self._call_times: list = []

    # ------------------------------------------------------------------
    # 註冊
    # ------------------------------------------------------------------
    def register(self, name: str, provider: Any) -> None:
        """註冊外部服務後端（包裝為 ExternalBackend）。"""
        self._backends[name] = ExternalBackend(name, provider)

    def register_backend(self, name: str, backend: Any) -> None:
        """註冊已包裝的 ExternalBackend。"""
        self._backends[name] = backend

    def unregister(self, name: str) -> bool:
        return self._backends.pop(name, None) is not None

    def names(self) -> list:
        return list(self._backends.keys())

    def has(self, name: str) -> bool:
        return name in self._backends

    def get_backend(self, name: str, default: Any = None) -> Any:
        return self._backends.get(name, default)

    # ------------------------------------------------------------------
    # rate-limit
    # ------------------------------------------------------------------
    def _check_rate_limit(self) -> None:
        if self._rate_limit <= 0:
            return
        now = time.monotonic()
        window_start = now - 1.0
        self._call_times = [t for t in self._call_times if t > window_start]
        if len(self._call_times) >= self._rate_limit:
            raise RuntimeError(f"ExternalGateway rate limit exceeded ({self._rate_limit}/s)")
        self._call_times.append(now)

    # ------------------------------------------------------------------
    # 呼叫（成對排程，步驟 B4）
    # ------------------------------------------------------------------
    async def call_external(
        self,
        name: str,
        method: str,
        timeout: float = 8.0,
        retries: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """呼叫外部服務（內建重試 + 熔斷 + rate-limit + 成對追蹤）。

        流程（步驟 B4）：
        1. `_check_rate_limit()` 節流。
        2. 建立輸入信封，`backbone.io.submit` 取得 pair_id（成對追蹤）。
        3. 執行 `ExternalBackend.call(method, **kwargs)`（可包 RetryPolicy/
           CircuitBreaker）。
        4. 成功 → `backbone.io.resolve`；失敗/逾時 → 標記 ERROR/ORPHAN，
           永不靜默。
        """
        self._check_rate_limit()
        backend = self._backends.get(name)
        if backend is None:
            raise KeyError(f"External backend not registered: {name}")

        envelope = Envelope(
            payload={"name": name, "method": method, "kwargs": kwargs},
            kind=EnvelopeKind.EXTERNAL,
            source="external_gateway",
            target=name,
        )
        pair_id: Optional[str] = None
        if self.pairs is not None:
            pair_id = self.pairs.submit(envelope, timeout=timeout, kind=EnvelopeKind.EXTERNAL)

        try:
            result = await self._run_with_resilience(backend, method, timeout, retries, **kwargs)
        except Exception as exc:
            logger.warning("call_external %s.%s failed: %s", name, method, exc, exc_info=True)
            if pair_id is not None and self.pairs is not None:
                try:
                    self.pairs.fail(pair_id, reason=str(exc))
                except Exception:
                    pass
            raise
        else:
            if pair_id is not None and self.pairs is not None:
                output = Envelope(
                    payload=result,
                    kind=EnvelopeKind.EXTERNAL,
                    direction="up",
                    correlation_id=envelope.correlation_id,
                    source=name,
                    target="external_gateway",
                )
                try:
                    self.pairs.resolve(pair_id, output)
                except Exception:
                    pass
            return result

    async def _run_with_resilience(
        self,
        backend: ExternalBackend,
        method: str,
        timeout: float,
        retries: Optional[int],
        **kwargs: Any,
    ) -> Any:
        async def _call() -> Any:
            return await asyncio.wait_for(backend.call(method, **kwargs), timeout=timeout)

        if retries is not None and retries > 0 and self._retry_policy is not None:
            from shared.network_resilience import RetryPolicy

            policy = RetryPolicy(max_retries=retries)
            return await policy.execute(_call)

        if self._circuit_breaker is not None:
            return await self._circuit_breaker.call(_call)

        return await _call()
