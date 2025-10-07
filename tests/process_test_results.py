#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试结果处理主脚本
整合测试结果可视化、分析和反馈功能
"""

import argparse
import logging
from pathlib import Path
from typing import Optional
import sys

# 添加项目根目录到Python路径
project_root: str = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.test_result_visualizer import TestResultVisualizer
from scripts.test_result_analyzer import TestResultAnalyzer
from scripts.test_result_feedback import TestResultFeedbackSystem

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger: Any = logging.getLogger(__name__)

def process_test_results(results_file: str, 
                        baseline_file: Optional[str] = None,
                        historical_files: Optional[list] = None,
                        send_email: bool = False,
                        recipient_emails: Optional[list] = None):
    """
    处理测试结果的完整流程
    
    Args:
        results_file: 测试结果文件路径
        baseline_file: 基线测试结果文件路径（用于性能回归检测）


        historical_files: 历史测试结果文件列表（用于趋势分析）
        send_email: 是否发送邮件通知
        recipient_emails: 邮件接收者列表
    """
    try:
        # 初始化组件
        visualizer = TestResultVisualizer()
        analyzer = TestResultAnalyzer()
        feedback_system = TestResultFeedbackSystem()
        
        # 1. 加载测试结果
        logger.info("正在加载测试结果...")
        results_data = visualizer.load_test_results(results_file)
        if not results_data:
            logger.error("无法加载测试结果数据")
            return False
        
        # 2. 生成可视化图表
        logger.info("正在生成可视化图表...")
        
        # 生成测试分布图
        visualizer.visualize_test_distribution(results_data)
        
        # 如果有历史数据，生成趋势图
        if historical_files:
            historical_results = []
            for file in historical_files:
                hist_data = visualizer.load_test_results(file)
                if hist_data:
                    historical_results.append(hist_data)
            
            if historical_results:
                # 添加当前结果到历史数据中
                historical_results.append(results_data)
                visualizer.visualize_test_trends(historical_results)
        
        # 生成HTML可视化报告
        visualizer.generate_html_report(results_data)
        
        # 3. 分析测试结果
        logger.info("正在分析测试结果...")
        
        # 分析失败模式
        failure_patterns = analyzer.analyze_failure_patterns(results_data)
        
        # 检测性能回归
        performance_regressions = []
        if baseline_file:
            baseline_data = analyzer.load_test_results(baseline_file)
            if baseline_data:

                performance_regressions = analyzer.detect_performance_regressions(
                    results_data, baseline_data)
        
        # 分析覆盖率趋势
        coverage_trends = {}
        if historical_files:
            historical_results = []
            for file in historical_files:
                hist_data = analyzer.load_test_results(file)
                if hist_data:
                    historical_results.append(hist_data)
            
            if historical_results:
                coverage_trends = analyzer.analyze_test_coverage_trends(historical_results)
        
         # 生成分析报告

        analysis_report = analyzer.generate_analysis_report(
            results_data, failure_patterns, performance_regressions, coverage_trends)
        
        # 4. 生成反馈和改进建议
        logger.info("正在生成反馈和改进建议...")
        
        # 生成改进建议
        suggestions = feedback_system.generate_improvement_suggestions(analysis_report)

        
         # 生成反馈报告

        feedback_report_path = feedback_system.generate_feedback_report(
            analysis_report, suggestions)
        
         # 5. 发送邮件通知（如果需要）

        if send_email and recipient_emails and feedback_report_path:
            logger.info("正在发送邮件通知...")

            feedback_system.send_email_notification(
                recipient_emails, feedback_report_path, analysis_report)
        
        # 6. 与开发流程集成
        logger.info("正在与开发流程集成...")
        tasks = feedback_system.integrate_with_development_workflow(suggestions)
        
        logger.info("测试结果处理完成!")
        logger.info(f"  - 可视化报告: {visualizer.reports_dir / 'visualization_report.html'}")
        logger.info(f"  - 分析报告: {analyzer.reports_dir / 'analysis_report.json'}")
        logger.info(f"  - 反馈报告: {feedback_report_path}")
        logger.info(f"  - 改进任务: {len(tasks)} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"处理测试结果时发生错误: {e}")
        return False


def main() -> None:
    """主函数"""

    parser = argparse.ArgumentParser(description='处理测试结果的完整流程')
    parser.add_argument('results_file', help='测试结果文件路径')
    parser.add_argument('--baseline', help='基线测试结果文件路径（用于性能回归检测）')
    parser.add_argument('--historical', nargs='*', help='历史测试结果文件列表（用于趋势分析）')
    parser.add_argument('--send-email', action='store_true', help='是否发送邮件通知')
    # 
# 
#     parser.add_argument('--recipients', nargs='*', help='邮件接收者列表')
#     
#     args = parser.parse_args()
#     
    success = process_test_results(
        results_file=args.results_file,
        baseline_file=args.baseline,
        historical_files=args.historical,
        send_email=args.send_email,
        recipient_emails=args.recipients
    )
    
    if success:
        logger.info("测试结果处理成功完成")
        sys.exit(0)
    else:
        logger.error("测试结果处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()