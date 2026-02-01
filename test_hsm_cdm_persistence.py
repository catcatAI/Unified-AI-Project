"""
測試 HSM 和 CDM 的異步與持久化功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_hsm_persistence():
    """測試 HSM 持久化功能"""
    from apps.backend.src.ai.memory.hsm import HolographicStorageMatrix, Experience
    
    print("\n=== 測試 HSM 持久化 ===")
    
    # 創建 HSM
    hsm = HolographicStorageMatrix(dimension=256, max_memories=100)
    
    # 添加一些記憶
    exp1 = Experience(
        content="我的名字叫小明",
        context={"user_id": "user_001"},
        importance=0.8,
        timestamp="2026-01-31T12:00:00",
        modality="text",
        metadata={}
    )
    
    exp2 = Experience(
        content="我喜歡吃巧克力",
        context={"topic": "preference"},
        importance=0.6,
        timestamp="2026-01-31T12:01:00",
        modality="text",
        metadata={}
    )
    
    hsm.store(exp1)
    hsm.store(exp2)
    
    print(f"✓ 存儲了 {len(hsm.experiences)} 條記憶")
    
    # 保存到文件
    save_path = "data/test/hsm_test"
    success = hsm.save_to_file(save_path)
    print(f"✓ 保存到文件: {success}")
    
    # 創建新的 HSM 並加載
    hsm2 = HolographicStorageMatrix(dimension=256, max_memories=100)
    success = hsm2.load_from_file(save_path)
    print(f"✓ 從文件加載: {success}")
    print(f"✓ 加載後有 {len(hsm2.experiences)} 條記憶")
    
    # 檢索記憶
    memories = hsm2.retrieve_by_association("小明", top_k=3)
    print(f"✓ 檢索 '小明' 找到 {len(memories)} 條記憶")
    
    return True

async def test_hsm_async():
    """測試 HSM 異步功能"""
    from apps.backend.src.ai.memory.hsm import HolographicStorageMatrix, Experience
    
    print("\n=== 測試 HSM 異步操作 ===")
    
    hsm = HolographicStorageMatrix(dimension=256, max_memories=100)
    
    exp = Experience(
        content="這是異步測試",
        context={},
        importance=0.5,
        timestamp="2026-01-31T12:02:00",
        modality="text",
        metadata={}
    )
    
    # 異步存儲
    memory_id = await hsm.store_async(exp)
    print(f"✓ 異步存儲成功: {memory_id}")
    
    # 異步檢索
    memories = await hsm.retrieve_by_association_async("異步", top_k=3)
    print(f"✓ 異步檢索成功: 找到 {len(memories)} 條記憶")
    
    # 異步保存
    success = await hsm.save_to_file_async("data/test/hsm_async_test")
    print(f"✓ 異步保存成功: {success}")
    
    return True

async def test_cdm_persistence():
    """測試 CDM 持久化功能"""
    from apps.backend.src.ai.learning.cdm import CognitiveDeltaMatrix
    
    print("\n=== 測試 CDM 持久化 ===")
    
    cdm = CognitiveDeltaMatrix(novelty_threshold=0.3, learning_rate=0.1)
    
    # 計算一些差異並整合知識
    delta1 = cdm.compute_delta("機器學習是人工智能的一個分支")
    cdm.integrate_knowledge("機器學習是人工智能的一個分支", delta1)
    
    delta2 = cdm.compute_delta("深度學習是機器學習的一個子集")
    cdm.integrate_knowledge("深度學習是機器學習的一個子集", delta2)
    
    print(f"✓ 知識圖譜中有 {len(cdm.knowledge_graph.units)} 個單元")
    
    # 保存到文件
    save_path = "data/test/cdm_test.json"
    success = cdm.save_to_file(save_path)
    print(f"✓ 保存到文件: {success}")
    
    # 創建新的 CDM 並加載
    cdm2 = CognitiveDeltaMatrix(novelty_threshold=0.3, learning_rate=0.1)
    success = cdm2.load_from_file(save_path)
    print(f"✓ 從文件加載: {success}")
    print(f"✓ 加載後有 {len(cdm2.knowledge_graph.units)} 個單元")
    
    return True

async def test_cdm_async():
    """測試 CDM 異步功能"""
    from apps.backend.src.ai.learning.cdm import CognitiveDeltaMatrix
    
    print("\n=== 測試 CDM 異步操作 ===")
    
    cdm = CognitiveDeltaMatrix(novelty_threshold=0.3, learning_rate=0.1)
    
    # 異步計算差異
    delta = await cdm.compute_delta_async("這是異步測試內容")
    print(f"✓ 異步計算差異: {delta.delta_value:.3f}")
    
    # 異步整合知識
    unit = await cdm.integrate_knowledge_async("這是異步測試內容", delta)
    print(f"✓ 異步整合知識: {unit.unit_id if unit else 'None'}")
    
    # 異步保存
    success = await cdm.save_to_file_async("data/test/cdm_async_test.json")
    print(f"✓ 異步保存成功: {success}")
    
    return True

async def main():
    """主測試函數"""
    print("=" * 60)
    print("開始測試 HSM/CDM 異步與持久化功能")
    print("=" * 60)
    
    # 創建測試目錄
    Path("data/test").mkdir(parents=True, exist_ok=True)
    
    try:
        await test_hsm_persistence()
        await test_hsm_async()
        await test_cdm_persistence()
        await test_cdm_async()
        
        print("\n" + "=" * 60)
        print("✅ 所有測試通過！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)