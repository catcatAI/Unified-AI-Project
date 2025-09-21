#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试结果反馈系统
用于根据测试结果生成反馈并提供改进建议
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytest
import uuid

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DevelopmentTask:
    """开发任务类"""
    def __init__(self, task_id: str, title: str, description: str, priority: str):
        self.id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.status = "pending"

class TestResultFeedbackSystem:
    """测试结果反馈系统"""
    
    def __init__(self, results_dir: str = "test_results", reports_dir: str = "test_reports", templates_dir: str = "templates"):
        """
        初始化测试结果反馈系统
        
        Args:
            results_dir: 测试结果目录
            reports_dir: 报告输出目录
            templates_dir: 模板目录
        """
        self.results_dir = Path(results_dir)
        self.reports_dir = Path(reports_dir)
        self.templates_dir = Path(templates_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
    def generate_improvement_suggestions(self, analysis_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据分析报告生成改进建议
        
        Args:
            analysis_report: 分析报告
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 分析失败模式建议
        failure_analysis = analysis_report.get('failure_analysis', [])
        for failure in failure_analysis:
            suggestions.append({
                'type': 'failure_pattern',
                'title': f'处理"{failure["pattern"]}"失败模式',
                'description': f'检测到{failure["count"]}个"{failure["pattern"]}"相关的失败测试',
                'priority': 'high' if failure['count'] > 5 else 'medium',
                'affected_tests': failure['affected_tests']
            })
        
        # 性能回归建议
        performance_regressions = analysis_report.get('performance_regressions', [])
        for regression in performance_regressions:
            suggestions.append({
                'type': 'performance_regression',
                'title': f'优化{regression["test_name"]}性能',
                'description': f'性能下降{regression["regression_ratio"]*100:.1f}%，当前时间{regression["current_time"]:.4f}s',
                'priority': 'high' if regression['regression_ratio'] > 0.5 else 'medium',
                'test_name': regression['test_name']
            })
        
        # 整体质量建议
        pass_rate = analysis_report.get('summary', {}).get('pass_rate', 0)
        if pass_rate < 0.9:
            suggestions.append({
                'type': 'overall_quality',
                'title': '提高测试通过率',
                'description': f'当前通过率{pass_rate*100:.1f}%，低于90%的目标',
                'priority': 'high',
                'recommendation': '优先修复失败的测试用例'
            })
        
        return suggestions
    
    def generate_feedback_report(self, analysis_report: Dict[str, Any], 
                               suggestions: List[Dict[str, Any]],
                               report_file: str = "feedback_report.html") -> Path:
        """
        生成反馈报告
        
        Args:
            analysis_report: 分析报告
            suggestions: 改进建议
            report_file: 报告文件名
            
        Returns:
            报告文件路径
        """
        # 生成HTML报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试结果反馈报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #333;
        }}
        .summary-card {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .suggestion-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .high-priority {{
            border-left: 5px solid #dc3545;
        }}
        .medium-priority {{
            border-left: 5px solid #ffc107;
        }}
        .low-priority {{
            border-left: 5px solid #28a745;
        }}
        .priority-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .badge-high {{
            background-color: #dc3545;
            color: white;
        }}
        .badge-medium {{
            background-color: #ffc107;
            color: black;
        }}
        .badge-low {{
            background-color: #28a745;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>测试结果反馈报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-card">
            <h2>测试摘要</h2>
            <p>总测试数: {analysis_report.get('summary', {}).get('total_tests', 0)}</p>
            <p>通过测试数: {analysis_report.get('summary', {}).get('passed_tests', 0)}</p>
            <p>失败测试数: {analysis_report.get('summary', {}).get('failed_tests', 0)}</p>
            <p>通过率: {analysis_report.get('summary', {}).get('pass_rate', 0)*100:.1f}%</p>
        </div>
        
        <h2>改进建议</h2>
        """
        
        # 添加改进建议
        for suggestion in suggestions:
            priority_class = f"badge-{suggestion['priority']}"
            card_class = f"{suggestion['priority']}-priority"
            html_content += f"""
        <div class="suggestion-card {card_class}">
            <h3>{suggestion['title']}</h3>
            <p>{suggestion['description']}</p>
            <span class="priority-badge {priority_class}">{suggestion['priority'].upper()} PRIORITY</span>
        </div>
            """
        
        html_content += """
    </div>
</body>
</html>
        """
        
        # 保存报告
        report_path = self.reports_dir / report_file
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"反馈报告已保存到: {report_path}")
        except Exception as e:
            logger.error(f"保存反馈报告失败: {e}")
        
        return report_path
    
    def integrate_with_development_workflow(self, suggestions: List[Dict[str, Any]]) -> List[DevelopmentTask]:
        """
        将建议集成到开发流程中
        
        Args:
            suggestions: 改进建议
            
        Returns:
            开发任务列表
        """
        tasks = []
        
        for suggestion in suggestions:
            task_id = str(uuid.uuid4())[:8]
            
            if suggestion['type'] == 'failure_pattern':
                task = DevelopmentTask(
                    task_id=task_id,
                    title=suggestion['title'],
                    description=suggestion['description'],
                    priority=suggestion['priority']
                )
            elif suggestion['type'] == 'performance_regression':
                task = DevelopmentTask(
                    task_id=task_id,
                    title=suggestion['title'],
                    description=suggestion['description'],
                    priority=suggestion['priority']
                )
            elif suggestion['type'] == 'overall_quality':
                task = DevelopmentTask(
                    task_id=task_id,
                    title=suggestion['title'],
                    description=suggestion['description'],
                    priority=suggestion['priority']
                )
            else:
                continue
            
            tasks.append(task)
        
        return tasks


# 添加pytest标记，防止被误认为测试类
TestResultFeedbackSystem.__test__ = False


def main():
    """主函数"""
    feedback_system = TestResultFeedbackSystem()
    
    # 示例使用方式
    # 加载测试结果
    # results = feedback_system.load_test_results("latest_test_results.json")
    
    # 生成反馈报告
    # feedback_report = feedback_system.generate_feedback_report(results)
    
    logger.info("测试结果反馈系统已准备就绪")

if __name__ == "__main__":
    main()