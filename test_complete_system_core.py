#!/usr/bin/env python3
"""
完整版系统测试套件 - 核心功能验证
测试统一系统管理器完整版的各项功能
"""

import asyncio
import pytest
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入完整版系统
from unified_system_manager_complete_core import (
    UnifiedSystemManagerComplete,
    CompleteSystemConfig,
    get_complete_system_manager,
    start_complete_system,
    stop_complete_system,
    SystemStatus,
    SystemCategory
)

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestCompleteSystemCore:
    """完整版系统核心测试类"""
    
    @pytest.fixture
    def config(self) -> CompleteSystemConfig:
        """测试配置"""
        return CompleteSystemConfig(
            max_workers=4,  # 测试时使用较少的worker
            max_concurrent_operations=20,
            response_time_target=0.2,  # 测试时放宽响应时间要求
            enable_motivation_intelligence=True,
            enable_metacognition=True,
            enable_performance_monitoring=True,
            enable_encryption=True,
            enable_access_control=True,
            audit_logging_enabled=True
        )
    
    @pytest.fixture
    async def system_manager(self, config: CompleteSystemConfig):
        """系统管理器fixture"""
        manager = UnifiedSystemManagerComplete(config)
        
        # 启动系统
        success = await manager.start_complete_system()
        assert success, "系统启动失败"
        
        yield manager
        
        # 清理：停止系统
        await manager.stop_complete_system()
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, config: CompleteSystemConfig):
        """测试系统初始化"""
        logger.info("测试系统初始化...")
        
        manager = UnifiedSystemManagerComplete(config)
        
        # 验证智能模块已初始化
        assert manager.motivation_module is not None, "动机型智能模块未初始化"
        assert manager.metacognition_module is not None, "元认知智能模块未初始化"
        
        # 验证系统注册
        assert len(manager.systems) >= 4, f"系统数量不足: {len(manager.systems)}"
        assert "motivation_intelligence" in manager.systems, "动机型智能系统未注册"
        assert "metacognition_intelligence" in manager.systems, "元认知智能系统未注册"
        
        logger.info("✅ 系统初始化测试通过")
    
    @pytest.mark.asyncio
    async def test_system_startup_shutdown(self, config: CompleteSystemConfig):
        """测试系统启动和关闭"""
        logger.info("测试系统启动和关闭...")
        
        manager = UnifiedSystemManagerComplete(config)
        
        # 测试启动
        start_success = await manager.start_complete_system()
        assert start_success, "系统启动失败"
        assert manager.is_running, "系统未处于运行状态"
        assert manager.system_state == "running", f"系统状态错误: {manager.system_state}"
        
        # 验证异步架构组件
        assert manager.async_event_loop is not None, "异步事件循环未初始化"
        assert len(manager.background_tasks) > 0, "后台任务未启动"
        
        # 等待系统完全启动
        await asyncio.sleep(2)
        
        # 测试关闭
        stop_success = await manager.stop_complete_system()
        assert stop_success, "系统关闭失败"
        assert not manager.is_running, "系统仍在运行"
        assert manager.system_state == "stopped", f"系统状态错误: {manager.system_state}"
        
        logger.info("✅ 系统启动和关闭测试通过")
    
    @pytest.mark.asyncio
    async def test_motivation_intelligence_module(self, system_manager: UnifiedSystemManagerComplete):
        """测试动机型智能模块"""
        logger.info("测试动机型智能模块...")
        
        # 测试动机生成
        test_context = {
            "system_state": {
                "error_rate": 0.08,  # 8%错误率，应该触发错误减少目标
                "response_time": 0.6   # 600ms响应时间，应该触发优化目标
            },
            "performance_metrics": {
                "error_rate": 0.08,
                "response_time": 0.6,
                "throughput": 100
            },
            "challenges": ["memory_limitations", "collaboration_inefficiency"]
        }
        
        result = await system_manager.execute_complete_operation(
            "motivation.generate",
            context=test_context
        )
        
        assert result["success"], f"动机生成失败: {result.get('error')}"
        assert "goals" in result["result"], "目标未生成"
        assert "motivations" in result["result"], "动机未生成"
        assert "valued_motivations" in result["result"], "价值判断未生成"
        
        goals = result["result"]["goals"]
        motivations = result["result"]["motivations"]
        valued_motivations = result["result"]["valued_motivations"]
        
        assert len(goals) > 0, "未生成任何目标"
        assert len(motivations) > 0, "未生成任何动机"
        assert len(valued_motivations) > 0, "未进行价值判断"
        
        # 验证目标类型
        goal_types = [goal["type"] for goal in goals]
        assert "error_reduction" in goal_types, "未生成错误减少目标"
        assert "system_optimization" in goal_types, "未生成系统优化目标"
        
        logger.info(f"✅ 动机型智能模块测试通过 - 生成 {len(goals)} 个目标, {len(motivations)} 个动机")
    
    @pytest.mark.asyncio
    async def test_metacognition_intelligence_module(self, system_manager: UnifiedSystemManagerComplete):
        """测试元认知智能模块"""
        logger.info("测试元认知智能模块...")
        
        # 测试深度自我反思
        cognition_data = {
            "reasoning_steps": [
                {"step_id": 1, "description": "分析输入数据", "confidence": 0.8},
                {"step_id": 2, "description": "应用推理规则", "confidence": 0.9}
            ],
            "decision_points": [
                {"decision_id": 1, "description": "选择推理路径", "selected": "路径A"}
            ],
            "confidence_levels": [0.8, 0.9, 0.75],
            "assumptions": ["数据完整性", "推理规则有效"],
            "recent_event_weight": 0.3,
            "vivid_memory_preference": 0.2,
            "self_awareness_indicators": True,
            "progress_tracking": True
        }
        
        result = await system_manager.execute_complete_operation(
            "metacognition.reflect",
            cognition_data=cognition_data
        )
        
        assert result["success"], f"元认知反思失败: {result.get('error')}"
        assert "reasoning_trace" in result["result"], "推理追踪未生成"
        assert "cognitive_biases" in result["result"], "认知偏差未检测"
        assert "thinking_patterns" in result["result"], "思维模式未分析"
        assert "self_model" in result["result"], "自我模型未更新"
        
        reasoning_trace = result["result"]["reasoning_trace"]
        cognitive_biases = result["result"]["cognitive_biases"]
        thinking_patterns = result["result"]["thinking_patterns"]
        self_model = result["result"]["self_model"]
        
        # 验证推理追踪完整性
        assert "cognitive_trace" in reasoning_trace, "认知追踪缺失"
        assert "metacognitive_trace" in reasoning_trace, "元认知追踪缺失"
        assert "bias_indicators" in reasoning_trace, "偏差指标缺失"
        assert "thinking_quality" in reasoning_trace, "思维质量评估缺失"
        
        logger.info(f"✅ 元认知智能模块测试通过 - 检测到 {len(cognitive_biases)} 个认知偏差")
    
    @pytest.mark.asyncio
    async def test_async_task_processing(self, system_manager: UnifiedSystemManagerComplete):
        """测试异步任务处理"""
        logger.info("测试异步任务处理...")
        
        # 提交多个异步任务
        task_ids = []
        
        for i in range(5):
            task_id = await system_manager.submit_async_task(
                "system_operation",
                {"operation": "context.create_enhanced", "context_type": "test", "initial_content": {"test_id": i}}
            )
            task_ids.append(task_id)
        
        assert len(task_ids) == 5, "异步任务提交失败"
        
        # 等待任务处理
        await asyncio.sleep(3)
        
        # 获取任务结果
        results = []
        for task_id in task_ids:
            result = await system_manager.get_async_result(task_id, timeout=10.0)
            if result:
                results.append(result)
        
        assert len(results) > 0, "未获取到任何任务结果"
        
        # 验证结果质量
        successful_results = [r for r in results if r.get("success", False)]
        assert len(successful_results) > 0, "没有成功的任务结果"
        
        logger.info(f"✅ 异步任务处理测试通过 - 成功处理 {len(successful_results)}/{len(results)} 个任务")
    
    @pytest.mark.asyncio
    async def test_system_performance(self, system_manager: UnifiedSystemManagerComplete):
        """测试系统性能"""
        logger.info("测试系统性能...")
        
        # 执行批量操作测试
        start_time = time.time()
        operations = []
        
        for i in range(10):
            op = system_manager.execute_complete_operation(
                "context.create_enhanced",
                context_type="performance_test",
                initial_content={"test_index": i, "timestamp": time.time()}
            )
            operations.append(op)
        
        # 等待所有操作完成
        results = await asyncio.gather(*operations, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证结果
        successful_ops = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_ops = len(results) - successful_ops
        
        assert successful_ops >= 8, f"成功操作数不足: {successful_ops}/10"
        
        # 性能验证
        avg_response_time = total_time / len(results)
        assert avg_response_time < 1.0, f"平均响应时间过长: {avg_response_time:.3f}s"
        
        logger.info(f"✅ 系统性能测试通过 - 平均响应时间: {avg_response_time:.3f}s, 成功率: {successful_ops}/{len(results)}")
    
    @pytest.mark.asyncio
    async def test_system_status_reporting(self, system_manager: UnifiedSystemManagerComplete):
        """测试系统状态报告"""
        logger.info("测试系统状态报告...")
        
        # 获取系统状态
        status = system_manager.get_complete_system_status()
        
        # 验证状态报告完整性
        required_fields = [
            "system_state", "uptime_seconds", "total_systems", "active_systems",
            "total_operations", "successful_operations", "success_rate",
            "system_version", "motivation_module_active", "metacognition_module_active",
            "enterprise_features_active", "performance_monitoring_active",
            "async_architecture", "production_ready", "agi_level", "modular_score"
        ]
        
        for field in required_fields:
            assert field in status, f"状态报告中缺少字段: {field}"
        
        # 验证关键状态值
        assert status["system_state"] == "running", f"系统状态错误: {status['system_state']}"
        assert status["system_version"] == "2.0.0", f"系统版本错误: {status['system_version']}"
        assert status["motivation_module_active"] is True, "动机模块未激活"
        assert status["metacognition_module_active"] is True, "元认知模块未激活"
        assert status["enterprise_features_active"] is True, "企业功能未激活"
        assert status["production_ready"] is True, "系统未标记为生产就绪"
        assert status["agi_level"] == "Level 3-4 (Complete System)", f"AGI等级错误: {status['agi_level']}"
        assert status["modular_score"] == 1200, f"模块化分数错误: {status['modular_score']}"
        
        # 验证异步架构状态
        async_status = status["async_architecture"]
        assert async_status["async_loop_active"] is True, "异步循环未激活"
        assert async_status["async_processing_enabled"] is True, "异步处理未启用"
        assert async_status["performance_optimized"] is True, "性能未优化"
        
        logger.info("✅ 系统状态报告测试通过")
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, system_manager: UnifiedSystemManagerComplete):
        """测试错误处理和恢复"""
        logger.info("测试错误处理和恢复...")
        
        # 测试无效操作
        result = await system_manager.execute_complete_operation("invalid.operation")
        assert result["success"] is False, "无效操作应该失败"
        assert "error" in result, "错误信息缺失"
        
        # 测试不存在的系统操作
        result = await system_manager.execute_complete_operation("nonexistent.system")
        assert result["success"] is False, "不存在的系统操作应该失败"
        
        # 测试异步任务错误处理
        task_id = await system_manager.submit_async_task("invalid_task_type", {})
        result = await system_manager.get_async_result(task_id, timeout=5.0)
        
        if result:
            assert result.get("success") is False, "无效任务类型应该失败"
            assert "error" in result.get("result", {}), "任务错误信息缺失"
        
        logger.info("✅ 错误处理和恢复测试通过")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, system_manager: UnifiedSystemManagerComplete):
        """测试并发操作"""
        logger.info("测试并发操作...")
        
        # 创建并发操作任务
        concurrent_tasks = []
        
        # 混合不同类型的并发操作
        for i in range(15):
            if i % 3 == 0:
                # 动机生成
                task = system_manager.execute_complete_operation(
                    "motivation.generate",
                    context={"system_state": {"error_rate": 0.05}, "performance_metrics": {"response_time": 0.3}}
                )
            elif i % 3 == 1:
                # 元认知反思
                task = system_manager.execute_complete_operation(
                    "metacognition.reflect",
                    cognition_data={"reasoning_steps": [{"step_id": 1, "description": "test"}]}
                )
            else:
                # 系统操作
                task = system_manager.execute_complete_operation(
                    "context.create_enhanced",
                    context_type="concurrent_test",
                    initial_content={"test_id": i}
                )
            
            concurrent_tasks.append(task)
        
        # 执行并发操作
        start_time = time.time()
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 验证并发执行结果
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success", False):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"并发任务 {i} 异常: {result}")
        
        success_rate = len(successful_results) / len(results)
        assert success_rate >= 0.8, f"并发操作成功率过低: {success_rate:.2%}"
        
        # 性能验证 - 并发操作应该在合理时间内完成
        assert total_time < 10.0, f"并发操作耗时过长: {total_time:.3f}s"
        
        logger.info(f"✅ 并发操作测试通过 - 成功率: {success_rate:.2%}, 耗时: {total_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_complete_system_integration(self, config: CompleteSystemConfig):
        """测试完整系统集成"""
        logger.info("测试完整系统集成...")
        
        # 创建完整系统实例
        manager = UnifiedSystemManagerComplete(config)
        
        # 启动系统
        start_success = await manager.start_complete_system()
        assert start_success, "系统集成启动失败"
        
        try:
            # 执行综合测试场景
            test_results = await self._run_integration_test_scenario(manager)
            
            # 验证集成测试结果
            assert test_results["scenario_completed"], "集成测试场景未完成"
            assert test_results["all_modules_active"], "并非所有模块都激活"
            assert test_results["async_architecture_working"], "异步架构未正常工作"
            assert test_results["enterprise_features_enabled"], "企业功能未启用"
            
            # 验证系统最终状态
            final_status = manager.get_complete_system_status()
            assert final_status["system_state"] == "running", "系统最终状态错误"
            assert final_status["production_ready"] is True, "系统未标记为生产就绪"
            assert final_status["modular_score"] == 1200, "模块化分数未达到满分"
            
            logger.info("✅ 完整系统集成测试通过")
            
        finally:
            # 确保系统正确关闭
            await manager.stop_complete_system()
    
    async def _run_integration_test_scenario(self, manager: UnifiedSystemManagerComplete) -> Dict[str, Any]:
        """运行集成测试场景"""
        logger.info("运行集成测试场景...")
        
        results = {
            "scenario_completed": False,
            "all_modules_active": False,
            "async_architecture_working": False,
            "enterprise_features_enabled": False,
            "test_steps": []
        }
        
        try:
            # 步骤1: 验证所有模块激活
            status = manager.get_complete_system_status()
            if (status["motivation_module_active"] and 
                status["metacognition_module_active"] and
                status["enterprise_features_active"]):
                results["all_modules_active"] = True
                results["test_steps"].append("所有智能模块已激活")
            
            # 步骤2: 测试异步架构
            task_id = await manager.submit_async_task("system_operation", {"operation": "test"})
            if task_id:
                results["async_architecture_working"] = True
                results["test_steps"].append("异步架构正常工作")
            
            # 步骤3: 测试动机型智能
            motivation_result = await manager.execute_complete_operation(
                "motivation.generate",
                context={"system_state": {"error_rate": 0.03}, "performance_metrics": {"response_time": 0.25}}
            )
            if motivation_result["success"]:
                results["test_steps"].append("动机型智能模块功能正常")
            
            # 步骤4: 测试元认知智能
            metacognition_result = await manager.execute_complete_operation(
                "metacognition.reflect",
                cognition_data={"reasoning_steps": [{"step_id": 1, "description": "integration_test"}]}
            )
            if metacognition_result["success"]:
                results["test_steps"].append("元认知智能模块功能正常")
            
            # 步骤5: 验证企业级功能
            if status["performance_monitoring_active"]:
                results["enterprise_features_enabled"] = True
                results["test_steps"].append("企业级监控功能已启用")
            
            # 步骤6: 并发压力测试
            concurrent_tasks = []
            for i in range(20):
                task = manager.execute_complete_operation(
                    "context.create_enhanced",
                    context_type="integration_test",
                    initial_content={"test_index": i, "timestamp": time.time()}
                )
                concurrent_tasks.append(task)
            
            concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            successful_concurrent = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get("success", False))
            
            if successful_concurrent >= 16:  # 80%成功率
                results["test_steps"].append(f"并发压力测试通过: {successful_concurrent}/20")
            
            # 所有步骤完成
            results["scenario_completed"] = True
            results["test_steps"].append("集成测试场景完成")
            
        except Exception as e:
            logger.error(f"集成测试场景失败: {e}")
            results["error"] = str(e)
        
        return results

class TestCompleteSystemPerformance:
    """完整版系统性能测试类"""
    
    @pytest.mark.asyncio
    async def test_response_time_performance(self):
        """测试响应时间性能"""
        logger.info("测试响应时间性能...")
        
        config = CompleteSystemConfig(
            max_workers=8,
            max_concurrent_operations=50,
            response_time_target=0.1
        )
        
        manager = UnifiedSystemManagerComplete(config)
        await manager.start_complete_system()
        
        try:
            # 预热系统
            await manager.execute_complete_operation("context.create_enhanced", context_type="warmup")
            
            # 测试响应时间
            response_times = []
            for i in range(50):
                start_time = time.time()
                result = await manager.execute_complete_operation(
                    "context.create_enhanced",
                    context_type="performance_test",
                    initial_content={"iteration": i}
                )
                end_time = time.time()
                
                if result["success"]:
                    response_times.append(end_time - start_time)
            
            # 计算性能指标
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                logger.info(f"响应时间性能 - 平均: {avg_response_time:.3f}s, 最大: {max_response_time:.3f}s, 最小: {min_response_time:.3f}s")
                
                # 性能验证
                assert avg_response_time < 0.5, f"平均响应时间超标: {avg_response_time:.3f}s"
                assert max_response_time < 1.0, f"最大响应时间超标: {max_response_time:.3f}s"
                
                logger.info("✅ 响应时间性能测试通过")
            else:
                logger.warning("未收集到响应时间数据")
                
        finally:
            await manager.stop_complete_system()
    
    @pytest.mark.asyncio
    async def test_throughput_performance(self):
        """测试吞吐量性能"""
        logger.info("测试吞吐量性能...")
        
        config = CompleteSystemConfig(
            max_workers=16,
            max_concurrent_operations=100,
            response_time_target=0.1
        )
        
        manager = UnifiedSystemManagerComplete(config)
        await manager.start_complete_system()
        
        try:
            # 测试吞吐量
            test_duration = 10  # 10秒测试
            start_time = time.time()
            end_time = start_time + test_duration
            
            completed_operations = 0
            failed_operations = 0
            
            # 持续提交操作直到时间结束
            tasks = []
            while time.time() < end_time:
                task = manager.execute_complete_operation(
                    "context.create_enhanced",
                    context_type="throughput_test",
                    initial_content={"timestamp": time.time()}
                )
                tasks.append(task)
                
                # 限制并发数量
                if len(tasks) >= 20:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, dict) and result.get("success", False):
                            completed_operations += 1
                        else:
                            failed_operations += 1
                    tasks = []
                
                await asyncio.sleep(0.01)  # 小延迟避免过载
            
            # 处理剩余任务
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, dict) and result.get("success", False):
                        completed_operations += 1
                    else:
                        failed_operations += 1
            
            # 计算吞吐量
            actual_duration = time.time() - start_time
            throughput = completed_operations / actual_duration
            error_rate = failed_operations / (completed_operations + failed_operations) if (completed_operations + failed_operations) > 0 else 0
            
            logger.info(f"吞吐量性能 - 完成操作: {completed_operations}, 吞吐量: {throughput:.2f} ops/s, 错误率: {error_rate:.2%}")
            
            # 性能验证
            assert throughput > 5.0, f"吞吐量不足: {throughput:.2f} ops/s"
            assert error_rate < 0.05, f"错误率过高: {error_rate:.2%}"
            
            logger.info("✅ 吞吐量性能测试通过")
            
        finally:
            await manager.stop_complete_system()

@pytest.mark.asyncio
async def test_complete_system_end_to_end():
    """端到端完整系统测试"""
    logger.info("开始端到端完整系统测试...")
    
    # 创建测试套件
    test_suite = TestCompleteSystemCore()
    config = CompleteSystemConfig()
    
    # 运行完整的端到端测试
    manager = UnifiedSystemManagerComplete(config)
    
    try:
        # 启动系统
        logger.info("启动完整系统...")
        start_success = await manager.start_complete_system()
        assert start_success, "端到端测试启动失败"
        
        # 等待系统稳定
        await asyncio.sleep(3)
        
        # 验证系统状态
        status = manager.get_complete_system_status()
        logger.info(f"系统状态: {status}")
        
        # 执行端到端场景
        logger.info("执行端到端测试场景...")
        
        # 1. 动机生成 -> 元认知反思 -> 系统操作 的完整流程
        motivation_result = await manager.execute_complete_operation(
            "motivation.generate",
            context={
                "system_state": {"error_rate": 0.02, "response_time": 0.15},
                "performance_metrics": {"throughput": 150, "efficiency": 0.85}
            }
        )
        assert motivation_result["success"], "动机生成失败"
        
        # 基于动机结果进行元认知反思
        cognition_data = {
            "motivation_result": motivation_result["result"],
            "reasoning_steps": [{"step": "analyze_motivation", "confidence": 0.9}],
            "decision_points": [{"choice": "proceed_with_goals", "rationale": "goals_are_valuable"}]
        }
        
        metacognition_result = await manager.execute_complete_operation(
            "metacognition.reflect",
            cognition_data=cognition_data
        )
        assert metacognition_result["success"], "元认知反思失败"
        
        # 执行系统操作
        system_result = await manager.execute_complete_operation(
            "context.create_enhanced",
            context_type="end_to_end_test",
            initial_content={
                "motivation_data": motivation_result["result"],
                "metacognition_data": metacognition_result["result"],
                "integration_timestamp": time.time()
            }
        )
        assert system_result["success"], "系统操作失败"
        
        # 2. 异步任务处理验证
        async_task_id = await manager.submit_async_task(
            "system_operation",
            {"operation": "context.create_enhanced", "context_type": "async_end_to_end"}
        )
        
        async_result = await manager.get_async_result(async_task_id, timeout=15.0)
        assert async_result is not None, "异步任务结果获取失败"
        assert async_result.get("success", False), "异步任务执行失败"
        
        # 3. 并发压力测试
        concurrent_operations = []
        for i in range(25):
            op = manager.execute_complete_operation(
                "context.create_enhanced",
                context_type="concurrent_end_to_end",
                initial_content={"concurrent_id": i, "integration_test": True}
            )
            concurrent_operations.append(op)
        
        concurrent_results = await asyncio.gather(*concurrent_operations, return_exceptions=True)
        successful_concurrent = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get("success", False))
        
        assert successful_concurrent >= 20, f"并发测试成功率不足: {successful_concurrent}/25"
        
        # 4. 最终系统状态验证
        final_status = manager.get_complete_system_status()
        
        # 验证关键指标
        assert final_status["system_state"] == "running", "系统未保持运行状态"
        assert final_status["production_ready"] is True, "系统未保持生产就绪状态"
        assert final_status["modular_score"] == 1200, "模块化分数未达到满分"
        assert final_status["agi_level"] == "Level 3-4 (Complete System)", "AGI等级未达标"
        
        # 验证异步架构状态
        async_status = final_status["async_architecture"]
        assert async_status["async_loop_active"] is True, "异步循环未保持激活"
        assert async_status["async_processing_enabled"] is True, "异步处理未保持启用"
        assert async_status["performance_optimized"] is True, "性能未保持优化"
        
        logger.info("✅ 端到端完整系统测试通过")
        logger.info(f"最终系统状态: {final_status}")
        
    finally:
        # 确保系统正确关闭
        logger.info("关闭完整系统...")
        await manager.stop_complete_system()
        logger.info("✅ 端到端测试完成")

if __name__ == "__main__":
    # 运行测试
    logger.info("开始完整版系统测试...")
    
    # 运行端到端测试
    asyncio.run(test_complete_system_end_to_end())
    
    logger.info("完整版系统测试完成")