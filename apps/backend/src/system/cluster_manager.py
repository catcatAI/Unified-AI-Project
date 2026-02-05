"""
Angela AI v6.0 - Cluster Deployment Manager
集群部屬管理器

基於矩陣架構 (L0~L11) × (4~8) 的分佈式計算實現。
主機負責任務分配，分機負責子矩陣運算與小數點記憶化。

Author: Angela AI Development Team
Version: 1.0.0
Date: 2026-02-05
"""

import asyncio
import logging
import uuid
import time
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class NodeType(Enum):
    MASTER = "master"
    WORKER = "worker"

class PrecisionLevel(Enum):
    FP8 = "fp8"       # 極速/高效 (Efficient)
    FP16 = "fp16"     # 標準 (Standard)
    FP32 = "fp32"     # 高精度 (High)
    FP64 = "fp64"     # 超高精度 (Ultra)
    FP128 = "fp128"   # 矩陣核心精度 (Core)

class PrecisionMode(Enum):
    INT = "int"         # 僅整數 (Integer only)
    DEC1 = "dec1"       # 1位小數 (1 decimal)
    DEC2 = "dec2"       # 2位小數 (2 decimals)
    DEC3 = "dec3"       # 3位小數 (3 decimals)
    DEC4 = "dec4"       # 4位小數 (4 decimals)

@dataclass
class UnifiedStatusTensor:
    """Angela 統一狀態張量 (V × L × P × M)"""
    version_status: str  # Angela 版本狀態 (V)
    maturity_level: int  # 成熟度 L0~L11 (L)
    precision_level: PrecisionLevel # FP8~FP128 (P)
    precision_mode: PrecisionMode   # INT-DEC4 (M)
    
    def to_vector(self) -> Tuple[str, int, str, str]:
        return (self.version_status, self.maturity_level, self.precision_level.value, self.precision_mode.value)

@dataclass
class MatrixShape:
    dimensions: Tuple[int, ...]
    
    def total_elements(self) -> int:
        res = 1
        for d in self.dimensions:
            res *= d
        return res

@dataclass
class ModulePrecision:
    module_name: str
    default_precision: PrecisionLevel
    default_shape: MatrixShape
    dynamic_range: Tuple[PrecisionLevel, PrecisionLevel]
    fp_split_support: bool = False

class PrecisionMap:
    """精度圖譜：定義不同功能模組的精度與矩陣維度"""
    def __init__(self):
        self.map: Dict[str, ModulePrecision] = {
            "Vision": ModulePrecision(
                "Vision", 
                PrecisionLevel.FP16, 
                MatrixShape((8, 8)), 
                (PrecisionLevel.FP8, PrecisionLevel.FP32)
            ),
            "Audio": ModulePrecision(
                "Audio", 
                PrecisionLevel.FP8, 
                MatrixShape((4, 4)), 
                (PrecisionLevel.FP8, PrecisionLevel.FP16)
            ),
            "Logic": ModulePrecision(
                "Logic", 
                PrecisionLevel.FP32, 
                MatrixShape((8, 8, 8, 8)), 
                (PrecisionLevel.FP16, PrecisionLevel.FP64),
                fp_split_support=True
            ),
            "Memory": ModulePrecision(
                "Memory", 
                PrecisionLevel.FP64, 
                MatrixShape((12, 8)), 
                (PrecisionLevel.FP32, PrecisionLevel.FP128),
                fp_split_support=True
            ),
            "Sensory": ModulePrecision(
                "Sensory", 
                PrecisionLevel.FP8, 
                MatrixShape((4, 4)), 
                (PrecisionLevel.FP8, PrecisionLevel.FP16)
            )
        }

    def get_config(self, module_name: str) -> ModulePrecision:
        return self.map.get(module_name, self.map["Logic"])

@dataclass
class MatrixTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module: str = "Logic"
    precision: PrecisionLevel = PrecisionLevel.FP16
    shape: Tuple[int, ...] = (8, 8)
    data_int: List[int] = field(default_factory=list) # 矩陣整數數據
    require_precision: bool = False
    fp_chunks: int = 1 # 如果是 FP128 切分到 FP8，這裡代表塊數
    status_tensor: Optional[UnifiedStatusTensor] = None # 統一狀態張量 (V x L x P x M)
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    efficiency: float = 0.0  # 能效 (Tasks/Watt or similar)
    speed: float = 0.0       # 速度 (Tasks/sec)
    precision: float = 0.0   # 精度 (1.0 - error_rate)
    status_tensor_snapshot: Optional[Tuple[str, int, str, str]] = None # 狀態張量快照
    hardware_usage: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class DecimalMemoizer:
    """小數點記憶化存儲，支援精度等級"""
    def __init__(self):
        # 存儲格式: (module, shape, int_vals_tuple, precision) -> decimal_vals_tuple
        self._memo: Dict[Tuple[str, Tuple[int, ...], Tuple[int, ...], PrecisionLevel], Tuple[float, ...]] = {}
        self.memo_hits = 0
        self.memo_misses = 0
        logger.info("多維精度小數點記憶化存儲已初始化")

    def get_decimals(self, module: str, shape: Tuple[int, ...], int_vals: List[int], precision: PrecisionLevel) -> Optional[List[float]]:
        key = (module, shape, tuple(int_vals), precision)
        vals = self._memo.get(key)
        if vals is not None:
            self.memo_hits += 1
            return list(vals)
        self.memo_misses += 1
        return None

    def store_decimals(self, module: str, shape: Tuple[int, ...], int_vals: List[int], precision: PrecisionLevel, decimal_vals: List[float]):
        key = (module, shape, tuple(int_vals), precision)
        self._memo[key] = tuple(decimal_vals)

class ClusterManager:
    """集群管理器：負責精度圖譜分組與動態任務分配"""
    def __init__(self, node_type: NodeType = NodeType.MASTER):
        self.node_type = node_type
        self.workers: Dict[str, Any] = {}
        self.memoizer = DecimalMemoizer()
        self.precision_map = PrecisionMap()
        self.metrics_history: List[PerformanceMetrics] = []
        
        # 矩陣基礎定義
        self.LAYERS = range(12)
        
        self.metrics_file = Path(__file__).parent.parent.parent.parent.parent / "metrics.md"

    async def distribute_task(self, module_name: str, matrix_data: List[float], custom_precision: Optional[PrecisionLevel] = None) -> str:
        """主機分配任務：根據精度圖譜切分數據並封裝狀態張量"""
        if self.node_type != NodeType.MASTER:
            raise RuntimeError("只有主機節點可以分配任務")

        config = self.precision_map.get_config(module_name)
        precision = custom_precision or config.default_precision
        shape = config.default_shape.dimensions
        
        # 決定精度模式 (M)
        precision_mode = PrecisionMode.INT
        if any(abs(v - int(v)) > 0.0001 for v in matrix_data):
            precision_mode = PrecisionMode.DEC4 # 預設為 DEC4 提升精度
        
        # 封裝統一狀態張量 (V x L x P x M)
        status_tensor = UnifiedStatusTensor(
            version_status="v6.0.4-Production", # V
            maturity_level=7,                   # L (模擬目前成熟度)
            precision_level=precision,          # P
            precision_mode=precision_mode       # M
        )

        # FP128 切分邏輯模擬
        fp_chunks = 1
        if precision == PrecisionLevel.FP128 and config.fp_split_support:
            # 模擬將 FP128 切分為 16 個 FP8 塊
            fp_chunks = 16
            logger.info(f"FP128 精度切分啟動: {module_name} -> {fp_chunks}xFP8 chunks")

        int_vals = [int(v) for v in matrix_data]
        # 檢查是否需要高精度傳輸
        require_precision = precision_mode != PrecisionMode.INT
        
        task = MatrixTask(
            module=module_name,
            precision=precision,
            shape=shape,
            data_int=int_vals,
            require_precision=require_precision,
            fp_chunks=fp_chunks,
            status_tensor=status_tensor
        )
        
        logger.debug(f"主機分配任務 [Tensor: {status_tensor.to_vector()}]: {module_name}")
        return task.task_id

    async def execute_task(self, task: MatrixTask) -> List[float]:
        """分機執行任務：還原數據並應用精度補償"""
        if self.node_type != NodeType.WORKER:
            raise RuntimeError("只有分機節點可以執行任務")

        start_time = time.time()
        
        # 記錄狀態張量上下文
        tensor_info = task.status_tensor.to_vector() if task.status_tensor else ("unknown", 0, "unknown", "unknown")
        logger.info(f"分機執行任務 [狀態張量: {tensor_info}]: {task.module}")
        
        # 處理 FP128 切分還原邏輯 (模擬)
        if task.precision == PrecisionLevel.FP128 and task.fp_chunks > 1:
            logger.info(f"執行 FP128 切分塊運算: {task.module} (Chunk 1/{task.fp_chunks})")
            # 實際實現中，這裡會等待所有塊到達或並行計算後合併
        
        # 嘗試從本地記憶化獲取小數點矩陣
        memoized_decimals = self.memoizer.get_decimals(
            task.module, task.shape, task.data_int, task.precision
        )
        
        if memoized_decimals is not None:
            final_values = [i + d for i, d in zip(task.data_int, memoized_decimals)]
            precision_score = 1.0
            logger.debug(f"精度圖譜記憶命中: {task.module} ({task.precision.value})")
        else:
            if task.require_precision:
                logger.info(f"請求精度圖譜補償: {task.module} ({task.precision.value})")
                # 模擬向主機獲取小數矩陣
                memoized_decimals = await self._request_matrix_precision(task)
                self.memoizer.store_decimals(
                    task.module, task.shape, task.data_int, task.precision, memoized_decimals
                )
                final_values = [i + d for i, d in zip(task.data_int, memoized_decimals)]
                # 根據精度等級計算模擬分數
                precision_weights = {
                    PrecisionLevel.FP8: 0.85,
                    PrecisionLevel.FP16: 0.95,
                    PrecisionLevel.FP32: 0.999,
                    PrecisionLevel.FP64: 0.99999,
                    PrecisionLevel.FP128: 0.999999
                }
                precision_score = precision_weights.get(task.precision, 0.99)
            else:
                final_values = [float(i) for i in task.data_int]
                precision_score = 0.5
            
        execution_time = time.time() - start_time
        self._record_local_metrics(execution_time, precision_score, task.status_tensor)
        
        return final_values

    async def _request_matrix_precision(self, task: MatrixTask) -> List[float]:
        """模擬從主機獲取矩陣精度數據"""
        await asyncio.sleep(0.02) # 多維矩陣網路延遲稍高
        # 返回模擬的小數部分
        return [0.123456 for _ in range(len(task.data_int))]

    def push_decimal_to_worker(self, worker_id: str, layer: int, dim: int, int_val: int, decimal_val: float):
        """主機主動推送小數點記憶到分機，用於預熱或校準"""
        if self.node_type != NodeType.MASTER:
            return
        
        logger.info(f"推送精度數據到 {worker_id}: L{layer}x{dim} -> {decimal_val}")
        # 實際實現中會透過 WebSocket/RPC 發送
    
    def _record_local_metrics(self, exec_time: float, precision: float, status_tensor: Optional[UnifiedStatusTensor] = None):
        """記錄本地執行指標"""
        speed = 1.0 / exec_time if exec_time > 0 else 0
        # 模擬能效計算 (Tasks / sec / normalized_power)
        efficiency = speed / 1.5 
        
        metric = PerformanceMetrics(
            efficiency=efficiency,
            speed=speed,
            precision=precision,
            status_tensor_snapshot=status_tensor.to_vector() if status_tensor else None
        )
        self.metrics_history.append(metric)
        
        # 定期同步到 metrics.md (例如每 100 次任務)
        if len(self.metrics_history) >= 100:
            asyncio.create_task(self.update_metrics_file())

    async def update_metrics_file(self):
        """將指標記錄到指標 MD 中 (最大、最小、平均/時間單位)"""
        if not self.metrics_history:
            return

        speeds = [m.speed for m in self.metrics_history]
        effs = [m.efficiency for m in self.metrics_history]
        precs = [m.precision for m in self.metrics_history]
        
        stats = {
            "speed": {"max": max(speeds), "min": min(speeds), "avg": sum(speeds)/len(speeds)},
            "efficiency": {"max": max(effs), "min": min(effs), "avg": sum(effs)/len(effs)},
            "precision": {"max": max(precs), "min": min(precs), "avg": sum(precs)/len(precs)}
        }
        
        self.metrics_history.clear()
        
        try:
            # 讀取現有內容並更新
            if self.metrics_file.exists():
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 這裡簡單地追加到文件末尾或替換特定標籤
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                new_entry = f"\n### 硬體效能日誌 ({timestamp})\n"
                new_entry += f"- **速度 (Tasks/s)**: Max: {stats['speed']['max']:.2f}, Min: {stats['speed']['min']:.2f}, Avg: {stats['speed']['avg']:.2f}\n"
                new_entry += f"- **能效 (Tasks/W)**: Max: {stats['efficiency']['max']:.2f}, Min: {stats['efficiency']['min']:.2f}, Avg: {stats['efficiency']['avg']:.2f}\n"
                new_entry += f"- **精度 (Score)**: Max: {stats['precision']['max']:.2f}, Min: {stats['precision']['min']:.2f}, Avg: {stats['precision']['avg']:.2f}\n"
                
                with open(self.metrics_file, "a", encoding="utf-8") as f:
                    f.write(new_entry)
                    
                logger.info("已更新 metrics.md 硬體效能日誌")
        except Exception as e:
            logger.error(f"更新 metrics.md 失敗: {e}")

    def add_worker(self, worker_id: str, connection_info: Dict[str, Any]):
        self.workers[worker_id] = connection_info
        logger.info(f"已添加分機節點: {worker_id}")

# 單例模式方便調用
cluster_manager = ClusterManager()
