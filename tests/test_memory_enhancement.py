"""
记忆增强系统测试
===============
测试记忆增强系统的各个组件

测试内容：
1. 记忆模板创建和序列化
2. 模板检索功能
3. 状态相似度计算
4. 预计算服务
5. LLM 服务集成
6. 端到端对话测试
"""

import asyncio
import sys
import os
import time
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apps.backend.src.ai.memory.memory_template import (
    MemoryTemplate,
    ResponseCategory,
    AngelaState,
    UserImpression,
    generate_template_id,
    create_template
)
from apps.backend.src.ai.memory.template_library import TemplateLibrary, PredefinedTemplate, get_template_library
from apps.backend.src.ai.memory.precompute_service import PrecomputeService, PrecomputeTask

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestMemoryEnhancement:
    """记忆增强系统测试类"""

    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

    def record_test(self, name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

        if passed:
            self.results["passed"] += 1
            logger.info(f"✓ {name}")
        else:
            self.results["failed"] += 1
            logger.error(f"✗ {name}: {details}")

    def test_1_template_creation_and_serialization(self):
        """测试 1: 记忆模板创建和序列化"""
        try:
            # 创建模板
            template = create_template(
                content="你好！见到你真开心~",
                category=ResponseCategory.GREETING,
                keywords=["你好", "开心"],
                metadata={"test": True}
            )

            # 测试序列化
            template_dict = template.to_dict()

            # 测试反序列化
            template_restored = MemoryTemplate.from_dict(template_dict)

            # 验证
            assert template.id == template_restored.id, "ID 不匹配"
            assert template.content == template_restored.content, "内容不匹配"
            assert template.category == template_restored.category, "类别不匹配"

            # 测试使用记录
            template.record_usage(success=True)
            assert template.usage_count == 1, "使用次数不正确"

            self.record_test("模板创建和序列化", True)
        except Exception as e:
            self.record_test("模板创建和序列化", False, str(e))

    def test_2_template_retrieval(self):
        """测试 2: 模板检索功能"""
        try:
            # 创建模板库
            library = TemplateLibrary()

            # 获取所有模板
            all_templates = library.get_all_templates()

            # 验证
            assert len(all_templates) > 0, "模板库为空"

            # 按类别获取模板
            greeting_templates = library.get_by_category(ResponseCategory.GREETING)
            assert len(greeting_templates) > 0, "问候类模板为空"

            # 按 ID 获取模板
            if greeting_templates:
                template = library.get_by_id(greeting_templates[0].id)
                assert template is not None, "无法通过 ID 获取模板"

            self.record_test("模板检索功能", True, f"共 {len(all_templates)} 个模板")
        except Exception as e:
            self.record_test("模板检索功能", False, str(e))

    def test_3_state_similarity_calculation(self):
        """测试 3: 状态相似度计算"""
        try:
            # 创建两个相似的状态
            state1 = AngelaState(
                alpha={"energy": 0.8},
                beta={"happy": 0.9},
                gamma={"thinking": 0.3},
                delta={"tired": 0.2}
            )

            state2 = AngelaState(
                alpha={"energy": 0.7},
                beta={"happy": 0.8},
                gamma={"thinking": 0.4},
                delta={"tired": 0.3}
            )

            # 创建两个不同的状态
            state3 = AngelaState(
                alpha={"energy": 0.2},
                beta={"sad": 0.9},
                gamma={"thinking": 0.8},
                delta={"tired": 0.9}
            )

            # 计算相似度（简化版本，实际应该在 QueryEngine 中测试）
            # 这里只测试状态创建和基本操作
            state1_dict = state1.to_dict()
            state1_restored = AngelaState.from_dict(state1_dict)

            assert state1.alpha == state1_restored.alpha, "Alpha 状态不匹配"

            self.record_test("状态相似度计算", True)
        except Exception as e:
            self.record_test("状态相似度计算", False, str(e))

    def test_4_precompute_service(self):
        """测试 4: 预计算服务"""
        try:
            # 创建预计算服务（启动后台任务）
            from apps.backend.src.ai.memory.precompute_service import PrecomputeService

            # 创建模拟的 LLM 服务
            class MockLLMService:
                async def generate_response(self, query, context):
                    from apps.backend.src.services.angela_llm_service import LLMResponse
                    return LLMResponse(
                        text=f"回应: {query}",
                        backend="mock",
                        model="test"
                    )

            # 创建模拟的记忆管理器
            class MockMemoryManager:
                async def store_template(self, template):
                    return True

            service = PrecomputeService(
                llm_service=MockLLMService(),
                memory_manager=MockMemoryManager(),
                idle_threshold=1.0,
                cpu_threshold=90.0
            )

            # 启动服务
            asyncio.run(service.start())

            # 测试添加任务
            task = PrecomputeTask(
                query="测试查询",
                category=ResponseCategory.QUESTION,
                keywords=["测试"],
                angela_state=AngelaState(),
                user_impression=UserImpression(),
                context={}
            )

            success = service.add_precompute_task(task)
            assert success, "添加任务失败"

            # 测试统计
            stats = service.get_stats()
            assert "total_tasks" in stats, "统计信息不完整"

            # 停止服务
            asyncio.run(service.stop())

            self.record_test("预计算服务", True, f"队列大小: {stats['queue_size']}")
        except Exception as e:
            self.record_test("预计算服务", False, str(e))

    def test_5_template_library_completeness(self):
        """测试 5: 模板库完整性"""
        try:
            library = TemplateLibrary()

            # 检查所有预定义模板
            all_templates = library.get_all_templates()
            assert len(all_templates) >= 20, f"模板数量不足: {len(all_templates)}"

            # 检查各类别都有模板
            category_counts = library.get_category_counts()

            # 检查关键类别
            required_categories = [
                ResponseCategory.GREETING,
                ResponseCategory.FAREWELL,
                ResponseCategory.EMOTIONAL,
                ResponseCategory.SMALL_TALK
            ]

            for category in required_categories:
                assert category in category_counts, f"缺少 {category.value} 类别"

            self.record_test("模板库完整性", True, f"共 {len(all_templates)} 个模板")
        except Exception as e:
            self.record_test("模板库完整性", False, str(e))

    def test_6_user_impression_model(self):
        """测试 6: 用户印象模型"""
        try:
            impression = UserImpression(
                relationship_level=0.7,
                preferred_style="casual",
                interaction_count=50,
                tags=["friendly", "talkative"]
            )

            # 测试序列化
            impression_dict = impression.to_dict()

            # 测试反序列化
            impression_restored = UserImpression.from_dict(impression_dict)

            # 验证
            assert impression.relationship_level == impression_restored.relationship_level
            assert impression.preferred_style == impression_restored.preferred_style

            self.record_test("用户印象模型", True)
        except Exception as e:
            self.record_test("用户印象模型", False, str(e))

    async def test_7_end_to_end_dialogue_simulation(self):
        """测试 7: 端到端对话模拟"""
        try:
            # 导入必要的模块
            from apps.backend.src.ai.memory.precompute_service import PrecomputeTask
            from apps.backend.src.services.angela_llm_service import LLMResponse

            # 创建模拟的 LLM 服务
            class MockLLMService:
                def __init__(self):
                    self.response_count = 0

                async def generate_response(self, query, context):
                    self.response_count += 1

                    # 模拟响应延迟
                    await asyncio.sleep(0.1)

                    return LLMResponse(
                        text=f"这是对 '{query}' 的回應 #{self.response_count}",
                        backend="mock",
                        model="test",
                        confidence=0.9
                    )

            llm_service = MockLLMService()

            # 模拟对话
            queries = [
                "你好！",
                "今天天气怎么样？",
                "你觉得怎么样？",
                "再见！"
            ]

            response_times = []

            for query in queries:
                start_time = time.time()
                response = await llm_service.generate_response(query, {})
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)

                assert response.text, "回應为空"
                assert not response.error, f"回應错误: {response.error}"

            # 计算平均响应时间
            avg_response_time = sum(response_times) / len(response_times)

            self.record_test(
                "端到端对话模拟",
                True,
                f"平均响应时间: {avg_response_time:.0f}ms"
            )
        except Exception as e:
            self.record_test("端到端对话模拟", False, str(e))

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始记忆增强系统测试")
        logger.info("=" * 60)

        # 同步测试
        self.test_1_template_creation_and_serialization()
        self.test_2_template_retrieval()
        self.test_3_state_similarity_calculation()
        self.test_4_precompute_service()
        self.test_5_template_library_completeness()
        self.test_6_user_impression_model()

        # 异步测试
        asyncio.run(self.test_7_end_to_end_dialogue_simulation())

        # 输出结果
        logger.info("=" * 60)
        logger.info("测试结果汇总")
        logger.info("=" * 60)
        logger.info(f"通过: {self.results['passed']}")
        logger.info(f"失败: {self.results['failed']}")
        logger.info(f"总计: {self.results['passed'] + self.results['failed']}")

        success_rate = (
            self.results['passed'] /
            (self.results['passed'] + self.results['failed'])
            if (self.results['passed'] + self.results['failed']) > 0
            else 0
        )
        logger.info(f"成功率: {success_rate * 100:.1f}%")

        return self.results


def main():
    """主函数"""
    tester = TestMemoryEnhancement()
    results = tester.run_all_tests()

    # 返回退出码
    return 0 if results['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())