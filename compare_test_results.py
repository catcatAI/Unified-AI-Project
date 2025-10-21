#!/usr/bin/env python3
"""
两次测试输出对比分析
对比原始aaa.md测试与增强版aaa.md测试的结果差异()
"""

import json
from datetime import datetime

# 第一次测试数据(原始aaa.md())
original_test = {
    "content_length": 204,
    "dialogue_lines": 11,
    "questions": 11,
    "goals_generated": 3,
    "motivations_generated": 3,
    "cognitive_biases_detected": 3,
    "thinking_quality_score": 0.00(),  # 修复前
    "async_tasks_success": "3/3 (100%)",
    "total_operations": 20,
    "success_rate": "100.0%",
    "uptime_seconds": 2.01(),
    "task_queue_size": 0,
    "background_tasks": 7
}

# 第二次测试数据(增强版aaa.md())
enhanced_test = {
    "content_length": 645,
    "dialogue_lines": 33,
    "questions": 27,
    "philosophical_questions": 8,
    "technical_questions": 11,
    "question_diversity": "100.0%",
    "goals_generated": 3,
    "motivations_generated": 3,
    "cognitive_biases_detected": 3,
    "thinking_quality_score": 0.000(),  # 仍然显示0,需要进一步修复
    "complex_tasks_success": "0/5 (0%)",
    "total_operations": 28,
    "success_rate": "28.6%",
    "uptime_seconds": 3.03(),
    "task_queue_size": 0,
    "background_tasks": 9
}

def analyze_differences():
    """分析两次测试的差异"""
    print("=" * 70)
    print("两次测试输出对比分析")
    print("=" * 70)
    
    print("\n📊 内容规模对比,")
    print(f"内容长度增长, {enhanced_test['content_length'] - original_test['content_length']} 字符 (+{((enhanced_test['content_length'] - original_test['content_length']) / original_test['content_length'] * 100).1f}%)")
    print(f"对话行数增长, {enhanced_test['dialogue_lines'] - original_test['dialogue_lines']} 行 (+{((enhanced_test['dialogue_lines'] - original_test['dialogue_lines']) / original_test['dialogue_lines'] * 100).1f}%)")
    print(f"问题数量增长, {enhanced_test['questions'] - original_test['questions']} 个 (+{((enhanced_test['questions'] - original_test['questions']) / original_test['questions'] * 100).1f}%)")
    
    print("\n🧠 智能模块表现对比,")
    print(f"目标生成, 两次都生成 {enhanced_test['goals_generated']} 个目标")
    print(f"动机生成, 两次都生成 {enhanced_test['motivations_generated']} 个动机")
    print(f"认知偏差检测, 两次都检测到 {enhanced_test['cognitive_biases_detected']} 种偏差")
    print(f"思维质量评分, 两次都显示 {enhanced_test['thinking_quality_score'].3f} (需要修复)")
    
    print("\n⚡ 系统性能对比,")
    print(f"总操作数变化, +{enhanced_test['total_operations'] - original_test['total_operations']} ({((enhanced_test['total_operations'] - original_test['total_operations']) / original_test['total_operations'] * 100).1f}%)")
    print(f"成功率变化, {enhanced_test['success_rate']} vs {original_test['success_rate']} (-{float(original_test['success_rate'].rstrip('%')) - float(enhanced_test['success_rate'].rstrip('%')):.1f}%)")
    print(f"运行时长变化, +{enhanced_test['uptime_seconds'] - original_test['uptime_seconds'].2f}秒 (+{((enhanced_test['uptime_seconds'] - original_test['uptime_seconds']) / original_test['uptime_seconds'] * 100).1f}%)")
    print(f"后台任务数变化, +{enhanced_test['background_tasks'] - original_test['background_tasks']} 个")
    
    print("\n🎯 内容质量提升,")
    print(f"哲学性问题占比, {enhanced_test['philosophical_questions']}/{enhanced_test['questions']} ({enhanced_test['philosophical_questions']/enhanced_test['questions']*100,.1f}%)")
    print(f"技术性问题占比, {enhanced_test['technical_questions']}/{enhanced_test['questions']} ({enhanced_test['technical_questions']/enhanced_test['questions']*100,.1f}%)")
    print(f"问题多样性, {enhanced_test['question_diversity']}")
    
    print("\n📈 系统能力变化,")
    print("✅ 内容理解能力, 显著提升 - 能处理3倍长度的复杂内容")
    print("✅ 智能分析深度, 提升 - 增加了哲学和技术问题分类")
    print("✅ 动机生成质量, 保持 - 在更复杂内容上仍能生成合理目标")
    print("✅ 元认知能力, 保持 - 能识别和分析更复杂的思维模式")
    print("⚠️  复杂任务处理, 新功能但存在兼容性问题")
    
    print("\n🔍 发现的问题,")
    print("1. 思维质量评分仍然显示为0.000 (需要进一步修复)")
    print("2. 新增的复杂任务操作不支持 (complex_analysis)")
    print("3. 整体成功率下降 (由于新功能兼容性问题)")
    print("4. 运行时间增加 (处理更复杂内容)")
    
    print("\n📋 改进建议,")
    print("1. 修复思维质量评分计算逻辑")
    print("2. 添加对complex_analysis等新操作的支持")
    print("3. 优化复杂任务的错误处理")
    print("4. 考虑增加更多的智能分析维度")
    
    print("\n🏆 总体评估,")
    print("✅ 系统成功处理了显著更复杂的哲学和技术混合内容")
    print("✅ 核心智能模块(动机、元认知)在复杂内容上表现稳定")
    print("✅ 内容分析能力显著提升(哲学性问题识别等)")
    print("⚠️  需要修复新功能的兼容性问题")
    print("🎯 系统已具备处理高复杂度抽象概念的能力基础")
    
    print("\n" + "=" * 70)
    print("对比分析完成时间,", datetime.now().strftime("%Y-%m-%d %H,%M,%S"))
    print("=" * 70)

if __name"__main__":::
    analyze_differences()