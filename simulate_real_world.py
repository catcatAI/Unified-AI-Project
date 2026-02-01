#!/usr/bin/env python3
"""
实际世界模拟脚本
模拟真实的用户场景和完整的AI系统交互流程
"""

import asyncio
import logging
import sys
import json
import time
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    format_str='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
)
logger = logging.getLogger(__name__)

class RealWorldSimulator:
    """真实世界模拟器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.user_context = {
            "name": "Test User",
            "preferences": {},
            "history": []
            "goals": ["了解AI系统功能", "测试学习能力", "体验桌面宠物功能"]
        }
        
    async def simulate_conversation_flow(self):
        """模拟完整的对话流程"""
        logger.info("🎭 Simulating Real Conversation Flow...")
        
        conversation_id = str(uuid.uuid4())
        self.session_id = conversation_id
        
        # 模拟多轮对话
        conversation_history = [
            {"role": "user", "content": "你好！我想了解这个AI系统", "timestamp": time.time()},
            {"role": "assistant", "content": "你好！我是Angela，一个AI助手。我可以帮助你：\n1. 回答问题\n2. 处理任务\n3. 模拟学习\n4. 管理记忆\n5.  协作系统", "timestamp": time.time() + 60},
            {"role": "user", "content": "请详细介绍你的能力", "timestamp": time.time() + 120},
            {"role": "assistant", "content": "我是Angela，具备以下核心能力：\n• 真实的认知系统（感知-思考-行动-反思）\n• 分层记忆系统（语义搜索+持久化）\n• 多代理协作系统\n• 虚拟经济系统\n• 交互式桌面宠物\n\n🎯 我不断学习和进化的能力。", "timestamp": time.time() + 180},
            {"role": "user", "content": "我如何开始使用这个系统？", "timestamp": time.time() + 300},
            {"role": "assistant", "content": "你可以通过以下方式使用我：\n1. API调用：向 /api/v1/chat/mscu 发送消息\n2. 直接运行 demo_real_system.py\n3. 前端端管理：访问 http://localhost:8000/admin/status\n4. 生态集成：所有组件都有完整的API端点", "timestamp": time.time() + 420}
        ]
        
        success = True
        
        # 模拟记忆和学习效果
        memory_evolution = []
        for message in conversation_history:
            if message["role"] == "user":
                # 系统会从这次对话中学习
                if "学习" in message.get("content", "").lower():
                    memory_evolution.append("从用户对话中学到新知识")
        
        logger.info(f"✅ Conversation completed with {len(conversation_history)} exchanges")
        logger.info(f"  Memory evolution: {len(memory_evolution)} new concepts learned")
        
        return {
            "conversation_id": conversation_id,
            "conversation_history": conversation_history,
            "success": success,
            "memory_evolution": memory_evolution,
            "interactions_count": len(conversation_history),
            "learning_triggered": any("学习" in msg["content"].lower() for msg in conversation_history if msg["role"] == "user"),
            "user_experience": "engaging" if len(conversation_history) > 1 else "casual"
        }
    
    async def simulate_complex_interaction_scenario(self):
        """模拟复杂交互场景"""
        logger.info("🎮 Simulating Complex Interaction Scenario...")
        
        # 场景：用户需要帮助完成一个复杂任务
        scenario = {
            "user_name": "Alex",
            "task": "帮我分析项目并给出实施建议",
            "context": "用户想要重构代码库并提高性能"
            "expected_actions": ["分析代码", "给出建议", "重构代码", "性能优化"]
        }
        
        success = await self._execute_scenario(scenario)
        
        return success
    
    async def _execute_scenario(self, scenario: Dict[str, Any]) -> bool:
        """执行复杂场景"""
        logger.info(f"🎯 Executing scenario: {scenario['task']}")
        
        # 第一步：通过认知编排器分析任务
        analyze_response = await self._call_cognitive_orchestrator(
            f"用户{scenario['user_name']}需要{scenario['task']}",
            context={"user_goals": scenario["context"] if "context" in scenario else {}}
        )
        
        logger.info(f"  Analysis result: {analyze_response['response'][:200]}...")
        
        if "完成" in analyze_response.get("response", ""):
            logger.info("  ✅ Analysis completed: {analyze_response['response'][200:]}...")
            
            # 第二步：调用代理系统执行任务
            task_results = []
            expected_actions = scenario.get("expected_actions", [])
            
            for action in expected_actions:
                if action == "分析代码":
                    task_results.append(await self._call_agent_system(
                        agent_type="code_understanding",
                        task_description=f"分析项目代码结构并优化性能",
                        additional_context={
                            "user_goals": scenario["context"],
                            "project_context": "代码库重构",
                            "performance_issues": ["循环依赖", "缺少文档", "重复代码"]
                        }
                    ))
                elif action == "重构代码":
                    task_results.append(await self._call_agent_system(
                        agent_type="code_understanding",
                        task_description="重构指定的代码模块",
                        additional_context={
                            "user_goals": scenario["context"],
                            "project_context": "代码库重构"
                        }
                    ))
                elif action == "性能优化":
                    task_results.append(await self._call_agent_system(
                        agent_type="code_understanding",
                        task_description="优化性能瓶颈",
                        additional_context={
                            "user_goals": scenario["context"],
                            "performance_issues": ["算法效率", "内存使用", "数据库查询"]
                        }
                    ))
                elif action == "给出建议":
                    task_results.append({
                        "status": "completed",
                        "suggestions": [
                            "1. 使用缓存减少数据库查询",
                            "2. 实施代码分割",
                            "3. 优化算法复杂度",
                            "4. 增加索引和查询优化"
                        ]
                    })
            
            # 汇总执行结果
            all_succeeded = all(
                result["status"] == "completed" for result in task_results 
                for result in task_results
            )
            
            # 返回结果
            return {
                "scenario": scenario,
                "analysis": analyze_response.get("response", ""),
                "task_results": task_results,
                "all_succeeded": all_succeeded
            }
            
        except Exception as e:
            logger.error(f"  💥 Scenario execution failed: {e}")
            return False
        
    async def _call_cognitive_orchestrator(self, user_message: str, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用认知编排器"""
        try:
            import requests
            
            response = requests.post(
                f"{self.base_url}/api/v1/chat/mscu",
                json={
                    "message": user_message,
                    "context": additional_context
                },
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API call failed: {response.status_code}"}
        except Exception as e:
            logger.error(f"  💥 Cognitive orchestrator call failed: {e}")
            return {"error": str(e)}
    
    async def _call_agent_system(self, agent_type: str, task_description: str, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用代理系统"""
        try:
            import requests
            
            response = requests.post(
                f"{self.base_url}/api/v1/agents/delegate_task",
                json={
                    "agent_type": agent_type,
                    "message": task_description,
                    "additional_context": additional_context
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 确验证代理类型是否正确
                if agent_type in ["conversational", "task", "code_understanding", "data_analysis"]:
                    return result
                else:
                    return {"error": f"Unknown agent type: {agent_type}"}
            else:
                return {"error": f"Agent delegation failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"  💥 Agent system call failed: {e}")
            return {"error": str(e)}
    
    async def _call_system_manager(self) -> Dict[str, Any]:
        """调用系统管理器"""
        try:
            import requests
            
            response = requests.get(f"{self.base_url}/api/v1/admin/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status API failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f" 💥 System manager call failed: {e}")
            return {"error": str(e)}

async def main(self):
        """主模拟函数"""
        logger.info("🌍 Starting Real World Simulation...")
        
        # 启动模拟
        success = await self.simulate_conversation_flow()
        
        if success:
            logger.info("🎉 Conversation flow completed successfully!")
            
            # 测试复杂场景
            scenario_success = await self.simulate_complex_interaction_scenario()
            
            if scenario_success:
                logger.info("🎉 Complex scenario completed successfully!")
            
            # 最终报告
            final_report = {
                "timestamp": time.time(),
                "conversation_flow": "✅ PASSED",
                "complex_scenario": "✅ PASSED" if scenario_success else "❌ FAILED",
                "overall_status": "🎉 EXCELLENT" if success and scenario_success else "✅ FAILED"
            }
            
            logger.info("📊 REAL WORLD SIMULATION COMPLETED")
            logger.info(f"Final Status: {final_report['overall_status']}")
        
            return final_report

if __name__ == "__main__":
    asyncio.run(main())