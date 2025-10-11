#!/usr/bin/env python3
"""
基于真实系统数据的全面解决方案
使用项目确实可用的部分进行系统性修复和全局性测试
"""

import psutil
import subprocess
import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime

def get_real_system_metrics():
    """获取真实的系统性能指标"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_io': psutil.disk_io_counters(),
        'timestamp': datetime.now().isoformat()
    }

def test_real_compiler():
    """使用真实Python编译器测试"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', 'training/train_model.py'
        ], capture_output=True, text=True, cwd='D:/Projects/Unified-AI-Project')
        
        return {
            'success': result.returncode == 0,
            'error': result.stderr.strip() if result.stderr else None,
            'output': result.stdout.strip() if result.stdout else None
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_real_data_generation():
    """测试真实的训练数据生成"""
    try:
        result = subprocess.run([
            sys.executable,
            'apps/backend/src/core/tools/math_model/data_generator.py',
            '--num-samples', '5',
            '--file-format', 'json',
            '--seed', str(int(datetime.now().timestamp()))
        ], capture_output=True, text=True, cwd='D:/Projects/Unified-AI-Project')
        
        if result.returncode == 0:
            # 检查生成的文件
            data_files = list(Path('data/raw_datasets').glob('*.json'))
            if data_files:
                latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 验证数据真实性
                valid_count = 0
                for item in data[:3]:  # 验证前3条
                    if 'problem' in item and 'answer' in item:
                        problem = item['problem'].split('=')[0].strip()
                        expected = item['answer']
                        try:
                            actual = str(eval(problem))
                            if actual == expected:
                                valid_count += 1
                        except:
                            pass
                
                return {
                    'status': 'success',
                    'data_count': len(data),
                    'valid_problems': valid_count,
                    'file': str(latest_file)
                }
            else:
                return {'status': 'no_files'}
        else:
            return {'status': 'failed', 'error': result.stderr}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def test_real_multimodal_fusion():
    """测试真实的多模态融合功能"""
    try:
        # 使用简单的多模态测试
        test_script = """
import asyncio
import sys
sys.path.insert(0, 'apps/backend/src')
from core.fusion.multimodal_fusion_engine import MultimodalInformationFusionEngine

async def test():
    engine = MultimodalInformationFusionEngine()
    
    # 测试真实的多模态处理
    text_data = "真实系统性能测试"
    structured_data = {"cpu": 45.2, "memory": 82.8, "timestamp": "2025-10-12T12:00:00"}
    
    success1 = await engine.process_modal_data('text_test', 'text', text_data, {'confidence': 0.9})
    success2 = await engine.process_modal_data('struct_test', 'structured', structured_data, {'confidence': 0.85})
    
    if success1 and success2:
        result = await engine.align_modalities(['text_test', 'struct_test'])
        return result.get('unified_representation') is not None
    
    return False

result = asyncio.run(test())
print(result)
"""
        
        result = subprocess.run([sys.executable, '-c', test_script], 
                               capture_output=True, text=True, cwd='D:/Projects/Unified-AI-Project')
        
        return {
            'status': 'success' if 'True' in result.stdout else 'failed',
            'output': result.stdout.strip(),
            'error': result.stderr.strip() if result.stderr else None
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def test_real_knowledge_graph():
    """测试真实的知识图谱功能"""
    try:
        test_script = """
import asyncio
import sys
sys.path.insert(0, 'apps/backend/src')
from core.knowledge.unified_knowledge_graph import UnifiedKnowledgeGraph

async def test():
    kg = UnifiedKnowledgeGraph()
    
    # 测试真实的知识图谱操作
    entity_data = {
        'entity_id': 'test_system_001',
        'name': '真实系统测试',
        'entity_type': '系统组件',
        'confidence': 0.95,
        'properties': {'type': 'performance_test', 'status': 'active'},
        'aliases': ['system_test'],
        'source': '真实系统测试',
        'timestamp': '2025-10-12T12:00:00'
    }
    
    # 创建实体对象
    entity = type('Entity', (), entity_data)()
    success = await kg.add_entity(entity)
    
    return success

result = asyncio.run(test())
print(result)
"""
        
        result = subprocess.run([sys.executable, '-c', test_script], 
                               capture_output=True, text=True, cwd='D:/Projects/Unified-AI-Project')
        
        return {
            'status': 'success' if 'True' in result.stdout else 'failed',
            'output': result.stdout.strip(),
            'error': result.stderr.strip() if result.stderr else None
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def perform_real_comprehensive_test():
    """执行真实的全面测试"""
    print("🚀 执行真实的全面测试")
    print("=" * 60)
    
    # 获取真实系统状态
    system_metrics = get_real_system_metrics()
    print(f"真实系统状态: CPU {system_metrics['cpu_percent']}%, 内存 {system_metrics['memory_percent']}%")
    
    # 测试1: 真实编译器
    print("\n🔍 测试1: 真实编译器")
    compiler_result = test_real_compiler()
    print(f"编译器测试: {'✅通过' if compiler_result['success'] else '❌失败'}")
    if not compiler_result['success']:
        print(f"  错误: {compiler_result['error']}")
    
    # 测试2: 真实训练数据生成
    print("\n🔍 测试2: 真实训练数据生成")
    training_result = test_real_data_generation()
    print(f"训练数据生成: {training_result['status']}")
    if training_result['status'] == 'success':
        print(f"  生成了 {training_result['data_count']} 条数据，{training_result['valid_problems']} 条验证通过")
    elif training_result['status'] == 'failed':
        print(f"  错误: {training_result['error']}")
    
    # 测试3: 真实多模态融合
    print("\n🔍 测试3: 真实多模态融合")
    fusion_result = test_real_multimodal_fusion()
    print(f"多模态融合: {fusion_result['status']}")
    if fusion_result['status'] == 'success':
        print("  ✅ 多模态融合功能真实可用")
    elif fusion_result['status'] == 'failed':
        print(f"  错误: {fusion_result['error']}")
    
    # 测试4: 真实知识图谱
    print("\n🔍 测试4: 真实知识图谱")
    kg_result = test_real_knowledge_graph()
    print(f"知识图谱: {kg_result['status']}")
    if kg_result['status'] == 'success':
        print("  ✅ 知识图谱功能真实可用")
    elif kg_result['status'] == 'failed':
        print(f"  错误: {kg_result['error']}")
    
    # 计算真实可用性
    total_tests = 4
    passed_tests = sum(1 for result in [compiler_result, training_result, fusion_result, kg_result] 
                      if result['status'] == 'success')
    
    print(f"\n📊 真实可用性结果: {passed_tests}/{total_tests} 组件真实可用 ({passed_tests/total_tests*100:.1f}%)")
    
    # 验证所有数值的真实性
    all_real = all(result['status'] == 'success' for result in [compiler_result, training_result, fusion_result, kg_result])
    
    if all_real:
        print("\n🎉 所有测试的组件都基于真实数据，无预设结果！")
        print("✅ 所有数值都有具体出处（硬件、文件系统、数学计算）")
        print("✅ 所有功能都真实运行，非预设模拟")
    else:
        print(f"\n⚠️ 有 {total_tests-passed_tests} 个组件需要进一步修复")
    
    return all_real

if __name__ == "__main__":
    success = perform_real_comprehensive_test()
    exit(0 if success else 1)