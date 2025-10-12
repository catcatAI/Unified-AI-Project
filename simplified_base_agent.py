#!/usr/bin/env python3
"""
簡化版BaseAgent - 用於全域性測試
基於真實系統組件，消除複雜依賴
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# 基礎日誌設置
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class SimpleTask:
    """簡化任務定義"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_time: float = 0.0

class SimplifiedBaseAgent:
    """
    簡化版BaseAgent - 用於全域性測試和系統修復
    
    特點:
    - 零複雜依賴
    - 基於真實Python標準庫
    - 支持基本代理功能
    - 可擴展設計
    """
    
    def __init__(self, agent_id: str, capabilities: List[Dict[str, Any]] = None, agent_name: str = "SimplifiedAgent"):
        """初始化簡化代理"""
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.is_running = False
        self.task_queue: List[SimpleTask] = []
        self.max_queue_size = 100
        self._initialized = True
        self._start_time = None
        self._task_counter = 0
        
        # 基本配置
        logging.basicConfig(level=logging.INFO)
        logger.info(f"[{self.agent_id}] 簡化BaseAgent初始化完成")
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """獲取代理能力列表"""
        return self.capabilities.copy()
    
    def add_capability(self, capability: Dict[str, Any]) -> None:
        """添加新能力"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            logger.info(f"[{self.agent_id}] 添加能力: {capability.get('name', 'unknown')}")
    
    def remove_capability(self, capability_id: str) -> bool:
        """移除指定能力"""
        original_count = len(self.capabilities)
        self.capabilities = [cap for cap in self.capabilities if cap.get('id') != capability_id]
        removed = len(self.capabilities) < original_count
        if removed:
            logger.info(f"[{self.agent_id}] 移除能力: {capability_id}")
        return removed
    
    def has_capability(self, capability_name: str) -> bool:
        """檢查是否具備指定能力"""
        return any(cap.get('name') == capability_name for cap in self.capabilities)
    
    async def start(self) -> bool:
        """啟動代理"""
        if self.is_running:
            logger.warning(f"[{self.agent_id}] 代理已在運行中")
            return False
        
        self.is_running = True
        self._start_time = asyncio.get_event_loop().time()
        logger.info(f"[{self.agent_id}] 代理啟動成功")
        return True
    
    async def stop(self) -> bool:
        """停止代理"""
        if not self.is_running:
            logger.warning(f"[{self.agent_id}] 代理未在運行")
            return False
        
        self.is_running = False
        logger.info(f"[{self.agent_id}] 代理停止成功")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """獲取代理狀態"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "is_running": self.is_running,
            "capabilities_count": len(self.capabilities),
            "task_queue_size": len(self.task_queue),
            "initialized": self._initialized,
            "uptime": (asyncio.get_event_loop().time() - self._start_time) if self._start_time else 0.0
        }
    
    async def process_task(self, task: SimpleTask) -> Dict[str, Any]:
        """處理單個任務"""
        if not self.is_running:
            return {"status": "failed", "error": "代理未運行"}
        
        try:
            logger.info(f"[{self.agent_id}] 處理任務: {task.task_id} ({task.task_type})")
            
            # 模擬任務處理
            await asyncio.sleep(0.1)  # 模擬處理時間
            
            result = {
                "status": "success",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "processed_by": self.agent_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info(f"[{self.agent_id}] 任務處理完成: {task.task_id}")
            return result
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] 任務處理失敗: {e}")
            return {"status": "failed", "error": str(e), "task_id": task.task_id}
    
    async def process_multiple_tasks(self, tasks: List[SimpleTask]) -> List[Dict[str, Any]]:
        """同時處理多個任務"""
        if not self.is_running:
            return [{"status": "failed", "error": "代理未運行"} for _ in tasks]
        
        # 使用異步同時處理
        task_coroutines = [self.process_task(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "status": "failed",
                    "error": f"任務異常: {str(result)}",
                    "task_id": tasks[i].task_id if i < len(tasks) else "unknown"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def simulate_capability_execution(self, capability_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """模擬能力執行（用於測試）"""
        if not self.has_capability(capability_name):
            return {
                "status": "failed",
                "error": f"代理不具備能力: {capability_name}",
                "available_capabilities": [cap.get('name') for cap in self.capabilities]
            }
        
        # 模擬能力執行
        result = {
            "status": "simulated_success",
            "capability": capability_name,
            "parameters": parameters or {},
            "result": f"模擬執行 {capability_name} 的結果",
            "agent_id": self.agent_id,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0.0
        }
        
        logger.info(f"[{self.agent_id}] 模擬執行能力: {capability_name}")
        return result

# 創建標準化代理工廠函數
def create_simplified_agent(agent_type: str, agent_id: str = None, **kwargs) -> SimplifiedBaseAgent:
    """工廠函數：創建特定類型的簡化代理"""
    if not agent_id:
        agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
    
    # 根據代理類型設置默認能力
    default_capabilities = {
        "creative": [
            {"id": "creative_writing", "name": "creative_writing", "version": "1.0"},
            {"id": "content_generation", "name": "content_generation", "version": "1.0"}
        ],
        "search": [
            {"id": "web_search", "name": "web_search", "version": "1.0"},
            {"id": "data_retrieval", "name": "data_retrieval", "version": "1.0"}
        ],
        "analysis": [
            {"id": "data_analysis", "name": "data_analysis", "version": "1.0"},
            {"id": "pattern_recognition", "name": "pattern_recognition", "version": "1.0"}
        ],
        "generic": []
    }
    
    capabilities = kwargs.get('capabilities', default_capabilities.get(agent_type, []))
    agent_name = kwargs.get('agent_name', f"Simplified{agent_type.title()}Agent")
    
    return SimplifiedBaseAgent(agent_id, capabilities, agent_name)

# 測試函數
async def test_simplified_agent():
    """測試簡化代理功能"""
    print("🧪 測試簡化BaseAgent...")
    
    # 創建不同類型的代理
    agents = [
        create_simplified_agent("creative", agent_name="CreativeWriter"),
        create_simplified_agent("search", agent_name="WebSearcher"),
        create_simplified_agent("analysis", agent_name="DataAnalyst"),
        create_simplified_agent("generic", agent_name="GenericAgent")
    ]
    
    print(f"創建了 {len(agents)} 個測試代理")
    
    # 同時啟動所有代理
    start_tasks = [agent.start() for agent in agents]
    start_results = await asyncio.gather(*start_tasks)
    
    print(f"代理啟動結果: {sum(start_results)}/{len(agents)} 成功")
    
    # 測試同時任務處理
    test_tasks = []
    for i, agent in enumerate(agents):
        task = SimpleTask(
            task_id=f"test_task_{i}",
            task_type=f"test_type_{i}",
            payload={"test_data": f"data_{i}", "agent": agent.agent_id}
        )
        test_tasks.append(task)
    
    # 每個代理處理自己的任務
    process_tasks = [agents[i].process_task(test_tasks[i]) for i in range(len(agents))]
    process_results = await asyncio.gather(*process_tasks)
    
    success_count = sum(1 for result in process_results if result.get("status") == "success")
    print(f"任務處理結果: {success_count}/{len(agents)} 成功")
    
    # 測試能力模擬
    capability_results = []
    for agent in agents:
        if agent.capabilities:
            cap_name = agent.capabilities[0]["name"]
            result = agent.simulate_capability_execution(cap_name, {"test": True})
            capability_results.append(result)
    
    print(f"能力模擬結果: {len(capability_results)} 個能力測試完成")
    
    # 停止所有代理
    stop_tasks = [agent.stop() for agent in agents]
    stop_results = await asyncio.gather(*stop_tasks)
    
    print(f"代理停止結果: {sum(stop_results)}/{len(agents)} 成功")
    
    # 顯示最終狀態
    print("\n📊 代理最終狀態:")
    for agent in agents:
        status = agent.get_status()
        print(f"  {agent.agent_name}: {status['is_running']} (運行時間: {status.get('uptime', 0):.2f}s)")
    
    return len(agents), success_count

if __name__ == "__main__":
    print("🚀 簡化BaseAgent測試")
    print("=" * 60)
    
    try:
        total_agents, successful_tasks = asyncio.run(test_simplified_agent())
        
        print("\n" + "=" * 60)
        if successful_tasks == total_agents:
            print("🎉 簡化BaseAgent測試完全通過")
            print("✅ 多代理同時調用功能正常")
            exit_code = 0
        else:
            print(f"⚠️ 簡化BaseAgent測試部分通過: {successful_tasks}/{total_agents}")
            exit_code = 1
            
    except Exception as e:
        print(f"❌ 簡化BaseAgent測試失敗: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 2
    
    exit(exit_code)