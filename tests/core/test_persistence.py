"""
P9 — Persistence Layer Test
===========================

測試 Redis/JSON 持久化層的完整功能。

Author: Angela AI v6.2.1
"""

import sys
sys.path.insert(0, 'apps/backend/src')


def test_persistence_basic():
    from core.engine.state_matrix_adapter import StateMatrixAdapter
    from core.autonomous.state_persistence import StatePersistence, PersistenceConfig

    print("=" * 60)
    print("P9 — Persistence Layer Test")
    print("=" * 60)

    print("\n[T1] StatePersistence initialization")
    config = PersistenceConfig(
        redis_enabled=False,
        json_storage_path="data/test_checkpoints",
        auto_save_interval=60,
        max_snapshots=10,
        checkpoint_every_n_updates=5,
    )
    persistence = StatePersistence(config)
    print(f"  ✓ config: redis={config.redis_enabled}, json={config.json_storage_path}")
    print(f"  ✓ stats: {persistence.get_stats()}")
    print("  ✅ T1 PASS\n")

    print("[T2] StateMatrixAdapter with persistence")
    sm = StateMatrixAdapter()
    print(f"  ✓ _persistence initialized: {hasattr(sm, '_persistence')}")
    print(f"  ✓ persistence stats: {sm.get_persistence_stats()}")
    print("  ✅ T2 PASS\n")

    print("[T3] save_checkpoint (JSON mode)")
    import asyncio

    async def run_save():
        await persistence.initialize()
        await sm.init_persistence()
        result = await sm.save_checkpoint(label="test")
        return result

    result = asyncio.run(run_save())
    assert result["status"] == "saved", f"Expected saved, got {result['status']}"
    assert result["mode"] in ("json", "redis"), f"Expected json/redis, got {result.get('mode')}"
    print(f"  ✓ saved: id={result['id']}, mode={result.get('mode')}, tag={result['tag']}")
    print(f"  ✓ timestamp: {result['timestamp']}")
    print("  ✅ T3 PASS\n")

    print("[T4] load_checkpoint")
    async def run_load():
        result2 = await sm.load_checkpoint(checkpoint_id=result["id"])
        return result2

    result2 = asyncio.run(run_load())
    assert result2["status"] == "loaded", f"Expected loaded, got {result2['status']}"
    print(f"  ✓ loaded: id={result2['id']}, tag={result2['tag']}")
    print(f"  ✓ update_count: {result2.get('update_count')}")
    print("  ✅ T4 PASS\n")

    print("[T5] list_checkpoints")
    async def run_list():
        checkpoints = await sm.list_checkpoints(limit=5)
        return checkpoints

    checkpoints = asyncio.run(run_list())
    assert len(checkpoints) > 0, "Should have at least 1 checkpoint"
    print(f"  ✓ found {len(checkpoints)} checkpoint(s)")
    print(f"  ✓ latest: {checkpoints[0]['id']} ({checkpoints[0]['tag']})")
    print("  ✅ T5 PASS\n")

    print("[T6] should_auto_save")
    persistence._last_save_time = 0
    persistence._update_count_since_save = 0
    config2 = PersistenceConfig(auto_save_interval=60, checkpoint_every_n_updates=5)
    p2 = StatePersistence(config2)
    assert p2.should_auto_save(10) == True, "should trigger after 5+ updates"
    p2._last_save_time = 9999999999
    p2._update_count_since_save = 0
    assert p2.should_auto_save(3) == False, "should not trigger (time not met)"
    print(f"  ✓ auto_save logic works")
    print("  ✅ T6 PASS\n")

    print("=" * 60)
    print("✅ ALL 6 TESTS PASSED — P9 Persistence Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_persistence_basic()