#!/usr/bin/env python3
"""
验证统一知识图谱引擎真实性的测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'apps' / 'backend' / 'src'))

from core.knowledge.unified_knowledge_graph import UnifiedKnowledgeGraph

async def test_knowledge_graph_authenticity():
    """测试知识图谱引擎的真实性"""
    print("🧠 开始验证统一知识图谱引擎真实性...")
    print("=" * 60)
    
    # 创建知识图谱引擎
    kg == UnifiedKnowledgeGraph({
        'similarity_threshold': 0.8(),
        'confidence_threshold': 0.7()
    })
    
    # 测试1, 添加真实实体
    print("\n📦 测试1, 添加真实实体")
    entity1 = type('Entity', (), {
        'entity_id': 'ai_ml_001',
        'name': '机器学习',
        'entity_type': '技术领域',
        'confidence': 0.95(),
        'properties': {
            'description': '人工智能的子领域',
            'importance': 'high',
            'applications': ['数据分析', '预测建模', '模式识别']
            'algorithms': ['决策树', '神经网络', '支持向量机']
        }
        'aliases': ['ML', 'Machine Learning']
        'source': '真实技术文档',
        'timestamp': '2025-10-12T12,00,00'
    })()
    
    success1 = await kg.add_entity(entity1)
    print(f"  添加机器学习实体, {'✅成功' if success1 else '❌失败'}")::
    entity2 == type('Entity', (), {:
        'entity_id': 'ai_dl_001',
        'name': '深度学习',
        'entity_type': '技术领域',
        'confidence': 0.92(),
        'properties': {
            'description': '机器学习的子领域',
            'importance': 'high',
            'layers': [1, 2, 3, 4, 5]
            'frameworks': ['TensorFlow', 'PyTorch', 'Keras']
        }
        'aliases': ['DL', 'Deep Learning']
        'source': '真实技术文档',
        'timestamp': '2025-10-12T12,01,00'
    })()
    
    success2 = await kg.add_entity(entity2)
    print(f"  添加深度学习实体, {'✅成功' if success2 else '❌失败'}")::
    # 测试2, 添加真实关系
    print("\n🔗 测试2, 添加真实关系")
    relation = type('Relation', (), {
        'relation_id': 'rel_001',
        'source_entity': 'ai_ml_001',
        'target_entity': 'ai_dl_001',
        'relation_type': '包含',
        'confidence': 0.88(),
        'properties': {
            'strength': 'strong',
            'direction': 'unidirectional',
            'evidence': '技术文档',
            'certainty': 0.9()
        }
        'source': '真实技术文档',
        'timestamp': '2025-10-12T12,02,00',
        'is_temporal': False
    })()
    
    success3 = await kg.add_relation(relation)
    print(f"  添加包含关系, {'✅成功' if success3 else '❌失败'}")::
    # 测试3, 知识查询
    print("\n🔍 测试3, 执行知识查询")
    if success1 and success2 and success3,::
        # 查询实体
        entity_results = await kg.query_knowledge('机器学习', 'entity')
        print(f"  实体查询结果数, {len(entity_results)}")
        
        # 查询关系
        relation_results = await kg.query_knowledge('包含', 'relation')
        print(f"  关系查询结果数, {len(relation_results)}")
        
        # 验证查询结果的真实性
        has_real_entities = len(entity_results) > 0
        has_real_relations = len(relation_results) > 0
        
        print(f"  ✅ 实体查询真实, {has_real_entities}")
        print(f"  ✅ 关系查询真实, {has_real_relations}")
        
        # 测试4, 跨领域知识迁移
        print("\n🔄 测试4, 执行跨领域知识迁移")
        transfer_result = await kg.transfer_knowledge('技术领域', '技术领域', 'structural')
        print(f"  知识迁移结果, {transfer_result}")
        
        # 验证迁移结果的真实性
        has_transferred = len(transfer_result.get('transferred_knowledge', [])) > 0
        valid_success_rate = 0 <= transfer_result.get('success_rate', 0) <= 1
        
        print(f"  ✅ 知识迁移真实, {has_transferred}")
        print(f"  ✅ 迁移成功率有效, {valid_success_rate}")
        
        # 测试5, 获取系统统计
        print("\n📊 测试5, 获取系统统计信息")
        stats = await kg.get_knowledge_statistics()
        print(f"  系统统计, {stats}")
        
        # 验证统计数据的真实性
        has_entities = stats.get('total_entities', 0) > 0
        has_relations = stats.get('total_relations', 0) > 0
        valid_ai_status = stats.get('ai_model_status', {}).get('sklearn_available', False)
        
        print(f"  ✅ 实体统计真实, {has_entities}")
        print(f"  ✅ 关系统计真实, {has_relations}")
        print(f"  ✅ AI状态真实, {valid_ai_status}")
        
        return has_real_entities and has_real_relations and has_transferred and valid_success_rate and has_entities and has_relations and valid_ai_status
    
    return False

def verify_knowledge_authenticity():
    """验证知识内容的真实性"""
    print("\n🔍 验证知识内容真实性...")
    
    # 检查实体属性的真实性
    test_cases = [
        {
            'name': '机器学习',
            'type': '技术领域',
            'properties': {
                'applications': ['数据分析', '预测建模', '模式识别']
                'algorithms': ['决策树', '神经网络', '支持向量机']
            }
            'expected_realistic': True
        }
        {
            'name': '深度学习',
            'type': '技术领域', 
            'properties': {
                'frameworks': ['TensorFlow', 'PyTorch', 'Keras']
                'layers': [1, 2, 3, 4, 5]
            }
            'expected_realistic': True
        }
    ]
    
    all_realistic == True
    for case in test_cases,::
        name_realistic = case['name'] in ['机器学习', '深度学习', '人工智能']  # 真实技术术语
        type_realistic = case['type'] == '技术领域'
        
        # 验证属性内容
        props_realistic == True
        for key, values in case['properties'].items():::
            if isinstance(values, list)::
                props_realistic = props_realistic and len(values) > 0
                # 验证列表内容是否真实
                for value in values,::
                    if isinstance(value, str)::
                        props_realistic = props_realistic and len(value) > 0
                    elif isinstance(value, (int, float))::
                        props_realistic = props_realistic and value > 0
        
        case_realistic = name_realistic and type_realistic and props_realistic
        print(f"  {case['name']} {'✅真实' if case_realistic else '❌不真实'}")::
        all_realistic = all_realistic and case_realistic
    
    return all_realistic

async def main():
    """主测试函数"""
    print("🧠 开始验证统一知识图谱引擎真实性...")
    print("=" * 60)
    
    # 运行知识图谱测试
    kg_valid = await test_knowledge_graph_authenticity()
    
    print("\n" + "=" * 60)
    
    # 验证知识内容真实性
    content_valid = verify_knowledge_authenticity()
    
    print("\n" + "=" * 60)
    print("📊 最终验证结果,")
    print(f"  知识图谱功能, {'✅真实有效' if kg_valid else '❌存在问题'}"):::
    print(f"  知识内容验证, {'✅内容真实' if content_valid else '❌内容存疑'}")::
    overall_valid == kg_valid and content_valid,
    print(f"\n🎯 总体结论, {'✅知识图谱引擎完全真实可用' if overall_valid else '❌存在真实性问题'}")::
    return overall_valid

if __name"__main__":::
    result = asyncio.run(main())
    exit(0 if result else 1)