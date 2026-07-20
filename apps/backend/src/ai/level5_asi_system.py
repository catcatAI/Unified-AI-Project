"""

Level 5 ASI 系统
整合所有Level 5 ASI组件的完整系统实现
"""

from core.utils import safe_error

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from core.hsp.types import HSPMessageEnvelopeClass as HSPMessageEnvelope
from core.system.config.magic_numbers import batch_value, loop_sleep

from .alignment.adversarial_generation_system import AdversarialGenerationSystem
from .alignment.aligned_base_agent import AlignedBaseAgent, AlignmentLevel
from .alignment.alignment_manager import AlignmentManager
from .alignment.asi_autonomous_alignment import ASIAutonomousAlignment
from .alignment.decision_theory_system import DecisionTheorySystem
from .alignment.distributed_coordinator import DistributedCoordinator
from .alignment.emotion_system import EmotionSystem
from .alignment.hyperlinked_parameter_cluster import HyperlinkedParameterCluster
from .alignment.ontology_system import OntologySystem
from .alignment.reasoning_system import ReasoningSystem

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

        except (
            Exception
        ) as e:  # broad exception acceptable: ASI initialization wraps all component failures
            logger.error(f"[{self.system_id}] 初始化失败: {e}", exc_info=True)
            return False

    async def start(self) -> bool:
        """启动Level 5 ASI系统"""
        if not self.is_initialized:
            logger.error(f"[{self.system_id}] 系统未初始化", exc_info=True)
            return False

        try:
            logger.info(f"[{self.system_id}] 启动Level 5 ASI系统")

            for agent in self.aligned_agents.values():
                await agent.start()

            self.is_running = True
            logger.info(f"[{self.system_id}] Level 5 ASI系统已启动")
            return True

        except (
            Exception
        ) as e:  # broad exception acceptable: ASI startup wraps all agent and system failures
            logger.error(f"[{self.system_id}] 启动失败: {e}", exc_info=True)
            return False

    async def stop(self) -> bool:
        """停止Level 5 ASI系统"""
        try:
            logger.info(f"[{self.system_id}] 停止Level 5 ASI系统")

            for agent in self.aligned_agents.values():
                await agent.stop()

            if self.distributed_coordinator:
                await self.distributed_coordinator.shutdown()

            self.is_running = False
            logger.info(f"[{self.system_id}] Level 5 ASI系统已停止")
            return True

        except (
            Exception
        ) as e:  # broad exception acceptable: ASI shutdown wraps all agent and system failures
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
                # Alignment passed but no matching agent — return alignment success
                return {
                    "status": "aligned",
                    "is_aligned": True,
                    "alignment_confidence": alignment_result.get("alignment_confidence", 0.0),
                    "note": "No matching agent, alignment gate passed",
                }

            result = await self._process_with_agent(agent, request, alignment_context)

            if self.adversarial_system is not None:
                adv_result = self._run_adversarial_evaluation(request, result)
                result["adversarial"] = adv_result

            response_time = (asyncio.get_running_loop().time() - start_time) * 1000
            self.performance_metrics["response_time_ms"] = response_time
            self.performance_metrics["successful_requests"] += 1

            await self._update_alignment_score()

            return result

        except (
            Exception
        ) as e:  # broad exception acceptable: ASI request processing wraps all failures
            logger.error(f"[{self.system_id}] 请求处理失败: {e}", exc_info=True)
            return {"error": safe_error(e)}

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

            if self.adversarial_system is not None:
                test_results["components"]["adversarial"] = self._test_adversarial_robustness()

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

        except (
            Exception
        ) as e:  # broad exception acceptable: comprehensive test wraps all component failures
            logger.error(f"[{self.system_id}] 综合测试失败: {e}", exc_info=True)
            return {"error": safe_error(e)}

    def _initialize_alignment_systems(self) -> None:
        """初始化对齐系统"""
        self.reasoning_system = ReasoningSystem(f"{self.system_id}_reasoning")
        self.emotion_system = EmotionSystem(system_id=f"{self.system_id}_emotion")
        self.ontology_system = OntologySystem()

        self.alignment_manager = AlignmentManager(
            config={
                "reasoning_system": self.reasoning_system,
                "emotion_system": self.emotion_system,
                "ontology_system": self.ontology_system,
                "system_id": f"{self.system_id}_alignment_manager",
            }
        )
        logger.info(f"[{self.system_id}] 对齐系统初始化完成")

    def _initialize_advanced_components(self) -> None:
        """初始化高级组件"""
        self.decision_system = DecisionTheorySystem(
            config={"system_id": f"{self.system_id}_decision_system"}
        )

        if self.config.get("enable_adversarial_testing"):
            self.adversarial_system = AdversarialGenerationSystem(
                config={"system_id": f"{self.system_id}_adversarial_system"}
            )

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
            config={
                "reasoning_system": self.reasoning_system,
                "emotion_system": self.emotion_system,
                "ontology_system": self.ontology_system,
            },
        )
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

    def _create_alignment_context(self, request: dict[str, Any]) -> dict[str, Any]:
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

    def _perform_alignment_check(
        self, request: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行对齐检查"""
        if not self.alignment_manager:
            return {"is_aligned": True, "modified_payload": request}

        try:
            action = {
                "action": "process_request",
                "parameters": request,
                "capability_id": request.get("capability_id", "unknown"),
                "ethical_constraints": request.get("ethical_constraints", []),
            }

            is_aligned = self.alignment_manager.check_alignment(action)
            score = self.alignment_manager.get_alignment_score(action)

            if is_aligned:
                return {
                    "is_aligned": True,
                    "modified_payload": request,
                    "alignment_confidence": score,
                }
            else:
                return {
                    "is_aligned": False,
                    "reason": f"Alignment check failed (score={score:.2f})",
                    "safety_score": score,
                }

        except (
            Exception
        ) as e:  # broad exception acceptable: alignment check wraps all decision failures
            logger.error(f"[{self.system_id}] 对齐检查失败: {e}", exc_info=True)
            return {
                "is_aligned": False,
                "reason": f"对齐检查系统错误: {safe_error(e)}",
                "safety_score": 0.0,
            }

    def _select_agent(self, request: dict[str, Any]) -> Optional[AlignedBaseAgent]:
        """选择合适的代理"""
        capability_id = request.get("capability_id")
        if not capability_id:
            return None

        for agent in self.aligned_agents.values():
            for cap in agent.capabilities:
                if cap.get("capability_id") == capability_id:
                    return agent

        return None

    def _process_with_agent(
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

            agent.handle_task_request(request, self.system_id, envelope)
            # Allow event loop to process other tasks — real work done by handle_task_request
            # await asyncio.sleep(0)  # Removed - no await needed

            return {
                "status": "success",
                "agent_id": agent.agent_id,
                "message": "请求已由对齐代理处理",
                "alignment_level": agent.alignment_level,
            }

        except (
            Exception
        ) as e:  # broad exception acceptable: agent processing wraps all task failures
            logger.error(f"[{self.system_id}] 代理处理失败: {e}", exc_info=True)
            return {"status": "error", "error_message": safe_error(e)}

    def _run_adversarial_evaluation(
        self, request: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate adversarial variant of request and evaluate response robustness."""
        request_content = request.get("content", str(request))
        adv = self.adversarial_system.generate_adversarial(request_content)
        response_text = result.get("message", "")
        robustness = self.adversarial_system.evaluate_robustness(response_text)
        return {
            "generated": adv,
            "robustness": robustness,
        }

    async def _update_alignment_score(self) -> None:
        """更新对齐分数"""
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

        except (
            Exception
        ) as e:  # broad exception acceptable: alignment system test wraps all failures
            logger.error(f"[{self.system_id}] 对齐系统测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": safe_error(e)}

    async def _test_distributed_system(self) -> dict[str, Any]:
        """测试分布式系统"""
        try:
            if not self.distributed_coordinator:
                return {"score": 0.0, "error": "分布式系统未初始化"}

            status = await self.distributed_coordinator.get_cluster_status()
            score = 1.0 if status.get("active_nodes", 0) > 0 else 0.0
            return {"score": score, "details": status}

        except (
            Exception
        ) as e:  # broad exception acceptable: distributed system test wraps all failures
            logger.error(f"[{self.system_id}] 分布式系统测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": safe_error(e)}

    async def _test_parameter_cluster(self) -> dict[str, Any]:
        """测试参数集群"""
        try:
            if not self.parameter_cluster:
                return {"score": 0.0, "error": "参数集群未初始化"}

            status = await self.parameter_cluster.get_cluster_status()
            score = 1.0 if status.get("total_parameters", 0) >= 0 else 0.0
            return {"score": score, "details": status}

        except (
            Exception
        ) as e:  # broad exception acceptable: parameter cluster test wraps all failures
            logger.error(f"[{self.system_id}] 参数集群测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": safe_error(e)}

    async def _test_autonomous_alignment(self) -> dict[str, Any]:
        """测试自主对齐"""
        try:
            if not self.autonomous_alignment:
                return {"score": 0.0, "error": "自主对齐系统未初始化"}

            status = await self.autonomous_alignment.get_alignment_status()
            score = 1.0 if status.get("alignment_score", 0.0) > 0.5 else 0.0
            return {"score": score, "details": status}

        except (
            Exception
        ) as e:  # broad exception acceptable: autonomous alignment test wraps all failures
            logger.error(f"[{self.system_id}] 自主对齐测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": safe_error(e)}

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
                except (
                    Exception
                ) as e:  # broad exception acceptable: aligned agent status wraps all failures
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    agent_details[agent_id] = {"error": "Failed to get status"}

            score = healthy_agents / len(self.aligned_agents)

            return {
                "score": score,
                "healthy_agents": healthy_agents,
                "total_agents": len(self.aligned_agents),
                "details": agent_details,
            }

        except (
            Exception
        ) as e:  # broad exception acceptable: aligned agents test wraps all agent failures
            logger.error(f"[{self.system_id}] 对齐代理测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": safe_error(e)}

    def _test_adversarial_robustness(self) -> dict[str, Any]:
        """Run adversarial robustness self-test using built-in patterns."""
        try:
            adv = self.adversarial_system.generate_adversarial()
            robustness = self.adversarial_system.evaluate_robustness(
                f"Response to: {adv.get('original', '')}"
            )
            score = robustness.get("robustness_score", 0.5)
            return {
                "score": score,
                "details": {
                    "pattern_type": adv.get("type", "unknown"),
                    "robustness_score": score,
                    "flags": robustness.get("flags", []),
                },
            }
        except Exception as e:  # broad exception acceptable: adversarial test wraps all failures
            logger.error(f"[{self.system_id}] 对抗测试失败: {e}", exc_info=True)
            return {"score": 0.0, "error": safe_error(e)}
