#!/usr/bin/env python3
"""
项目真实有效代码行数统计工具
只统计核心功能代码，排除重复、不完善的脚本
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class CodeLineCounter:
    """代码行数统计器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.excluded_patterns = [
            # 测试文件
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests/.*',
            
            # 备份和归档
            r'.*backup.*',
            r'.*archive.*',
            r'.*old.*',
            r'.*temp.*',
            r'.*tmp.*',
            
            # 重复的修复脚本
            r'.*fix.*\.py$',
            r'.*repair.*\.py$',
            r'.*heal.*\.py$',
            
            # 报告和文档
            r'.*\.md$',
            r'.*\.txt$',
            r'.*\.json$',
            r'.*\.log$',
            
            # 构建产物
            r'.*__pycache__.*',
            r'.*\.pyc$',
            r'.*\.pyo$',
            
            # 根目录临时脚本
            r'^[a-z]{3}\.md$',  # aaa.md, kkk.md等
            r'^debug_.*\.py$',
            r'^test_.*\.py$',
            
            # 配置文件
            r'.*config.*\.json$',
            r'.*\.yaml$',
            r'.*\.yml$',
        ]
        
        self.core_modules = {
            # 核心应用
            'apps/backend/src/ai/agents/',
            'apps/backend/src/ai/memory/',
            'apps/backend/src/ai/concept_models/',
            'apps/backend/src/ai/ops/',
            'apps/backend/src/core/',
            'apps/backend/src/api/',
            'apps/backend/src/managers/',
            
            # 训练系统
            'training/',
            
            # 工具系统 - 只统计核心工具
            'tools/cli/',
            'tools/ai/',
            
            # 共享包
            'packages/cli/',
            'packages/ui/',
            
            # 核心脚本
            'unified_system_manager.py',
            'main.py',
        }
        
        self.excluded_files = {
            # 根目录重复脚本
            'simple_integrity_check.py',
            'project_integrity_check.py',
            'check_python_env.py',
            'daily_maintenance.py',
            
            # 重复的修复脚本
            'comprehensive_repair_test.py',
            'complete_system_recovery.py',
            'execute_project_repair.py',
            'execute_repair_now.py',
            'enhanced_unified_fix_system.py',
        }
        
    def is_excluded(self, file_path: Path) -> bool:
        """检查文件是否应该排除"""
        relative_path = file_path.relative_to(self.project_root)
        path_str = str(relative_path).replace('\\', '/')
        
        # 检查文件名
        if file_path.name in self.excluded_files:
            return True
        
        # 检查排除模式
        for pattern in self.excluded_patterns:
            if re.search(pattern, path_str):
                return True
        
        # 检查是否在核心模块中
        is_core = False
        for core_module in self.core_modules:
            if path_str.startswith(core_module):
                is_core = True
                break
        
        # 如果不在核心模块中，且不是核心脚本，则排除
        if not is_core and not path_str.startswith('apps/backend/'):
            return True
        
        return False
    
    def count_lines_in_file(self, file_path: Path) -> Tuple[int, int, int]:
        """统计文件中的代码行数"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except:
            return 0, 0, 0
        
        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 空行
            if not stripped:
                blank_lines += 1
                continue
            
            # 多行注释处理
            if '"""' in stripped or "'''" in stripped:
                if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
                    in_multiline_comment = not in_multiline_comment
            
            # 注释行
            if in_multiline_comment or stripped.startswith('#') or stripped.startswith('//'):
                comment_lines += 1
                continue
            
            # 代码行
            code_lines += 1
        
        return code_lines, comment_lines, blank_lines
    
    def scan_project(self) -> Dict[str, Dict]:
        """扫描项目并统计代码行数"""
        results = defaultdict(lambda: {
            'files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'files_list': []
        })
        
        # 扫描所有Python文件
        for py_file in self.project_root.rglob('*.py'):
            if self.is_excluded(py_file):
                continue
            
            relative_path = py_file.relative_to(self.project_root)
            path_str = str(relative_path).replace('\\', '/')
            
            # 确定文件属于哪个模块
            module_name = 'other'
            for core_module in self.core_modules:
                if path_str.startswith(core_module):
                    module_name = core_module.rstrip('/')
                    break
            
            # 统计行数
            code_lines, comment_lines, blank_lines = self.count_lines_in_file(py_file)
            total_lines = code_lines + comment_lines + blank_lines
            
            if total_lines > 0:  # 只统计非空文件
                results[module_name]['files'] += 1
                results[module_name]['total_lines'] += total_lines
                results[module_name]['code_lines'] += code_lines
                results[module_name]['comment_lines'] += comment_lines
                results[module_name]['blank_lines'] += blank_lines
                results[module_name]['files_list'].append(str(relative_path))
        
        return dict(results)
    
    def generate_report(self, results: Dict[str, Dict]) -> str:
        """生成统计报告"""
        report = []
        report.append("# 项目真实有效代码行数统计报告")
        report.append("")
        report.append(f"**统计时间**: 2025年10月14日")
        report.append(f"**项目根目录**: {self.project_root}")
        report.append("")
        report.append("## 统计说明")
        report.append("- 只统计核心功能代码")
        report.append("- 排除测试文件、备份文件、重复脚本")
        report.append("- 排除不完善的修复脚本")
        report.append("- 只包含生产就绪的核心模块")
        report.append("")
        
        # 总计
        total_files = sum(r['files'] for r in results.values())
        total_lines = sum(r['total_lines'] for r in results.values())
        total_code_lines = sum(r['code_lines'] for r in results.values())
        total_comment_lines = sum(r['comment_lines'] for r in results.values())
        total_blank_lines = sum(r['blank_lines'] for r in results.values())
        
        report.append("## 总体统计")
        report.append(f"- **文件总数**: {total_files}")
        report.append(f"- **总行数**: {total_lines:,}")
        report.append(f"- **代码行数**: {total_code_lines:,}")
        report.append(f"- **注释行数**: {total_comment_lines:,}")
        report.append(f"- **空行数**: {total_blank_lines:,}")
        report.append(f"- **代码行占比**: {total_code_lines/total_lines*100:.1f}%")
        report.append("")
        
        # 按模块统计
        report.append("## 按模块统计")
        report.append("")
        
        # 按代码行数排序
        sorted_results = sorted(results.items(), key=lambda x: x[1]['code_lines'], reverse=True)
        
        for module, stats in sorted_results:
            if stats['files'] > 0:
                report.append(f"### {module}")
                report.append(f"- 文件数: {stats['files']}")
                report.append(f"- 代码行数: {stats['code_lines']:,}")
                report.append(f"- 总行数: {stats['total_lines']:,}")
                report.append(f"- 代码行占比: {stats['code_lines']/stats['total_lines']*100:.1f}%")
                report.append("")
        
        # 核心系统详细统计
        report.append("## 核心系统详细统计")
        report.append("")
        
        core_systems = {
            'AI代理系统': ['apps/backend/src/ai/agents/'],
            'AI运维系统': ['apps/backend/src/ai/ops/'],
            '记忆系统': ['apps/backend/src/ai/memory/'],
            '概念模型': ['apps/backend/src/ai/concept_models/'],
            '核心服务': ['apps/backend/src/core/', 'apps/backend/src/api/'],
            '训练系统': ['training/'],
            '管理系统': ['apps/backend/src/managers/'],
        }
        
        for system_name, modules in core_systems.items():
            system_files = 0
            system_code_lines = 0
            system_total_lines = 0
            
            for module in modules:
                if module.rstrip('/') in results:
                    stats = results[module.rstrip('/')]
                    system_files += stats['files']
                    system_code_lines += stats['code_lines']
                    system_total_lines += stats['total_lines']
            
            if system_files > 0:
                report.append(f"### {system_name}")
                report.append(f"- 文件数: {system_files}")
                report.append(f"- 代码行数: {system_code_lines:,}")
                report.append(f"- 总行数: {system_total_lines:,}")
                report.append(f"- 占总代码比例: {system_code_lines/total_code_lines*100:.1f}%")
                report.append("")
        
        # 代码质量分析
        report.append("## 代码质量分析")
        report.append("")
        comment_ratio = total_comment_lines / total_code_lines if total_code_lines > 0 else 0
        report.append(f"- **注释率**: {comment_ratio*100:.1f}% (注释行数/代码行数)")
        report.append(f"- **平均文件大小**: {total_code_lines/total_files:.0f} 行/文件")
        
        # 质量评级
        if comment_ratio >= 0.3:
            quality = "优秀 (注释充分)"
        elif comment_ratio >= 0.2:
            quality = "良好 (注释适中)"
        elif comment_ratio >= 0.1:
            quality = "一般 (注释偏少)"
        else:
            quality = "较差 (注释不足)"
        
        report.append(f"- **代码质量**: {quality}")
        report.append("")
        
        return "\n".join(report)

def main():
    """主函数"""
    project_root = Path(__file__).parent
    counter = CodeLineCounter(project_root)
    
    print("开始统计项目真实有效代码行数...")
    results = counter.scan_project()
    report = counter.generate_report(results)
    
    # 保存报告
    report_file = project_root / "REAL_CODE_LINES_COUNT_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"统计完成！报告已保存到: {report_file}")
    
    # 打印简要结果
    total_files = sum(r['files'] for r in results.values())
    total_code_lines = sum(r['code_lines'] for r in results.values())
    total_lines = sum(r['total_lines'] for r in results.values())
    
    print(f"\n=== 简要统计结果 ===")
    print(f"核心文件数: {total_files}")
    print(f"真实代码行数: {total_code_lines:,}")
    print(f"代码行占比: {total_code_lines/total_lines*100:.1f}%")

if __name__ == "__main__":
    main()