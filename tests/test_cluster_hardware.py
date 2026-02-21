import asyncio
import logging
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend"))

from src.system.hardware_probe import HardwareProbe
from src.system.deployment_manager import DeploymentManager
from src.system.cluster_manager import (
    ClusterManager,
    NodeType,
    PrecisionLevel,
    PrecisionMode,
    MatrixTask,
    UnifiedStatusTensor,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_hardware_and_cluster():
    print("🚀 開始硬體感知與集群邏輯驗證...")

    # 1. 驗證硬體探針
    print("\n🔍 1. 驗證硬體探針 (Hardware Probe)...")
    probe = HardwareProbe()
    profile = probe.get_hardware_profile()
    print(
        f"✅ 硬體概覽: {profile.cpu.brand} | {len(profile.gpu)} GPU(s) | {profile.memory.total // 1024} GB RAM"
    )
    print(f"✅ 效能分級: {profile.performance_tier} (Score: {profile.ai_capability_score})")

    # 2. 驗證部署管理器
    print("\n🔍 2. 驗證部署管理器 (Deployment Manager)...")
    dm = DeploymentManager(probe=probe)
    config = dm.generate_config(cluster_mode=True)
    print(f"✅ 部署模式: {config.mode.value}")
    print(
        f"✅ 模型配置: Size={config.model_config.size.value}, Precision={config.model_config.precision}"
    )
    print(f"✅ 集群角色: {config.cluster_role}")

    # 3. 驗證集群管理器與精度圖譜
    print("\n🔍 3. 驗證集群管理器 (Cluster Manager)...")
    master = ClusterManager(node_type=NodeType.MASTER)
    worker = ClusterManager(node_type=NodeType.WORKER)

    # 測試精度圖譜
    vision_config = master.precision_map.get_config("Vision")
    print(
        f"✅ Vision 精度圖譜: {vision_config.default_precision.value}, Shape: {vision_config.default_shape.dimensions}"
    )

    # 4. 驗證任務封裝與狀態張量
    print("\n🔍 4. 驗證任務封裝與狀態張量 (V x L x P x M)...")
    test_data = [1.5, 2.7, 3.1415, 4.2]

    # 模擬主機分配任務
    status_tensor = UnifiedStatusTensor(
        version_status="v6.0.4-Test",
        maturity_level=5,
        precision_level=PrecisionLevel.FP32,
        precision_mode=PrecisionMode.DEC4,
    )

    task = MatrixTask(
        module="Vision",
        precision=PrecisionLevel.FP32,
        shape=(2, 2),
        data_int=[1, 2, 3, 4],
        status_tensor=status_tensor,
        payload={"decimals": [0.5, 0.7, 0.1415, 0.2]},
    )

    print(f"✅ 任務封裝成功: ID={task.task_id}, Module={task.module}")
    print(f"✅ 狀態張量向量: {task.status_tensor.to_vector()}")

    # 5. 驗證分機執行與記憶化
    print("\n🔍 5. 驗證分機執行與小數點記憶化...")
    # 模擬分機執行
    worker_result = await worker.execute_task(task)
    print(f"✅ 分機執行結果 (前2位): {worker_result[:2]}")

    # 驗證記憶化命中
    hit_result = worker.memoizer.get_decimals("Vision", (2, 2), [1, 2, 3, 4], PrecisionLevel.FP32)
    if hit_result:
        print(f"✅ 小數點記憶化命中驗證通過")
    else:
        print(f"❌ 小數點記憶化未命中!")

    print("\n🎉 硬體感知與集群邏輯驗證完成！系統底層矩陣架構運行正常。")


if __name__ == "__main__":
    asyncio.run(test_hardware_and_cluster())
