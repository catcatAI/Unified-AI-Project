"""
Axis Port Channel & Output Manager — Phase 3
==============================================

端口通道：管理端口的數據緩衝（push/pull/peek）
軸輸出管理器：θ 路由驅動的 I/O 操作

使用方式:
    from core.engine.port_channel import PortChannel, AxisOutputManager

    channel = PortChannel(port)
    channel.push(data)

    manager = AxisOutputManager(state_adapter, port_registry)
    manager.output("beta", {"focus": 0.8})

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from core.system.config.magic_numbers import cache_value

if TYPE_CHECKING:
    from core.engine.axis_port_registry import PortRegistry
    from core.engine.state_matrix_adapter import StateMatrixAdapter

logger = logging.getLogger("angela_port_channel")


@dataclass
class PortChannel:
    """
    端口通道 — 管理端口的數據緩衝

    Attributes:
        port_name: 端口名
        buffer: 數據緩衝區（FIFO）
        max_buffer: 最大緩衝大小
        byte_size: 總字節數（估算）
        push_count: 寫入次數
        pull_count: 讀取次數
        last_push: 最後寫入時間
        last_pull: 最後讀取時間
    """
    port_name: str
    max_buffer: int = cache_value("port_channel_buffer", 100)
    buffer: deque = field(default_factory=lambda: deque(maxlen=100))
    byte_size: int = 0
    push_count: int = 0
    pull_count: int = 0
    last_push: float = field(default_factory=time.time)
    last_pull: float = field(default_factory=time.time)

    def push(self, data: Any) -> bool:
        """
        寫入數據到緩衝區

        Args:
            data: 要寫入的數據

        Returns:
            是否成功
        """
        if len(self.buffer) >= self.max_buffer:
            logger.warning(f"[PortChannel] Buffer full for '{self.port_name}', dropping oldest", exc_info=True)
            self.buffer.popleft()

        self.buffer.append(data)
        self.push_count += 1
        self.last_push = time.time()

        if isinstance(data, (dict, list, str)):
            self.byte_size += len(str(data)) if isinstance(data, str) else 64
        elif isinstance(data, bytes):
            self.byte_size += len(data)

        return True

    def pull(self) -> Optional[Any]:
        """
        從緩衝區讀取數據（FIFO）

        Returns:
            最早的數據，緩衝區空則返回 None
        """
        if not self.buffer:
            return None

        data = self.buffer.popleft()
        self.pull_count += 1
        self.last_pull = time.time()

        if isinstance(data, (dict, list, str)):
            self.byte_size -= len(str(data)) if isinstance(data, str) else 64
        elif isinstance(data, bytes):
            self.byte_size -= len(data)
        self.byte_size = max(0, self.byte_size)

        return data

    def peek(self) -> Optional[Any]:
        """窺視最早的數據（不移除）"""
        return self.buffer[0] if self.buffer else None

    def peek_all(self) -> List[Any]:
        """窺視所有數據（不移除）"""
        return list(self.buffer)

    def clear(self) -> int:
        """清空緩衝區，返回清除的數據量"""
        count = len(self.buffer)
        self.buffer.clear()
        self.byte_size = 0
        return count

    def size(self) -> int:
        """當前緩衝區大小"""
        return len(self.buffer)

    def is_empty(self) -> bool:
        """緩衝區是否為空"""
        return len(self.buffer) == 0

    def is_full(self) -> bool:
        """緩衝區是否已滿"""
        return len(self.buffer) >= self.max_buffer

    def summary(self) -> Dict[str, Any]:
        """獲取通道摘要"""
        return {
            "port_name": self.port_name,
            "buffer_size": self.size(),
            "max_buffer": self.max_buffer,
            "fill_ratio": round(len(self.buffer) / max(1, self.max_buffer), 3),
            "byte_size": self.byte_size,
            "push_count": self.push_count,
            "pull_count": self.pull_count,
            "net_flow": self.push_count - self.pull_count,
            "last_push_age": round(time.time() - self.last_push, 2),
            "last_pull_age": round(time.time() - self.last_pull, 2),
        }


class AxisOutputManager:
    """
    軸輸出管理器 — θ 路由驅動的 I/O 操作

    核心功能：
    - output(): 將軸數據路由到輸出端口（θ 決定哪些端口）
    - input(): 從輸入端口合併數據到軸（θ 決定合併策略）
    - batch_output(): 批量輸出多個軸的數據
    - get_port_data(): 獲取端口緩衝區的數據

    θ 路由：
    - 輸出時根據端口 priority 閾值決定是否dispatch
    - 輸入時根據端口 priority 加權合併
    - 由 ThetaRouter.cascade_output() / merge_input() 實現
    """

    def __init__(
        self,
        state_adapter: Optional["StateMatrixAdapter"] = None,
        port_registry: Optional["PortRegistry"] = None,
    ):
        self._state_adapter = state_adapter
        self._port_registry = port_registry
        self._channels: Dict[str, PortChannel] = {}

    def _get_channel(self, port_name: str) -> PortChannel:
        """獲取或創建端口通道"""
        if port_name not in self._channels:
            self._channels[port_name] = PortChannel(port_name=port_name)
        return self._channels[port_name]

    def push_to_port(self, port_name: str, data: Any) -> bool:
        """寫入數據到端口緩衝區"""
        port = self._port_registry.get_port(port_name) if self._port_registry else None
        if not port:
            logger.warning(f"[AxisOutputManager] Port '{port_name}' not registered", exc_info=True)
            return False

        channel = self._get_channel(port_name)
        return channel.push(data)

    def pull_from_port(self, port_name: str) -> Optional[Any]:
        """從端口緩衝區讀取數據"""
        channel = self._channels.get(port_name)
        if not channel:
            return None
        return channel.pull()

    def peek_port(self, port_name: str) -> Optional[Any]:
        """窺視端口緩衝區（不移除）"""
        channel = self._channels.get(port_name)
        if not channel:
            return None
        return channel.peek()

    def output(self, axis_name: str, data: Dict[str, float]) -> Dict[str, Any]:
        """
        將軸的數據輸出到所有綁定的端口（由 θ 路由決定）

        Args:
            axis_name: 軸名
            data: 軸數據 {"field": value, ...}

        Returns:
            輸出結果摘要
        """
        if not self._port_registry:
            return {"status": "no_registry"}

        outputs = self._port_registry.get_outputs_for_axis(axis_name)
        if not outputs:
            return {"status": "no_outputs", "axis": axis_name}

        dispatched = 0
        results = {}
        threshold = 0.6

        for port in outputs:
            if port.priority >= threshold:
                channel = self._get_channel(port.name)
                channel.push({"axis": axis_name, "data": data, "timestamp": time.time()})
                dispatched += 1
                results[port.name] = {"status": "dispatched", "priority": port.priority}
            else:
                results[port.name] = {"status": "skipped", "priority": port.priority}

        logger.info(f"[AxisOutputManager] output('{axis_name}') → {dispatched}/{len(outputs)} ports dispatched")

        return {
            "status": "completed",
            "axis": axis_name,
            "total": len(outputs),
            "dispatched": dispatched,
            "results": results,
        }

    def input(self, axis_name: str) -> Dict[str, Any]:
        """
        從所有綁定的輸入端口讀取並合併數據到軸

        Args:
            axis_name: 目標軸名

        Returns:
            合併後的數據摘要
        """
        if not self._port_registry:
            return {"status": "no_registry"}

        inputs = self._port_registry.get_inputs_for_axis(axis_name)
        if not inputs:
            return {"status": "no_inputs", "axis": axis_name}

        merged: Dict[str, float] = {}
        total_weight = 0.0

        for port in inputs:
            channel = self._channels.get(port.name)
            if not channel or channel.is_empty():
                continue

            data = channel.peek()
            if not isinstance(data, dict) or "data" not in data:
                continue

            port_data = data["data"]
            weight = port.priority
            total_weight += weight

            for key, value in port_data.items():
                if isinstance(value, (int, float)):
                    if key not in merged:
                        merged[key] = 0.0
                    merged[key] += value * weight

        if total_weight > 0:
            for key in merged:
                merged[key] /= total_weight

        logger.info(f"[AxisOutputManager] input('{axis_name}') ← {len(inputs)} ports, {len(merged)} fields merged")

        return {
            "status": "completed",
            "axis": axis_name,
            "inputs": len(inputs),
            "merged": merged,
            "total_weight": total_weight,
        }

    def batch_output(self, data_dict: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        批量輸出多個軸的數據

        Args:
            data_dict: {axis_name: data, ...}

        Returns:
            批量輸出結果
        """
        results = {}
        for axis_name, data in data_dict.items():
            results[axis_name] = self.output(axis_name, data)

        return {
            "status": "batch_completed",
            "axes": len(results),
            "total_dispatched": sum(1 for r in results.values() if r.get("status") == "completed" for v in r.get("results", {}).values() if v.get("status") == "dispatched"),
            "details": results,
        }

    def get_port_summary(self, port_name: str) -> Dict[str, Any]:
        """獲取端口通道摘要"""
        channel = self._channels.get(port_name)
        if not channel:
            return {"port_name": port_name, "status": "no_channel"}
        return channel.summary()

    def get_all_channel_summaries(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有端口通道摘要"""
        return {name: ch.summary() for name, ch in self._channels.items()}

    def clear_channel(self, port_name: str) -> int:
        """清空端口通道"""
        channel = self._channels.get(port_name)
        if not channel:
            return 0
        return channel.clear()