#!/usr/bin/env python3
"""
分析修复报告的脚本
"""

import json
from pathlib import Path

def analyze_fix_report():
    """分析修复报告"""
    # 查找最新的修复报告
    reports_dir = Path("unified_fix_reports")
    if not reports_dir.exists():
        print("修复报告目录不存在")
        return
    
    # 获取最新的报告文件
    report_files = list(reports_dir.glob("fix_report_*.json"))
    if not report_files:
        print("未找到修复报告文件")
        return
    
    # 按修改时间排序，获取最新的报告
    latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
    print(f"分析报告文件: {latest_report}")
    
    # 读取报告
    try:
        with open(latest_report, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        print(f"读取报告文件失败: {e}")
        return
    
    # 分析报告内容
    print("\n=== 修复报告分析 ===")
    
    # 基本信息
    timestamp = report.get("timestamp", "未知")
    project_root = report.get("project_root", "未知")
    print(f"报告时间: {timestamp}")
    print(f"项目根目录: {project_root}")
    
    # 分析结果
    analysis_result = report.get("analysis_result", {})
    statistics = analysis_result.get("statistics", {})
    print(f"\n=== 问题统计 ===")
    total_issues = sum(statistics.values())
    print(f"总问题数: {total_issues}")
    
    for fix_type, count in statistics.items():
        print(f"  {fix_type}: {count}")
    
    # 修复结果
    fix_results = report.get("fix_results", {})
    print(f"\n=== 修复结果 ===")
    print(f"修复模块数: {len(fix_results)}")
    
    success_count = 0
    failed_count = 0
    partial_count = 0
    
    for fix_type, result in fix_results.items():
        status = result.get("status", "未知")
        issues_found = result.get("issues_found", 0)
        issues_fixed = result.get("issues_fixed", 0)
        
        if status == "FixStatus.SUCCESS":
            success_count += 1
            print(f"  ✓ {fix_type}: 成功修复 {issues_fixed}/{issues_found} 个问题")
        elif status == "FixStatus.PARTIAL_SUCCESS":
            partial_count += 1
            print(f"  ⚠ {fix_type}: 部分成功修复 {issues_fixed}/{issues_found} 个问题")
        elif status == "FixStatus.FAILED":
            failed_count += 1
            print(f"  ✗ {fix_type}: 修复失败 ({issues_found} 个问题)")
        else:
            print(f"  ? {fix_type}: {status} ({issues_found} 个问题)")
    
    print(f"\n=== 修复统计 ===")
    print(f"  成功: {success_count}")
    print(f"  部分成功: {partial_count}")
    print(f"  失败: {failed_count}")
    
    # 错误信息
    errors = report.get("errors", [])
    if errors:
        print(f"\n=== 错误信息 ===")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... 还有 {len(errors) - 5} 个错误")

if __name__ == "__main__":
    analyze_fix_report()