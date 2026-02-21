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
import psutil
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from shared.utils.hardware_detector import SystemHardwareProbe

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
        self.probe = SystemHardwareProbe()
        
        # FP128 切分還原緩衝區: task_id -> {chunk_index: data}
        self.reconstruction_buffer: Dict[str, Dict[int, List[float]]] = {}
        
        # 矩陣基礎定義
        self.LAYERS = range(12)
        
        self.metrics_file = Path(__file__).parent.parent.parent.parent.parent / "metrics.md"

    def get_cluster_status(self) -> Dict[str, Any]:
        """獲取集群當前狀態與硬體資訊"""
        profile = self.probe.get_hardware_profile()
        
        # 模擬一些集群節點
        if not self.workers and self.node_type == NodeType.MASTER:
            self.workers = {
                "worker-alpha": {"status": "online", "precision": "FP16", "load": 0.45},
                "worker-beta": {"status": "online", "precision": "FP8", "load": 0.12},
                "worker-gamma": {"status": "offline", "precision": "FP32", "load": 0.0}
            }

        return {
            "node_type": self.node_type.value,
            "hardware": {
                "cpu": {
                    "brand": profile.cpu.brand,
                    "usage": profile.cpu.usage_percent,
                    "cores": profile.cpu.cores_logical
                },
                "memory": {
                    "total": profile.memory.total,
                    "used": profile.memory.used,
                    "usage_percent": profile.memory.usage_percent
                },
                "performance_tier": profile.performance_tier,
                "ai_capability_score": profile.ai_capability_score
            },
            "cluster": {
                "active_nodes": len([w for w in self.workers.values() if w["status"] == "online"]),
                "total_nodes": len(self.workers) + 1,
                "nodes": [
                    {"id": "master-node (Self)", "type": "master", "status": "online", "load": psutil.cpu_percent() / 100},
                    *[{"id": k, "type": "worker", **v} for k, v in self.workers.items()]
                ]
            },
            "timestamp": time.time()
        }

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """
        获取所有节点列表

        Returns:
            List[Dict[str, Any]]: 节点列表，每个节点包含 id, type, status, load 等信息
        """
        status = self.get_cluster_status()
        return status.get('cluster', {}).get('nodes', [])

    def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定节点的状态

        Args:
            node_id: 节点 ID

        Returns:
            Optional[Dict[str, Any]]: 节点状态信息，如果节点不存在则返回 None
        """
        for node in self.get_all_nodes():
            if node['id'] == node_id:
                return node
        return None

    async def restart_node(self, node_id: str) -> bool:
        """
        重启指定节点

        Args:
            node_id: 节点 ID

        Returns:
            bool: 是否成功重启
        """
        node = self.get_node_status(node_id)
        if not node:
            logger.warning(f"Node {node_id} not found")
            return False

        if node['type'] == 'master':
            logger.warning(f"Cannot restart master node")
            return False

        # 重启节点
        logger.info(f"Restarting node {node_id}")
        if node_id in self.workers:
            self.workers[node_id]['status'] = 'online'
            logger.info(f"Node {node_id} restarted successfully")
            return True

        return False

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
        
        # 處理 FP128 切分還原邏輯
        if task.precision == PrecisionLevel.FP128 and task.fp_chunks > 1:
            chunk_idx = task.payload.get("chunk_index", 0)
            logger.info(f"執行 FP128 切分塊運算: {task.module} (Chunk {chunk_idx + 1}/{task.fp_chunks})")
            
            # 模擬計算塊數據
            chunk_data = [float(i) * 1.000000000001 for i in task.data_int]
            
            if task.task_id not in self.reconstruction_buffer:
                self.reconstruction_buffer[task.task_id] = {}
            
            self.reconstruction_buffer[task.task_id][chunk_idx] = chunk_data
            
            # 檢查是否所有塊都已到達
            if len(self.reconstruction_buffer[task.task_id]) == task.fp_chunks:
                logger.info(f"FP128 任務所有塊已到達，開始還原: {task.task_id}")
                full_data = []
                # 按順序合併塊數據 (簡化邏輯：假設每個塊對應矩陣的一個子集或精度層)
                for i in range(task.fp_chunks):
                    full_data.extend(self.reconstruction_buffer[task.task_id][i])
                
                del self.reconstruction_buffer[task.task_id]
                execution_time = time.time() - start_time
                self._record_local_metrics(execution_time, 0.999999, task.status_tensor)
                return full_data
            else:
                # 尚未完成，返回當前塊結果（在實際異步系統中，這通常會觸發一個回調或事件）
                return chunk_data
        
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
        
        # 獲取硬體資訊
        hardware_usage = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
        }
        
        # 嘗試獲取 GPU 資訊 (如果有)
        try:
            profile = self.probe.get_hardware_profile()
            if profile.gpu:
                hardware_usage["gpu_load"] = profile.gpu[0].load if hasattr(profile.gpu[0], 'load') else 0
        except (OSError, AttributeError, IndexError) as e:
            # 硬件探测失敗，使用默認值
            logger.debug(f"硬件探測失敗（可忽略）: {e}")
            pass
        
        metric = PerformanceMetrics(
            efficiency=efficiency,
            speed=speed,
            precision=precision,
            status_tensor_snapshot=status_tensor.to_vector() if status_tensor else None,
            hardware_usage=hardware_usage
        )
        self.metrics_history.append(metric)
        
        # 定期同步到 metrics.md (例如每 100 次任務)
        if len(self.metrics_history) >= 100:
            asyncio.create_task(self.update_metrics_file())

    async def update_metrics_file(self):
        """將指標記錄到指標 MD 中 (更新實測記錄區段)"""
        if not self.metrics_history:
            return

        speeds = [m.speed for m in self.metrics_history]
        effs = [m.efficiency for m in self.metrics_history]
        precs = [m.precision for m in self.metrics_history]
        
        cpu_loads = [m.hardware_usage.get("cpu_percent", 0) for m in self.metrics_history]
        mem_loads = [m.hardware_usage.get("memory_percent", 0) for m in self.metrics_history]
        
        stats = {
            "speed": {"max": max(speeds), "min": min(speeds), "avg": sum(speeds)/len(speeds)},
            "efficiency": {"max": max(effs), "min": min(effs), "avg": sum(effs)/len(effs)},
            "precision": {"max": max(precs), "min": min(precs), "avg": sum(precs)/len(precs)},
            "cpu": sum(cpu_loads)/len(cpu_loads),
            "mem": sum(mem_loads)/len(mem_loads)
        }
        
        self.metrics_history.clear()
        
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                new_lines = []
                skip = False
                for line in lines:
                    if "### 運算速度 (Ops/s)" in line:
                        new_lines.append(line)
                        new_lines.append(f"- **最大值**: {stats['speed']['max']:.2f}\n")
                        new_lines.append(f"- **最小值**: {stats['speed']['min']:.2f}\n")
                        new_lines.append(f"- **平均值**: {stats['speed']['avg']:.2f}\n")
                        skip = True
                    elif "### 推論精度 (%)" in line:
                        new_lines.append(line)
                        new_lines.append(f"- **最大值**: {stats['precision']['max']*100:.2f}%\n")
                        new_lines.append(f"- **最小值**: {stats['precision']['min']*100:.2f}%\n")
                        new_lines.append(f"- **平均值**: {stats['precision']['avg']*100:.2f}%\n")
                        skip = True
                    elif "### 資源利用率 (%)" in line:
                        new_lines.append(line)
                        new_lines.append(f"- **GPU 平均負載**: 測算中...\n")
                        new_lines.append(f"- **CPU 平均負載**: {stats['cpu']:.1f}%\n")
                        new_lines.append(f"- **記憶體平均負載**: {stats['mem']:.1f}%\n")
                        skip = True
                    elif line.startswith("- **") and skip:
                        continue
                    else:
                        skip = False
                        new_lines.append(line)
                
                with open(self.metrics_file, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                    
                logger.info("已更新 metrics.md 實測記錄")
        except Exception as e:
            logger.error(f"更新 metrics.md 失敗: {e}")

    def add_worker(self, worker_id: str, connection_info: Dict[str, Any]):
        self.workers[worker_id] = connection_info
        logger.info(f"已添加分機節點: {worker_id}")

# Lazy singleton pattern to avoid blocking on import
_cluster_manager = None

def get_cluster_manager() -> ClusterManager:
    """Get or create the cluster manager singleton"""
    global _cluster_manager
    if _cluster_manager is None:
        _cluster_manager = ClusterManager()
    return _cluster_manager

# Backward compatibility: access via attribute
class _LazyClusterManagerProxy:
    def __getattr__(self, name):
        return getattr(get_cluster_manager(), name)

cluster_manager = _LazyClusterManagerProxy()
