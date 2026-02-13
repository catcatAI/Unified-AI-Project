"""
Agent Manager Extensions for Phase 15
進程代理管理、健康監控和自動重啟功能
"""

import asyncio
import logging
import multiprocessing as mp
import time
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class AgentManagerExtensions:
    """
    AgentManager 的擴展功能（Phase 15）
    提供進程代理管理、健康監控和自動重啟
    """
    
    @staticmethod
    async def launch_process_agent(agent_manager, agent_type: str, agent_id: str,
                                   agent_entry_point: Callable) -> bool:
        """
        在新進程中啟動代理
        
        Args:
            agent_manager: AgentManager 實例
            agent_type: 代理類型
            agent_id: 代理 ID
            agent_entry_point: 代理入口函數（在新進程中執行）
        
        Returns:
            是否成功啟動
        """
        if not agent_manager.enable_process_agents:
            logger.error("Process agents are disabled")
            return False
        
        try:
            # 創建進程
            process = mp.Process(
                target=agent_entry_point,
                args=(agent_id,),
                name=f"Agent-{agent_id}"
            )
            process.start()

            # 記錄進程信息（包括入口函數）
            from src.ai.agents.agent_manager import ProcessAgentInfo
            agent_manager.process_agents[agent_id] = ProcessAgentInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                process=process,
                start_time=time.time(),
                last_heartbeat=time.time(),
                entry_point=agent_entry_point  # 保存入口函數
            )

            logger.info(f"Launched process agent {agent_id} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch process agent {agent_id}: {e}")
            return False
    
    @staticmethod
    async def start_health_monitoring(agent_manager):
        """啟動健康監控任務"""
        if agent_manager._health_monitor_task:
            logger.warning("Health monitor already running")
            return
        
        agent_manager._health_monitor_task = asyncio.create_task(
            AgentManagerExtensions._health_monitor_loop(agent_manager)
        )
        logger.info("Health monitoring started")
    
    @staticmethod
    async def stop_health_monitoring(agent_manager):
        """停止健康監控任務"""
        if agent_manager._health_monitor_task:
            agent_manager._health_monitor_task.cancel()
            try:
                await agent_manager._health_monitor_task
            except asyncio.CancelledError:
                pass
            agent_manager._health_monitor_task = None
            logger.info("Health monitoring stopped")
    
    @staticmethod
    async def _health_monitor_loop(agent_manager):
        """健康監控循環"""
        logger.info("Health monitor loop started")
        
        while True:
            try:
                await asyncio.sleep(agent_manager.health_check_interval)
                
                # 檢查所有進程代理
                dead_agents = []
                for agent_id, agent_info in agent_manager.process_agents.items():
                    if not agent_info.process.is_alive():
                        logger.warning(f"Agent {agent_id} is dead (PID: {agent_info.process.pid})")
                        dead_agents.append(agent_id)
                
                # 嘗試重啟死亡代理
                for agent_id in dead_agents:
                    await AgentManagerExtensions._attempt_restart(agent_manager, agent_id)
                
            except asyncio.CancelledError:
                logger.info("Health monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
    
    @staticmethod
    async def _attempt_restart(agent_manager, agent_id: str) -> bool:
        """
        嘗試重啟代理
        
        Args:
            agent_manager: AgentManager 實例
            agent_id: 代理 ID
        
        Returns:
            是否成功重啟
        """
        agent_info = agent_manager.process_agents.get(agent_id)
        if not agent_info:
            return False
        
        # 檢查重啟次數
        if agent_info.restart_count >= agent_manager.max_restart_attempts:
            logger.error(f"Agent {agent_id} exceeded max restart attempts ({agent_manager.max_restart_attempts})")
            del agent_manager.process_agents[agent_id]
            return False
        
        logger.info(f"Attempting to restart agent {agent_id} (attempt {agent_info.restart_count + 1})")

        # 使用保存的入口函數重啟代理
        if agent_info.entry_point is None:
            logger.error(f"Cannot restart agent {agent_id}: no entry point saved")
            return False

        try:
            # 創建新進程
            new_process = mp.Process(
                target=agent_info.entry_point,
                args=(agent_id,),
                name=f"Agent-{agent_id}"
            )
            new_process.start()

            # 更新進程信息
            from src.ai.agents.agent_manager import ProcessAgentInfo
            agent_manager.process_agents[agent_id] = ProcessAgentInfo(
                agent_id=agent_id,
                agent_type=agent_info.agent_type,
                process=new_process,
                start_time=time.time(),
                last_heartbeat=time.time(),
                restart_count=agent_info.restart_count + 1,
                entry_point=agent_info.entry_point
            )

            logger.info(f"Successfully restarted agent {agent_id} (new PID: {new_process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to restart agent {agent_id}: {e}")
            return False
    
    @staticmethod
    def get_process_agent_status(agent_manager, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取進程代理狀態
        
        Args:
            agent_manager: AgentManager 實例
            agent_id: 代理 ID
        
        Returns:
            代理狀態字典
        """
        agent_info = agent_manager.process_agents.get(agent_id)
        if not agent_info:
            return None
        
        return {
            "agent_id": agent_id,
            "agent_type": agent_info.agent_type,
            "pid": agent_info.process.pid,
            "is_alive": agent_info.process.is_alive(),
            "uptime": time.time() - agent_info.start_time,
            "restart_count": agent_info.restart_count
        }
    
    @staticmethod
    async def shutdown_all_process_agents(agent_manager):
        """關閉所有進程代理"""
        logger.info(f"Shutting down {len(agent_manager.process_agents)} process agents...")
        
        for agent_id, agent_info in agent_manager.process_agents.items():
            if agent_info.process.is_alive():
                logger.info(f"Terminating agent {agent_id} (PID: {agent_info.process.pid})")
                agent_info.process.terminate()
                agent_info.process.join(timeout=5.0)
                
                if agent_info.process.is_alive():
                    logger.warning(f"Force killing agent {agent_id}")
                    agent_info.process.kill()
        
        agent_manager.process_agents.clear()
        logger.info("All process agents shut down")


# 示例代理入口函數
def example_agent_entry_point(agent_id: str):
    """
    示例代理入口函數（在新進程中運行）
    
    Args:
        agent_id: 代理 ID
    """
    import time
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"[Agent-{agent_id}] Started in process {mp.current_process().pid}")
    
    # 模擬代理工作
    try:
        while True:
            logger.info(f"[Agent-{agent_id}] Working...")
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info(f"[Agent-{agent_id}] Shutting down")


# 測試代碼
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "D:/Projects/Unified-AI-Project/apps/backend/src")
    
    from ai.agents.agent_manager import AgentManager
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_process_agents():
        """測試進程代理管理"""
        print("=== Testing Process Agent Management ===\n")
        
        # 創建 AgentManager
        agent_manager = AgentManager(enable_process_agents=True)
        
        # 啟動健康監控
        await AgentManagerExtensions.start_health_monitoring(agent_manager)
        
        # 啟動測試代理
        await AgentManagerExtensions.launch_process_agent(
            agent_manager,
            agent_type="test_agent",
            agent_id="test_agent_1",
            agent_entry_point=example_agent_entry_point
        )
        
        # 等待一段時間
        await asyncio.sleep(3)
        
        # 檢查狀態
        status = AgentManagerExtensions.get_process_agent_status(agent_manager, "test_agent_1")
        print(f"Agent status: {status}\n")
        
        # 關閉
        await AgentManagerExtensions.shutdown_all_process_agents(agent_manager)
        await AgentManagerExtensions.stop_health_monitoring(agent_manager)
        
        print("=== Test Complete ===")
    
    # 運行測試
    asyncio.run(test_process_agents())
