#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试结果处理演示脚本
展示如何使用测试结果处理组件
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root: str = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def demo_test_result_processing() -> None:
    """演示测试结果处理流程"""


    print("=== 测试结果处理演示 ===")
    
    # 动态导入模块
    from apps.backend.scripts.test_result_visualizer import TestResultVisualizer
    from apps.backend.scripts.test_result_analyzer import TestResultAnalyzer
    from apps.backend.scripts.test_result_feedback import TestResultFeedbackSystem
    
    # 确保必要的目录存在
    test_data_dir = project_root / "apps" / "backend" / "test_data"
    test_reports_dir = test_data_dir / "test_reports"
    templates_dir = test_data_dir / "templates"
    test_reports_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)
    
    # 初始化组件，指定正确的目录
    visualizer = TestResultVisualizer(results_dir=str(test_data_dir), reports_dir=str(test_reports_dir))
    analyzer = TestResultAnalyzer(results_dir=str(test_data_dir), reports_dir=str(test_reports_dir))
    feedback_system = TestResultFeedbackSystem(reports_dir=str(test_reports_dir), templates_dir=str(templates_dir))
    
    # 1. 加载示例测试结果
    print("1. 加载示例测试结果...")
    test_data_path = project_root / "apps" / "backend" / "test_data" / "sample_test_results.json"
    
    # 直接读取JSON文件
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
    except Exception as e:
        print(f"无法加载测试结果文件: {test_data_path}, 错误: {e}")
        return
    
    print(f"   成功加载测试结果，总测试数: {results_data['summary']['total']}")
    
    # 2. 生成可视化图表
    print("2. 生成可视化图表...")
    # 切换到test_data目录以正确加载文件
    original_cwd = Path.cwd()
    os.chdir(test_data_dir)
    visualizer.visualize_test_distribution(results_data)
    visualizer.generate_html_report(results_data)
    # 恢复原目录
    os.chdir(original_cwd)
    print("   可视化图表生成完成")
    
    # 3. 分析测试结果
    print("3. 分析测试结果...")
    # 切换到test_data目录以正确加载文件
    os.chdir(test_data_dir)
    failure_patterns = analyzer.analyze_failure_patterns(results_data)
    
     # 生成分析报告

    analysis_report = analyzer.generate_analysis_report(
        results_data, failure_patterns)
    print(f"   分析报告已生成: {test_reports_dir / 'analysis_report.json'}")
    
    # 恢复原目录
    os.chdir(original_cwd)
    print(f"   发现 {len(failure_patterns)} 个失败模式")
    
    # 4. 生成改进建议
    print("4. 生成改进建议...")
    suggestions = feedback_system.generate_improvement_suggestions(analysis_report)
    print(f"   生成 {len(suggestions)} 个改进建议")
    
    # 5. 生成反馈报告
    print("5. 生成反馈报告...")
    # 切换到test_data目录以正确生成报告

    os.chdir(test_data_dir)
    feedback_report_path = feedback_system.generate_feedback_report(
        analysis_report, suggestions)
    # 恢复原目录
    os.chdir(original_cwd)
    print(f"   反馈报告生成完成: {feedback_report_path}")
    
    print("\n=== 演示完成 ===")
    print("生成的文件:")
    print("  - test_reports/test_distribution.png (测试分布图)")
    print("  - test_reports/visualization_report.html (可视化报告)")
    print("  - test_reports/analysis_report.json (分析报告)")
    print("  - test_reports/feedback_report.html (反馈报告)")

if __name__ == "__main__":
    demo_test_result_processing()