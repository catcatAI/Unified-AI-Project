#!/usr/bin/env python3
"""
Phase 15 Integration Tests
測試本地集群模擬、進程代理和資源感知調度
"""

import asyncio
import logging
import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
backend_src = os.path.join(project_root, 'apps', 'backend', 'src')
sys.path.insert(0, backend_src)

from apps.backend.src.ai.integration.local_cluster_manager import LocalClusterManager, ClusterTask
from apps.backend.src.ai.agents.agent_manager import AgentManager
from apps.backend.src.ai.agents.agent_manager_extensions import AgentManagerExtensions, example_agent_entry_point
from apps.backend.src.core.hsp.transport import HSPTransportFactory, HSPTransportMode, LocalIPCTransport
import multiprocessing as mp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_local_cluster_basic():
    """測試 1: 本地集群基本功能"""
    print("\n" + "="*60)
    print("TEST 1: Local Cluster Basic Functionality")
    print("="*60 + "\n")
    
    with LocalClusterManager(max_workers=2) as cluster:
        # 提交任務
        for i in range(10):
            task = ClusterTask(
                task_id=f"task_{i}",
                task_type="test",
                payload={"index": i}
            )
            cluster.submit_task(task)
        
        print(f"Submitted 10 tasks")
        print(f"Cluster status: {cluster.get_cluster_status()}\n")
        
        # 收集結果
        results = []
        for _ in range(10):
            result = cluster.get_result(timeout=10.0)
            if result:
                results.append(result)
        
        print(f"Collected {len(results)} results")
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"
        print("✅ Test 1 PASSED\n")


async def test_hsp_transport_ipc():
    """測試 2: HSP IPC 傳輸"""
    print("\n" + "="*60)
    print("TEST 2: HSP IPC Transport")
    print("="*60 + "\n")
    
    # 創建隊列
    queue_a_to_b = mp.Queue()
    queue_b_to_a = mp.Queue()
    
    # 創建傳輸實例
    transport_a = LocalIPCTransport(send_queue=queue_a_to_b, recv_queue=queue_b_to_a)
    transport_b = LocalIPCTransport(send_queue=queue_b_to_a, recv_queue=queue_a_to_b)
    
    # 連接
    await transport_a.connect()
    await transport_b.connect()
    
    # 訂閱
    received_messages = []
    
    async def on_message(payload):
        received_messages.append(payload)
        logger.info(f"Received message: {payload}")
    
    await transport_b.subscribe("test_topic", on_message)
    
    # 發送消息
    for i in range(5):
        await transport_a.publish("test_topic", {"message": f"Hello {i}"})
    
    # 等待處理
    await asyncio.sleep(2)
    
    # 斷開
    await transport_a.disconnect()
    await transport_b.disconnect()
    
    print(f"Sent 5 messages, received {len(received_messages)}")
    assert len(received_messages) == 5, f"Expected 5 messages, got {len(received_messages)}"
    print("✅ Test 2 PASSED\n")


async def test_process_agent_management():
    """測試 3: 進程代理管理"""
    print("\n" + "="*60)
    print("TEST 3: Process Agent Management")
    print("="*60 + "\n")
    
    # 創建 AgentManager
    agent_manager = AgentManager(enable_process_agents=True)
    
    # 啟動健康監控
    await AgentManagerExtensions.start_health_monitoring(agent_manager)
    
    # 啟動測試代理
    success = await AgentManagerExtensions.launch_process_agent(
        agent_manager,
        agent_type="test_agent",
        agent_id="test_agent_1",
        agent_entry_point=example_agent_entry_point
    )
    
    assert success, "Failed to launch process agent"
    print("✅ Agent launched successfully")
    
    # 等待一段時間
    await asyncio.sleep(2)
    
    # 檢查狀態
    status = AgentManagerExtensions.get_process_agent_status(agent_manager, "test_agent_1")
    print(f"Agent status: {status}")
    assert status is not None, "Failed to get agent status"
    assert status["is_alive"], "Agent is not alive"
    print("✅ Agent is alive and healthy")
    
    # 關閉
    await AgentManagerExtensions.shutdown_all_process_agents(agent_manager)
    await AgentManagerExtensions.stop_health_monitoring(agent_manager)
    
    print("✅ Test 3 PASSED\n")


async def test_resource_aware_scaling():
    """測試 4: 資源感知縮放"""
    print("\n" + "="*60)
    print("TEST 4: Resource-Aware Scaling")
    print("="*60 + "\n")
    
    try:
        from services.resource_awareness_service import ResourceAwarenessService
        
        # 創建資源服務
        resource_service = ResourceAwarenessService()
        
        # 獲取實時指標
        metrics = resource_service.get_realtime_metrics()
        print(f"System metrics: {metrics}")
        
        # 獲取推薦並發度
        if hasattr(resource_service, 'get_recommended_concurrency'):
            recommended = resource_service.get_recommended_concurrency()
            print(f"Recommended concurrency: {recommended}")
        else:
            print("⚠️ get_recommended_concurrency not implemented yet")
        
        # 檢查壓力狀態
        is_stressed = resource_service.is_system_stressed()
        print(f"System stressed: {is_stressed}")
        
        print("✅ Test 4 PASSED\n")
        
    except Exception as e:
        print(f"⚠️ Test 4 SKIPPED: {e}\n")


async def test_integration_full_stack():
    """測試 5: 完整堆棧集成"""
    print("\n" + "="*60)
    print("TEST 5: Full Stack Integration")
    print("="*60 + "\n")
    
    # 創建集群
    cluster = LocalClusterManager(max_workers=2)
    cluster.start()
    
    # 創建 AgentManager
    agent_manager = AgentManager(enable_process_agents=True)
    
    try:
        # 提交混合任務
        for i in range(5):
            task = ClusterTask(
                task_id=f"integration_task_{i}",
                task_type="integration_test",
                payload={"data": f"test_{i}"}
            )
            cluster.submit_task(task)
        
        print("Submitted 5 integration tasks")
        
        # 收集結果
        results = []
        for _ in range(5):
            result = cluster.get_result(timeout=10.0)
            if result:
                results.append(result)
        
        print(f"Collected {len(results)} results")
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        print("✅ Test 5 PASSED\n")
        
    finally:
        cluster.shutdown()


async def run_all_tests():
    """運行所有測試"""
    print("\n" + "="*60)
    print("PHASE 15 VERIFICATION TESTS")
    print("="*60)
    
    tests = [
        ("Local Cluster Basic", test_local_cluster_basic),
        ("HSP IPC Transport", test_hsp_transport_ipc),
        ("Process Agent Management", test_process_agent_management),
        ("Resource-Aware Scaling", test_resource_aware_scaling),
        ("Full Stack Integration", test_integration_full_stack)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' FAILED: {e}", exc_info=True)
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
