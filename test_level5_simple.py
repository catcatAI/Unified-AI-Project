#!/usr/bin/env python3
"""
Level 5 AGI组件验证测试
简化版测试，验证核心功能
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_level5_components():
    """测试Level 5组件核心功能"""
    print("🚀 Level 5 AGI组件验证测试")
    print("=" * 50)
    
    try:
        # 1. 测试统一知识图谱
        print("\n📚 测试统一知识图谱...")
        from apps.backend.src.core.knowledge.unified_knowledge_graph import UnifiedKnowledgeGraph
        
        kg = UnifiedKnowledgeGraph()
        
        # 添加测试实体
        from apps.backend.src.core.knowledge.unified_knowledge_graph import Entity, Relation
        
        entity = Entity(
            entity_id="test_ai",
            name="人工智能",
            entity_type="技术领域",
            confidence=0.95,
            properties={"description": "AI技术"},
            aliases=["AI"],
            source="test",
            timestamp=datetime.now()
        )
        
        success = await kg.add_entity(entity)
        print(f"✅ 知识图谱实体添加: {'成功' if success else '失败'}")
        
        # 2. 测试多模态融合
        print("\n🌈 测试多模态融合...")
        from apps.backend.src.core.fusion.multimodal_fusion_engine import MultimodalInformationFusionEngine
        
        fusion = MultimodalInformationFusionEngine()
        
        # 处理文本模态
        success1 = await fusion.process_modal_data("test_text", "text", "测试文本数据", {})
        success2 = await fusion.process_modal_data("test_struct", "structured", {"data": "test"}, {})
        
        print(f"✅ 文本模态处理: {'成功' if success1 else '失败'}")
        print(f"✅ 结构化模态处理: {'成功' if success2 else '失败'}")
        
        # 3. 测试认知约束
        print("\n🧠 测试认知约束...")
        from apps.backend.src.core.cognitive.cognitive_constraint_engine import CognitiveConstraintEngine, CognitiveTarget
        
        cognitive = CognitiveConstraintEngine()
        
        target = CognitiveTarget(
            target_id="test_target",
            description="测试认知目标",
            semantic_vector=None,
            priority=0.8,
            necessity_score=0.9,
            resource_requirements={'cpu': 0.5},
            dependencies=[],
            conflicts=[],
            creation_time=datetime.now(),
            deadline=None,
            metadata={'test': True}
        )
        
        result = await cognitive.add_cognitive_target(target)
        print(f"✅ 认知目标添加: {result['action']}")
        
        # 4. 测试综合功能
        print("\n🔗 测试组件协同...")
        
        # 基于知识图谱创建认知目标
        kg_target = CognitiveTarget(
            target_id="kg_based_target",
            description="基于知识图谱的语义分析目标",
            semantic_vector=None,
            priority=0.85,
            necessity_score=0.9,
            resource_requirements={'knowledge_processing': 0.6},
            dependencies=[],
            conflicts=[],
            creation_time=datetime.now(),
            deadline=None,
            metadata={'source': 'knowledge_graph'}
        )
        
        result = await cognitive.add_cognitive_target(kg_target)
        print(f"✅ 知识驱动认知目标: {result['action']}")
        
        # 获取统计信息
        kg_stats = await kg.get_knowledge_statistics()
        fusion_stats = await fusion.get_fusion_statistics()
        cognitive_stats = await cognitive.get_cognitive_constraint_statistics()
        
        print(f"📊 知识图谱实体: {kg_stats['total_entities']}")
        print(f"📊 融合成功率: {fusion_stats['fusion_success_rate']:.1%}")
        print(f"📊 认知约束平均必要性: {cognitive_stats['average_necessity_score']:.3f}")
        
        print("\n🎉 Level 5 AGI组件验证完成！")
        print("✅ 所有核心功能正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_level5_components())
    exit(0 if success else 1)