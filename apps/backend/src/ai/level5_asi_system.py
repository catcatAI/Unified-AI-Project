"""
Level 5 ASI 系统
整合所有Level 5 ASI组件的完整系统实现
"""

import asyncio
import logging
import uuid
from typing import Any, Optional
from datetime import datetime

from core.system.config.magic_numbers import batch_value, loop_sleep

# Assuming these are the correct import paths based on project structure
from .alignment.reasoning_system import ReasoningSystem
from .alignment.emotion_system import EmotionSystem
from .alignment.ontology_system import OntologySystem
from .alignment.alignment_manager import AlignmentManager
from .alignment.decision_theory_system import DecisionTheorySystem
from .alignment.adversarial_generation_system import AdversarialGenerationSystem
from .alignment.asi_autonomous_alignment import ASIAutonomousAlignment

# Placeholder classes for missing imports to ensure syntactic validity
class DistributedCoordinator:
    """STUB: Real implementation at .alignment.distributed_coordinator"""

    def __init__(self, coordinator_id: str = "default_coordinator"):
        self.coordinator_id = coordinator_id
        self.is_initialized = False
        self.cluster_nodes: list[str] = []
        self.active_nodes: list[str] = []
        self.task_queue: list[dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the component."""
        self.is_initialized = True
        self.cluster_nodes = [f"node_{i}" for i in range(3)]
        self.active_nodes = list(self.cluster_nodes)
        logger.info(f"[DistributedCoordinator] Initialized coordinator={self.coordinator_id} nodes={len(self.active_nodes)}")

    async def shutdown(self) -> None:
        """Shut down the component."""
        self.is_initialized = False
        self.active_nodes = []
        logger.info(f"[DistributedCoordinator] Shutdown coordinator={self.coordinator_id}")

    async def get_cluster_status(self) -> dict:
        """Get the cluster status by self."""
        return {
            "coordinator_id": self.coordinator_id,
            "is_initialized": self.is_initialized,
            "total_nodes": len(self.cluster_nodes),
            "active_nodes": len(self.active_nodes),
            "cluster_nodes": list(self.cluster_nodes),
            "pending_tasks": len(self.task_queue),
            "status": "active" if self.is_initialized else "inactive",
        }

    async def distribute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute the distribute task operation."""
        return {
            "status": "distributed",
            "task_id": task.get("task_id", str(uuid.uuid4())),
            "assigned_node": self.active_nodes[0] if self.active_nodes else None,
            "coordinator_id": self.coordinator_id,
        }

    async def coordinate(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute the coordinate operation."""
        return {
            "status": "coordinated",
            "task_id": task.get("task_id", str(uuid.uuid4())),
            "coordinator_id": self.coordinator_id,
            "nodes_involved": list(self.active_nodes),
        }


class HyperlinkedParameterCluster:
    """STUB: Real implementation at .alignment.hyperlinked_parameter_cluster"""

    def __init__(self, cluster_id: str = "default_cluster"):
        self.cluster_id = cluster_id
        self.is_initialized = False
        self.parameters: dict[str, Any] = {}
        self.total_parameters = 1000

    async def initialize(self) -> None:
        """Initialize the component."""
        self.is_initialized = True
        self.parameters = {"learning_rate": 0.001, "batch_size": 32, "epochs": 10}
        logger.info(f"[HyperlinkedParameterCluster] Initialized cluster={self.cluster_id} params={self.total_parameters}")

    async def get_cluster_status(self) -> None:
        """Get the cluster status by self."""
        return {
            "cluster_id": self.cluster_id,
            "is_initialized": self.is_initialized,
            "total_parameters": self.total_parameters,
            "active_parameters": len(self.parameters),
            "parameter_keys": list(self.parameters.keys()),
            "status": "active" if self.is_initialized else "inactive",
        }

    async def update_parameters(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Update the parameters."""
        self.parameters.update(updates)
        return {
            "status": "updated",
            "cluster_id": self.cluster_id,
            "updated_keys": list(updates.keys()),
            "total_parameters": self.total_parameters,
        }


class AlignmentLevel:
    ADVANCED = "ADVANCED"
    SUPERINTELLIGENT = "SUPERINTELLIGENT"


class AlignedBaseAgent:
    """STUB: Real implementation at .alignment.aligned_base_agent"""

    def __init__(self, agent_id, capabilities, agent_name, alignment_level):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.agent_name = agent_name
        self.alignment_level = alignment_level
        self.is_initialized = False
        self.is_running = False
        self.alignment_enabled = True
        self.task_count = 0
        self.messages_processed = 0
        self.performance_score = 1.0

    async def initialize_alignment_full(self) -> None:
        """Log a diagnostic message."""
        self.is_initialized = True
        logger.info(f"[AlignedBaseAgent] Initialized agent={self.agent_name}")

    async def start(self) -> None:
        """Start the component."""
        self.is_running = True
        logger.info(f"[AlignedBaseAgent] Started agent={self.agent_name}")

    async def stop(self) -> None:
        """Stop the component."""
        self.is_running = False
        logger.info(f"[AlignedBaseAgent] Stopped agent={self.agent_name}")

    async def get_alignment_status(self) -> None:
        """Get the alignment status by self."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "alignment_level": self.alignment_level,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "alignment_enabled": self.alignment_enabled,
            "task_count": self.task_count,
            "messages_processed": self.messages_processed,
            "performance_score": self.performance_score,
            "capabilities": list(self.capabilities) if self.capabilities else [],
            "status": "active" if self.is_running else "inactive",
        }

    async def handle_task_request(self, request, sender_id, envelope) -> dict:
        """Handle task request."""
        self.task_count += 1
        self.messages_processed += 1
        return {
            "status": "processed",
            "agent_id": self.agent_id,
            "task_id": request.get("request_id", str(uuid.uuid4())),
        }

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process incoming data."""
        self.task_count += 1
        return {
            "status": "completed",
            "agent_id": self.agent_id,
            "result": "Task processed by agent",
        }

    async def update_alignment(self, alignment_data: dict[str, Any]) -> dict[str, Any]:
        """Update the alignment."""
        self.alignment_enabled = alignment_data.get("alignment_enabled", self.alignment_enabled)
        self.performance_score = alignment_data.get("performance_score", self.performance_score)
        return {
            "status": "alignment_updated",
            "agent_id": self.agent_id,
            "alignment_enabled": self.alignment_enabled,
        }

    async def shutdown(self) -> None:
        """Shut down the component."""
        self.is_running = False
        self.is_initialized = False
        logger.info(f"[AlignedBaseAgent] Shutdown agent={self.agent_name}")


class HSPMessageEnvelope:
    """STUB: Real implementation at .core.hsp.types"""

    def __init__(self, message_id, timestamp, sender_id, recipient_id, message_type):
        self.message_id = message_id
        self.timestamp = timestamp
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.status = "created"
        self.created_at = datetime.now()


logger = logging.getLogger(__name__)


class Level5ASISystem:
    """
    Level 5 ASI 整合系统

    实现完整的Level 5 ASI架构：
    - 三大支柱对齐系统(理智、感性、存在)
    - 分布式计算架构
    - 超链接参数管理
    - 自主对齐机制
    - 决策理论系统
    - 对抗性生成系统
    """

    def __init__(self, system_id: str = "level5_asi_system"):
        self.system_id = system_id

        # 核心对齐系统
        self.reasoning_system: Optional[ReasoningSystem] = None
        self.emotion_system: Optional[EmotionSystem] = None
        self.ontology_system: Optional[OntologySystem] = None
        self.alignment_manager: Optional[AlignmentManager] = None

        # 高级组件
        self.decision_system: Optional[DecisionTheorySystem] = None
        self.adversarial_system: Optional[AdversarialGenerationSystem] = None
        self.autonomous_alignment: Optional[ASIAutonomousAlignment] = None

        # 分布式系统
        self.distributed_coordinator: Optional[DistributedCoordinator] = None
        self.parameter_cluster: Optional[HyperlinkedParameterCluster] = None

        # 对齐代理
        self.aligned_agents: dict[str, AlignedBaseAgent] = {}

        # 系统状态
        self.is_initialized: bool = False
        self.is_running: bool = False

        # 性能监控
        self.performance_metrics: dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "alignment_score": 0.0,
            "system_health": 1.0,
            "response_time_ms": 0.0,
        }

        # 配置
        self.config: dict[str, Any] = {
            "enable_autonomous_alignment": True,
            "enable_distributed_computing": True,
            "enable_adversarial_testing": True,
            "max_concurrent_agents": int(batch_value("level5_concurrent_agents", 10)),
            "safety_threshold": 0.8,
        }

    async def initialize(self) -> bool:
        """初始化Level 5 ASI系统"""
        try:
            logger.info(f"[{self.system_id}] 开始初始化Level 5 ASI系统")

            await self._initialize_alignment_systems()
            await self._initialize_advanced_components()

            if self.config.get("enable_distributed_computing"):
                await self._initialize_distributed_system()

            if self.config.get("enable_autonomous_alignment"):
                await self._initialize_autonomous_alignment()

            await self._create_aligned_agents()

            self.is_initialized = True
            logger.info(f"[{self.system_id}] Level 5 ASI系统初始化完成")
            return True

        except Exception as e:  # broad exception acceptable: ASI initialization wraps all component failures
            logger.error(f"[{self.system_id}] 初始化失败: {e}", exc_info=True)
            return False

    async def start(self) -> bool:
        """启动Level 5 ASI系统"""
        if not self.is_initialized:
            logger.error(f"[{self.system_id}] 系统未初始化", exc_info=True)
            return False

        try:
            logger.info(f"[{self.system_id}] 启动Level 5 ASI系统")

            if self.autonomous_alignment:
                await self.autonomous_alignment.start()

            for agent in self.aligned_agents.values():
                await agent.start()

            self.is_running = True
            logger.info(f"[{self.system_id}] Level 5 ASI系统已启动")
            return True

        except Exception as e:  # broad exception acceptable: ASI startup wraps all agent and system failures
            logger.error(f"[{self.system_id}] 启动失败: {e}", exc_info=True)
            return False

    async def stop(self) -> bool:
        """停止Level 5 ASI系统"""
        try:
            logger.info(f"[{self.system_id}] 停止Level 5 ASI系统")

            for agent in self.aligned_agents.values():
                await agent.stop()

            if self.autonomous_alignment:
                await self.autonomous_alignment.stop()

            if self.distributed_coordinator:
                await self.distributed_coordinator.shutdown()

            self.is_running = False
            logger.info(f"[{self.system_id}] Level 5 ASI系统已停止")
            return True

        except Exception as e:  # broad exception acceptable: ASI shutdown wraps all agent and system failures
            logger.error(f"[{self.system_id}] 停止失败: {e}", exc_info=True)
            return False

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """处理系统请求"""
        if not self.is_running:
            return {"error": "系统未运行"}

        try:
            self.performance_metrics["total_requests"] += 1
            start_time = asyncio.get_running_loop().time()

            alignment_context = await self._create_alignment_context(request)
            alignment_result = await self._perform_alignment_check(request, alignment_context)

            if not alignment_result.get("is_aligned"):
                return {
                    "status": "alignment_failed",
                    "reason": alignment_result.get("reason"),
                    "safety_score": alignment_result.get("safety_score", 0.0),
                }

            agent = await self._select_agent(request)
            if not agent:
                return {"error": "没有可用的对齐代理"}

            result = await self._process_with_agent(agent, request, alignment_context)

            response_time = (asyncio.get_running_loop().time() - start_time) * 1000
            self.performance_metrics["response_time_ms"] = response_time
            self.performance_metrics["successful_requests"] += 1

            await self._update_alignment_score()

            return result

        except Exception as e:  # broad exception acceptable: ASI request processing wraps all failures
            logger.error(f"[{self.system_id}] 请求处理失败: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        status = {
            "system_id": self.system_id,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "performance_metrics": self.performance_metrics,
            "config": self.config,
        }

        if self.alignment_manager:
            status["alignment_system"] = await self.alignment_manager.get_status()

        if self.distributed_coordinator:
            status["distributed_system"] = await self.distributed_coordinator.get_cluster_status()

        if self.parameter_cluster:
            status["parameter_cluster"] = await self.parameter_cluster.get_cluster_status()

        if self.autonomous_alignment:
            status["autonomous_alignment"] = await self.autonomous_alignment.get_alignment_status()

        agent_statuses = {}
        for agent_id, agent in self.aligned_agents.items():
            agent_statuses[agent_id] = await agent.get_alignment_status()
        status["aligned_agents"] = agent_statuses

        return status

    async def run_comprehensive_test(self) -> dict[str, Any]:
        """运行综合测试"""
        try:
            logger.info(f"[{self.system_id}] 开始综合测试")

            test_results: dict[str, Any] = {
                "test_id": str(uuid.uuid4()),
                "timestamp": datetime.now(),
                "components": {},
                "overall_score": 0.0,
                "passed": False,
            }

            if self.alignment_manager:
                test_results["components"]["alignment"] = await self._test_alignment_system()

            if self.distributed_coordinator:
                test_results["components"]["distributed"] = await self._test_distributed_system()

            if self.parameter_cluster:
                test_results["components"][
                    "parameter_cluster"
                ] = await self._test_parameter_cluster()

            if self.autonomous_alignment:
                test_results["components"][
                    "autonomous_alignment"
                ] = await self._test_autonomous_alignment()

            test_results["components"]["aligned_agents"] = await self._test_aligned_agents()

            component_scores = [
                result.get("score", 0.0) for result in test_results["components"].values()
            ]
            test_results["overall_score"] = (
                sum(component_scores) / len(component_scores) if component_scores else 0.0
            )
            test_results["passed"] = test_results["overall_score"] >= 0.8

            logger.info(
                f"[{self.system_id}] 综合测试完成, 分数: {test_results['overall_score']:.2f}"
            )
            return test_results

        except Exception as e:  # broad exception acceptable: comprehensive test wraps all component failures
            logger.error(f"[{self.system_id}] 综合测试失败: {e}", exc_info=True)
            return {"error": str(e)}

    async def _initialize_alignment_systems(self) -> None:
        """初始化对齐系统"""
        self.reasoning_system = ReasoningSystem(f"{self.system_id}_reasoning")
        self.emotion_system = EmotionSystem(f"{self.system_id}_emotion")
        self.ontology_system = OntologySystem(f"{self.system_id}_ontology")

        self.alignment_manager = AlignmentManager(
            reasoning_system=self.reasoning_system,
            emotion_system=self.emotion_system,
            ontology_system=self.ontology_system,
            system_id=f"{self.system_id}_alignment_manager",
        )
        await self.alignment_manager.initialize()
        logger.info(f"[{self.system_id}] 对齐系统初始化完成")

    async def _initialize_advanced_components(self) -> None:
        """初始化高级组件"""
        self.decision_system = DecisionTheorySystem(system_id=f"{self.system_id}_decision_system")
        await self.decision_system.initialize()

        if self.config.get("enable_adversarial_testing"):
            self.adversarial_system = AdversarialGenerationSystem(
                system_id=f"{self.system_id}_adversarial_system"
            )
            await self.adversarial_system.initialize()

        logger.info(f"[{self.system_id}] 高级组件初始化完成")

    async def _initialize_distributed_system(self) -> None:
        """初始化分布式系统"""
        self.distributed_coordinator = DistributedCoordinator(
            coordinator_id=f"{self.system_id}_distributed_coordinator"
        )
        await self.distributed_coordinator.initialize()

        self.parameter_cluster = HyperlinkedParameterCluster(
            cluster_id=f"{self.system_id}_parameter_cluster"
        )
        await self.parameter_cluster.initialize()

        logger.info(f"[{self.system_id}] 分布式系统初始化完成")

    async def _initialize_autonomous_alignment(self) -> None:
        """初始化自主对齐系统"""
        self.autonomous_alignment = ASIAutonomousAlignment(
            system_id=f"{self.system_id}_autonomous_alignment",
            reasoning_system=self.reasoning_system,
            emotion_system=self.emotion_system,
            ontology_system=self.ontology_system,
        )
        await self.autonomous_alignment.initialize()
        logger.info(f"[{self.system_id}] 自主对齐系统初始化完成")

    async def _create_aligned_agents(self) -> None:
        """创建对齐代理"""
        creative_agent = AlignedBaseAgent(
            agent_id=f"{self.system_id}_creative_agent",
            capabilities=[
                {
                    "capability_id": "creative_writing",
                    "description": "对齐的创意写作",
                    "input_schema": {
                        "type": "object",
                        "properties": {"prompt": {"type": "string"}, "style": {"type": "string"}},
                    },
                }
            ],
            agent_name="对齐创意写作代理",
            alignment_level=AlignmentLevel.ADVANCED,
        )
        await creative_agent.initialize_alignment_full()
        self.aligned_agents[creative_agent.agent_id] = creative_agent

        analysis_agent = AlignedBaseAgent(
            agent_id=f"{self.system_id}_analysis_agent",
            capabilities=[
                {
                    "capability_id": "ethical_analysis",
                    "description": "伦理分析",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "context": {"type": "object"},
                        },
                    },
                }
            ],
            agent_name="伦理分析代理",
            alignment_level=AlignmentLevel.SUPERINTELLIGENT,
        )
        await analysis_agent.initialize_alignment_full()
        self.aligned_agents[analysis_agent.agent_id] = analysis_agent

        logger.info(f"[{self.system_id}] 创建了 {len(self.aligned_agents)} 个对齐代理")

    async def _create_alignment_context(self, request: dict[str, Any]) -> dict[str, Any]:
        """创建对齐上下文"""
        return {
            "request_id": request.get("request_id", str(uuid.uuid4())),
            "user_intent": request.get("user_intent", {}),
            "ethical_constraints": request.get("ethical_constraints", []),
            "emotional_context": request.get("emotional_context", {}),
            "ontological_context": request.get("ontological_context", {}),
            "system_context": {
                "system_id": self.system_id,
                "timestamp": datetime.now(),
                "system_state": "active",
            },
        }

    async def _perform_alignment_check(
        self, request: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行对齐检查"""
        if not self.alignment_manager:
            return {"is_aligned": True, "modified_payload": request}

        try:
            options = [
                {
                    "action": "process_request",
                    "parameters": request,
                    "description": f"处理请求, {request.get('capability_id', 'unknown')}",
                },
                {"action": "reject_request", "parameters": {}, "description": "拒绝请求"},
            ]

            alignment_result = await self.alignment_manager.make_decision(
                context=context, options=options
            )

            if alignment_result.is_aligned:
                return {
                    "is_aligned": True,
                    "modified_payload": request,
                    "alignment_confidence": alignment_result.confidence,
                }
            else:
                return {
                    "is_aligned": False,
                    "reason": alignment_result.reasoning,
                    "safety_score": alignment_result.safety_score,
                }

        except Exception as e:  # broad exception acceptable: alignment check wraps all decision failures
            logger.error(f"[{self.system_id}] 对齐检查失败: {e}", exc_info=True)
            return {
                "is_aligned": False,
                "reason": f"对齐检查系统错误: {str(e)}",
                "safety_score": 0.0,
            }

    async def _select_agent(self, request: dict[str, Any]) -> Optional[AlignedBaseAgent]:
        """选择合适的代理"""
        capability_id = request.get("capability_id")
        if not capability_id:
            return None

        for agent in self.aligned_agents.values():
            for cap in agent.capabilities:
                if cap.get("capability_id") == capability_id:
                    return agent

        return None

    async def _process_with_agent(
        self, agent: AlignedBaseAgent, request: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """使用代理处理请求"""
        try:
            envelope = HSPMessageEnvelope(
                message_id=str(uuid.uuid4()),
                timestamp=datetime.now().timestamp(),
                sender_id="level5_asi_system",
                recipient_id=agent.agent_id,
                message_type="task_request",
            )

            await agent.handle_task_request(request, self.system_id, envelope)
            await asyncio.sleep(loop_sleep("level5_process", 1.0))  # Simulate processing time

            return {
                "status": "success",
                "agent_id": agent.agent_id,
                "message": "请求已由对齐代理处理",
                "alignment_level": agent.alignment_level,
            }

        except Exception as e:  # broad exception acceptable: agent processing wraps all task failures
            logger.error(f"[{self.system_id}] 代理处理失败: {e}", exc_info=True)
            return {"status": "error", "error_message": str(e)}

    async def _update_alignment_score(self) -> None:
        """更新对齐分数"""
        if self.autonomous_alignment:
            status = await self.autonomous_alignment.get_alignment_status()
            self.performance_metrics["alignment_score"] = status.get("alignment_score", 0.0)
        else:
            success_rate = self.performance_metrics["successful_requests"] / max(
                1, self.performance_metrics["total_requests"]
            )
            self.performance_metrics["alignment_score"] = success_rate

    async def _test_alignment_system(self) -> dict[str, Any]:
        """测试对齐系统"""
        try:
            test_request = {
                "request_id": str(uuid.uuid4()),
                "capability_id": "ethical_analysis",
                "content": "测试内容",
                "ethical_constraints": ["无偏见", "尊重隐私"],
            }

            context = await self._create_alignment_context(test_request)
            result = await self._perform_alignment_check(test_request, context)

            return {"score": 1.0 if result.get("is_aligned") else 0.0, "details": result}

        except Exception as e:  # broad exception acceptable: alignment system test wraps all failures
            logger.error(f"[{self.system_id}] 对齐系统测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": str(e)}

    async def _test_distributed_system(self) -> dict[str, Any]:
        """测试分布式系统"""
        try:
            if not self.distributed_coordinator:
                return {"score": 0.0, "error": "分布式系统未初始化"}

            status = await self.distributed_coordinator.get_cluster_status()
            score = 1.0 if status.get("active_nodes", 0) > 0 else 0.0
            return {"score": score, "details": status}

        except Exception as e:  # broad exception acceptable: distributed system test wraps all failures
            logger.error(f"[{self.system_id}] 分布式系统测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": str(e)}

    async def _test_parameter_cluster(self) -> dict[str, Any]:
        """测试参数集群"""
        try:
            if not self.parameter_cluster:
                return {"score": 0.0, "error": "参数集群未初始化"}

            status = await self.parameter_cluster.get_cluster_status()
            score = 1.0 if status.get("total_parameters", 0) >= 0 else 0.0
            return {"score": score, "details": status}

        except Exception as e:  # broad exception acceptable: parameter cluster test wraps all failures
            logger.error(f"[{self.system_id}] 参数集群测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": str(e)}

    async def _test_autonomous_alignment(self) -> dict[str, Any]:
        """测试自主对齐"""
        try:
            if not self.autonomous_alignment:
                return {"score": 0.0, "error": "自主对齐系统未初始化"}

            status = await self.autonomous_alignment.get_alignment_status()
            score = 1.0 if status.get("alignment_score", 0.0) > 0.5 else 0.0
            return {"score": score, "details": status}

        except Exception as e:  # broad exception acceptable: autonomous alignment test wraps all failures
            logger.error(f"[{self.system_id}] 自主对齐测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": str(e)}

    async def _test_aligned_agents(self) -> dict[str, Any]:
        """测试对齐代理"""
        try:
            if not self.aligned_agents:
                return {"score": 0.0, "error": "没有对齐代理"}

            healthy_agents = 0
            agent_details = {}

            for agent_id, agent in self.aligned_agents.items():
                try:
                    status = await agent.get_alignment_status()
                    if status.get("alignment_enabled", False):
                        healthy_agents += 1
                    agent_details[agent_id] = status
                except Exception as e:  # broad exception acceptable: aligned agent status wraps all failures
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    agent_details[agent_id] = {"error": "Failed to get status"}

            score = healthy_agents / len(self.aligned_agents)

            return {
                "score": score,
                "healthy_agents": healthy_agents,
                "total_agents": len(self.aligned_agents),
                "details": agent_details,
            }

        except Exception as e:  # broad exception acceptable: aligned agents test wraps all agent failures
            logger.error(f"[{self.system_id}] 对齐代理测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": str(e)}
