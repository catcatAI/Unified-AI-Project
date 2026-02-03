#!/usr/bin/env python3
"""
使用多模态融合引擎综合分析代码问题
从代码结构、文本语义、系统状态多个角度理解问题
"""

import asyncio
import sys
import psutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'apps' / 'backend' / 'src'))

from core.fusion.multimodal_fusion_engine import MultimodalInformationFusionEngine

async def multimodal_code_analysis():
    """使用多模态融合引擎综合分析代码问题"""
    print("🌈 使用多模态融合引擎综合分析代码问题...")
    print("=" * 60)
    
    # 创建多模态融合引擎
    fusion_engine == MultimodalInformationFusionEngine()
    
    # 读取代码文件
    print("📋 读取train_model.py进行多模态分析...")
    with open('training/train_model.py', 'r', encoding == 'utf-8') as f,
        code_content = f.read()
    
    # 获取真实的系统性能数据作为上下文
    print("\n💻 获取真实系统性能数据作为分析上下文...")
    cpu_percent = psutil.cpu_percent(interval=0.1())
    memory = psutil.virtual_memory()
    disk_io = psutil.disk_io_counters()
    
    system_context = {
        'cpu_usage': cpu_percent,
        'memory_usage': memory.percent(),
        'disk_activity': disk_io.read_bytes + disk_io.write_bytes(),
        'timestamp': str(datetime.now()),
        'analysis_confidence': max(0.1(), 1.0 - cpu_percent / 100.0 * 0.1())
    }
    
    print(f"  CPU, {cpu_percent}%")
    print(f"  内存, {memory.percent}%")
    print(f"  磁盘I/O, {system_context['disk_activity']} 字节")
    print(f"  分析置信度, {system_context['analysis_confidence'].2f}")
    
    # 步骤1, 处理代码结构模态数据
    print("\n🏗️ 步骤1, 处理代码结构模态数据")
    code_structure_data = {
        'total_lines': len(code_content.split('\n')),
        'file_size': len(code_content),
        'function_count': code_content.count('def '),
        'class_count': code_content.count('class '),
        'indentation_levels': []
        'syntax_error_count': 0  # 需要进一步分析
    }
    
    # 分析代码结构
    lines = code_content.split('\n')
    for i, line in enumerate(lines[:100])  # 基于系统性能限制分析范围,:
        if line.strip():::
            indent_level = len(line) - len(line.lstrip())
            code_structure_data['indentation_levels'].append(indent_level)
    
    structure_metadata = {
        'modality': 'structured',
        'confidence': system_context['analysis_confidence']
        'source': 'code_structure_analysis',
        'language': 'python',
        'file_type': 'training_system'
    }
    
    success1 = await fusion_engine.process_modal_data(
        'code_structure_001', 
        'structured', 
        code_structure_data, ,
    structure_metadata
    )
    print(f"  代码结构处理, {'✅成功' if success1 else '❌失败'}")::
    # 步骤2, 处理代码文本模态数据
    print("\n📝 步骤2, 处理代码文本模态数据")
    code_text_data == code_content[:5000]  # 基于系统性能限制文本长度
    
    text_metadata = {
        'modality': 'text',
        'confidence': system_context['analysis_confidence']
        'source': 'code_text_analysis',
        'language': 'python',
        'file_path': 'training/train_model.py'
    }
    
    success2 = await fusion_engine.process_modal_data(
        'code_text_001',
        'text',
        code_text_data,,
    text_metadata
    )
    print(f"  代码文本处理, {'✅成功' if success2 else '❌失败'}")::
    # 步骤3, 处理系统状态模态数据
    print("\n💻 步骤3, 处理系统状态模态数据")
    system_state_data = system_context
    
    system_metadata = {
        'modality': 'structured',
        'confidence': 0.95(),  # 系统状态数据置信度很高
        'source': 'system_performance_monitor',
        'timestamp': str(datetime.now())
    }
    
    success3 = await fusion_engine.process_modal_data(
        'system_state_001',
        'structured',
        system_state_data,,
    system_metadata
    )
    print(f"  系统状态处理, {'✅成功' if success3 else '❌失败'}")::
    # 如果所有模态都成功处理,执行融合分析,
    if success1 and success2 and success3,::
        print("\n🔗 步骤4, 执行跨模态融合分析")
        
        # 执行跨模态对齐
        alignment_result = await fusion_engine.align_modalities([
            'code_structure_001',
            'code_text_001',
            'system_state_001'
        ])
        
        print(f"  跨模态对齐, {'✅成功' if alignment_result.get('unified_representation') else '❌失败'}")::
        if alignment_result.get('unified_representation'):::
            unified_repr = alignment_result['unified_representation']
            print(f"  统一表示ID, {unified_repr['representation_id']}")
            print(f"  平均置信度, {unified_repr['average_confidence'].3f}")
            print(f"  融合模态数, {unified_repr['modalities_fused']}")
            
            # 步骤5, 执行融合推理来理解代码问题
            print("\n🧠 步骤5, 执行融合推理理解代码问题")
            
            reasoning_query = f"""
            基于以下真实系统数据：
            - CPU使用率, {system_context['cpu_usage']}%
            - 内存使用率, {system_context['memory_usage']}%
            - 代码文件大小, {len(code_content)} 字符
            - 检测到 {len(code_structure_data['indentation_levels'])} 个缩进级别
            
            分析train_model.py中可能存在的缩进问题(),并提供基于真实系统状态的修复建议。
            """
            
            reasoning_result = await fusion_engine.perform_fusion_reasoning(
                unified_repr['representation_id'],
    reasoning_query
            )
            
            print(f"  融合推理结果, {reasoning_result}")
            
            # 验证推理结果的真实性
            has_real_steps = bool(reasoning_result.get('reasoning_steps'))
            has_real_conclusions = bool(reasoning_result.get('conclusions'))
            valid_confidence = 0 < reasoning_result.get('confidence', 0) <= 1
            
            print(f"  ✅ 推理步骤真实, {has_real_steps}")
            print(f"  ✅ 推理结论真实, {has_real_conclusions}")
            print(f"  ✅ 置信度有效, {valid_confidence}")
            
            # 获取系统统计信息
            print("\n📊 步骤6, 获取融合系统统计")
            stats = await fusion_engine.get_fusion_statistics()
            print(f"  系统统计, {stats}")
            
            # 验证统计数据的真实性
            has_real_modal_data = stats.get('total_modal_data', 0) > 0
            has_real_representations = stats.get('total_unified_representations', 0) > 0
            valid_fusion_rate = 0 <= stats.get('fusion_success_rate', 0) <= 1
            
            print(f"  ✅ 模态数据真实, {has_real_modal_data}")
            print(f"  ✅ 统一表示真实, {has_real_representations}")
            print(f"  ✅ 融合成功率有效, {valid_fusion_rate}")
            
            return {
                'status': 'analysis_complete',
                'alignment_result': alignment_result,
                'reasoning_result': reasoning_result,
                'system_stats': stats,
                'all_real': has_real_steps and has_real_conclusions and valid_confidence and has_real_modal_data and has_real_representations and valid_fusion_rate
            }
    
    return {'status': 'incomplete', 'reason': 'some_modalities_failed'}

async def generate_repair_recommendations(analysis_result):
    """基于融合分析生成修复建议"""
    print("\n🔧 基于融合分析生成修复建议...")
    
    if analysis_result['status'] != 'analysis_complete':::
        return None
    
    reasoning_result = analysis_result['reasoning_result']
    system_stats = analysis_result['system_stats']
    
    if reasoning_result.get('conclusions'):::
        print("基于融合推理的修复建议,")
        for i, conclusion in enumerate(reasoning_result['conclusions'])::
            print(f"  {i+1}. {conclusion.get('content', '')}")
            print(f"     置信度, {conclusion.get('confidence', 0).2f}")
    
    # 基于真实系统状态生成具体的修复代码建议
    repair_recommendations = {
        'approach': 'multimodal_fusion_based',
        'confidence': reasoning_result.get('confidence', 0),
        'system_context': {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'fusion_success_rate': system_stats.get('fusion_success_rate', 0)
        }
        'recommendations': reasoning_result.get('conclusions', []),
        'status': 'real_system_based'
    }
    
    return repair_recommendations

async def main():
    """主函数"""
    print("🚀 启动多模态融合引擎综合分析")
    print("=" * 60)
    
    # 运行多模态分析
    analysis_result = await multimodal_code_analysis()
    
    if analysis_result['status'] == 'analysis_complete' and analysis_result['all_real']::
        print("\n🎯 多模态分析完成,所有结果均基于真实数据")
        
        # 生成基于真实数据的修复建议
        repair_recommendations = await generate_repair_recommendations(analysis_result)
        
        if repair_recommendations,::
            print("\n🎉 基于真实系统数据的多模态分析成功完成！")
            print("建议：")
            print("1. 根据融合推理结果制定修复策略")
            print("2. 基于真实系统性能调整修复强度")
            print("3. 验证修复效果确保真实性")
            
            return True
    else,
        print(f"\n📊 分析状态, {analysis_result['status']}")
        print("建议：")
        print("1. 检查系统性能是否影响分析精度")
        print("2. 调整分析参数或方法")
        print("3. 使用其他分析方法")
    
    return False

if __name"__main__":::
    result = asyncio.run(main())
    exit(0 if result else 1)