#!/usr/bin/env python3
"""
项目复杂度评估与偏差预防系统
每次执行修复步骤前必须评估项目复杂度和潜在偏差
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import ast
import re

@dataclass
class ComplexityMetrics:
    """复杂度指标"""
    total_files: int = 0
    python_files: int = 0
    total_lines: int = 0
    total_size_mb: float = 0.0
    max_file_lines: int = 0
    avg_file_lines: float = 0.0
    # 语法复杂度
    syntax_errors: int = 0
    import_complexity: int = 0
    class_count: int = 0
    function_count: int = 0
    
    # 架构复杂度
    directory_depth: int = 0
    circular_imports: int = 0
    interdependencies: int = 0
    
    # 历史复杂度
    git_commits: int = 0
    active_branches: int = 0
    merge_conflicts: int = 0

class ProjectComplexityAssessment:
    """项目复杂度评估系统"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.assessment_file = self.project_root / ".complexity_assessment.json"
        self.thresholds = {
            "simple": {"max_files": 100, "max_lines": 10000, "max_errors": 10},
            "medium": {"max_files": 500, "max_lines": 50000, "max_errors": 100},
            "complex": {"max_files": 2000, "max_lines": 200000, "max_errors": 500},
            "mega": {"max_files": float('inf'), "max_lines": float('inf'), "max_errors": float('inf')}
        }
        
    def assess_project_complexity(self) -> Tuple[ComplexityMetrics, str]:
        """评估项目整体复杂度"""
        print("🔍 开始项目复杂度评估...")
        metrics = ComplexityMetrics()
        
        # 基础文件统计
        for root, dirs, files in os.walk(self.project_root):
            # 跳过不需要的目录
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.venv']):
                continue
                
            metrics.total_files += len(files)
            
            # 计算目录深度
            rel_path = Path(root).relative_to(self.project_root)
            depth = len(rel_path.parts) if rel_path != Path('.') else 0
            metrics.directory_depth = max(metrics.directory_depth, depth)

            for file in files:
                file_path = Path(root) / file
                
                if file.endswith('.py'):
                    metrics.python_files += 1
                    file_metrics = self._analyze_python_file(file_path)
                    metrics.total_lines += file_metrics['lines']
                    metrics.max_file_lines = max(metrics.max_file_lines, file_metrics['lines'])
                    metrics.class_count += file_metrics['classes']
                    metrics.function_count += file_metrics['functions']
                    metrics.syntax_errors += file_metrics['syntax_errors']
                    
                elif file.endswith(('.md', '.txt', '.json', '.yaml', '.yml')):
                    # 分析文档和配置文件
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        metrics.total_lines += len(content.split('\n'))
                    except:
                        pass
        
        # 计算平均值
        if metrics.python_files > 0:
            metrics.avg_file_lines = metrics.total_lines / metrics.python_files
        # 分析架构复杂度
        arch_metrics = self._analyze_architecture()
        metrics.import_complexity = arch_metrics['import_complexity']
        metrics.circular_imports = arch_metrics['circular_imports']
        metrics.interdependencies = arch_metrics['interdependencies']
        
        # Git历史分析
        git_metrics = self._analyze_git_history()
        metrics.git_commits = git_metrics['commits']
        metrics.active_branches = git_metrics['branches']
        metrics.merge_conflicts = git_metrics['conflicts']
        
        # 计算总大小
        metrics.total_size_mb = self._calculate_total_size()
        
        # 确定复杂度等级
        complexity_level = self._determine_complexity_level(metrics)
        
        return metrics, complexity_level
        
    def _analyze_python_file(self, file_path: Path) -> Dict:
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            # 语法分析
            syntax_errors = 0
            try:
                ast.parse(content)
            except SyntaxError:
                syntax_errors += 1
                
            # AST分析
            try:
                tree = ast.parse(content)
                classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            except:
                classes = functions = 0
                
            return {
                'lines': len(lines),
                'classes': classes,
                'functions': functions,
                'syntax_errors': syntax_errors
            }
        except Exception:
            return {'lines': 0, 'classes': 0, 'functions': 0, 'syntax_errors': 0}
            
    def _analyze_architecture(self) -> Dict:
        """分析架构复杂度"""
        import_complexity = 0
        circular_imports = 0
        interdependencies = 0
        
        # 分析导入复杂度(简化版本)
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                # 计算导入语句数量
                imports = len(re.findall(r'^(import|from)\s+', content, re.MULTILINE))
                import_complexity += imports
                
                # 检测循环导入的潜在风险(简化检测)
                if 'from .' in content and 'import' in content:
                    interdependencies += 1
                    
            except Exception:
                continue
                
        return {
            'import_complexity': import_complexity,
            'circular_imports': circular_imports,
            'interdependencies': interdependencies
        }
        
    def _analyze_git_history(self) -> Dict:
        """分析Git历史复杂度"""
        try:
            # 获取提交数量
            result = os.popen('git rev-list --count HEAD 2>/dev/null').read().strip()
            commits = int(result) if result and result.isdigit() else 0
            # 获取分支数量
            result = os.popen('git branch -a | wc -l 2>/dev/null').read().strip()
            branches = int(result) if result and result.isdigit() else 0
            # 获取合并冲突历史(简化)
            conflicts = 0
            
            return {
                'commits': commits,
                'branches': branches,
                'conflicts': conflicts
            }
        except:
            return {'commits': 0, 'branches': 0, 'conflicts': 0}
            
    def _calculate_total_size(self) -> float:
        """计算项目总大小(MB)"""
        total_size = 0
        for root, dirs, files in os.walk(self.project_root):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules']):
                continue
            for file in files:
                try:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
                except:
                    continue
        return total_size / (1024 * 1024)  # 转换为MB
        
    def _determine_complexity_level(self, metrics: ComplexityMetrics) -> str:
        """确定复杂度等级"""
        # 多维度评估复杂度
        scores = {
            'files': min(metrics.total_files / 1000, 1.0),
            'lines': min(metrics.total_lines / 100000, 1.0),
            'errors': min(metrics.syntax_errors / 1000, 1.0),
            'depth': min(metrics.directory_depth / 10, 1.0),
            'git': min(metrics.git_commits / 10000, 1.0)
        }
        
        # 计算综合复杂度分数
        total_score = sum(scores.values()) / len(scores)
        
        if total_score < 0.2:
            return "simple"
        elif total_score < 0.5:
            return "medium"  
        elif total_score < 0.8:
            return "complex"
        else:
            return "mega"
            
    def evaluate_repair_approach(self, target_path: str = None) -> Dict:
        """评估修复方法的适用性"""
        print("🔍 开始修复方法适用性评估...")
        
        metrics, complexity_level = self.assess_project_complexity()
        
        # 保存评估结果
        assessment = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics.__dict__,
            'complexity_level': complexity_level,
            'recommendations': []
        }
        
        # 基于复杂度给出建议
        recommendations = []
        warnings = []
        
        if complexity_level == "simple":
            recommendations.append("✅ 项目复杂度低,可以使用统一修复系统")
            recommendations.append("✅ 可以一次性处理整个项目")
            
        elif complexity_level == "medium":
            recommendations.append("⚠️ 项目复杂度中等,建议分批处理")
            recommendations.append("✅ 使用统一修复系统,但建议按目录分批")
            recommendations.append("✅ 每批处理后都要验证效果")
            
        elif complexity_level == "complex":
            warnings.append("🚨 项目复杂度高,禁止使用简单修复脚本")
            recommendations.append("🚨 必须使用统一修复系统的分批模式")
            recommendations.append("🚨 每次只能处理特定目录或文件类型")
            recommendations.append("🚨 必须进行干运行验证后再实际修复")
            
        else:  # mega
            warnings.append("💀 项目为巨型复杂度,修复需要极端谨慎")
            recommendations.append("💀 禁止任何自动化修复,必须人工设计修复方案")
            recommendations.append("💀 必须建立完整的测试验证体系")
            recommendations.append("💀 建议分模块、分阶段、小步快跑的方式")
            
        # 特别警告
        if metrics.syntax_errors > self.thresholds[complexity_level]["max_errors"]:
            warnings.append(f"❌ 语法错误数量({metrics.syntax_errors})超过{complexity_level}级别阈值")
            
        if metrics.max_file_lines > 1000:
            warnings.append(f"⚠️  存在超大文件({metrics.max_file_lines}行),需要特殊处理")
            
        if metrics.circular_imports > 10:
            warnings.append(f"⚠️  检测到循环导入问题,修复时需要特别注意")
            
        assessment['recommendations'] = recommendations
        assessment['warnings'] = warnings
        assessment['allowed_approaches'] = self._get_allowed_approaches(complexity_level)
        assessment['forbidden_approaches'] = self._get_forbidden_approaches(complexity_level)
        
        # 保存到文件
        with open(self.assessment_file, 'w', encoding='utf-8') as f:
            json.dump(assessment, f, indent=2, default=str)
            
        return assessment
        
    def _get_allowed_approaches(self, complexity_level: str) -> List[str]:
        """获取允许的修复方法"""
        approaches = {
            "simple": [
                "统一自动修复系统 - 全项目处理",
                "统一自动修复系统 - 分批处理",
                "统一自动修复系统 - 单文件处理"
            ],
            "medium": [
                "统一自动修复系统 - 分批处理", 
                "统一自动修复系统 - 单目錄处理",
                "统一自动修复系统 - 单文件处理"
            ],
            "complex": [
                "统一自动修复系统 - 单目录处理",
                "统一自动修复系统 - 单文件处理",
                "统一自动修复系统 - 干运行验证"
            ],
            "mega": [
                "人工分析 + 统一系统干运行",
                "分模块统一修复",
                "小步快跑验证模式"
            ]
        }
        return approaches.get(complexity_level, [])
        
    def _get_forbidden_approaches(self, complexity_level: str) -> List[str]:
        """获取禁止的修复方法"""
        forbidden = {
            "simple": [
                "根目录简单修复脚本",
                "正则表达式批量替换",
                "无备份的直接修改"
            ],
            "medium": [
                "根目录简单修复脚本",
                "正则表达式批量替换", 
                "无范围限制的修复"
            ],
            "complex": [
                "根目录简单修复脚本",
                "正则表达式批量替换",
                "无范围限制的修复",
                "无验证的批量修复",
                "一次性全项目修复"
            ],
            "mega": [
                "任何自动化修复",
                "根目录简单修复脚本",
                "正则表达式批量替换",
                "无范围限制的修复",
                "无验证的批量修复",
                "一次性全项目修复",
                "无人工审核的修复"
            ]
        }
        return forbidden.get(complexity_level, [])
        
    def print_assessment_report(self, assessment: Dict):
        """打印评估报告"""
        print("\n" + "="*80)
        print("🔍 项目复杂度评估与修复方法建议报告")
        print("="*80)
        print(f"评估时间: {assessment['timestamp']}")
        print(f"复杂度等级: {assessment['complexity_level'].upper()}")
        print()
        
        metrics = assessment['metrics']
        print("📊 复杂度指标:")
        print(f"  📁 总文件数: {metrics['total_files']}")
        print(f"  🐍 Python文件: {metrics['python_files']}")
        print(f"  📏 总行数: {metrics['total_lines']}")
        print(f"  💾 总大小: {metrics['total_size_mb']:.1f} MB")
        print(f"  📐 最大文件: {metrics['max_file_lines']} 行")
        print(f"  📊 平均文件: {metrics['avg_file_lines']:.0f} 行")
        print(f"  ❌ 语法错误: {metrics['syntax_errors']}")
        print(f"  📂 目录深度: {metrics['directory_depth']}")
        print(f"  🔗 Git提交: {metrics['git_commits']}")
        print()
        
        if assessment.get('warnings'):
            print("⚠️  警告:")
            for warning in assessment['warnings']:
                print(f"  {warning}")
            print()
            
        print("✅ 推荐修复方法:")
        for rec in assessment['recommendations']:
            print(f"  {rec}")
        print()
        
        print("🎯 允许的修复方法:")
        for approach in assessment['allowed_approaches']:
            print(f"  ✅ {approach}")
        print()
        
        print("🚫 禁止的修复方法:")
        for approach in assessment['forbidden_approaches']:
            print(f"  ❌ {approach}")
        print()
        
        print("="*80)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."
        
    assessor = ProjectComplexityAssessment(project_path)
    
    # 执行评估
    assessment = assessor.evaluate_repair_approach()
    
    # 打印报告
    assessor.print_assessment_report(assessment)
    
    # 返回复杂度等级和关键指标
    complexity_level = assessment['complexity_level']
    syntax_errors = assessment['metrics']['syntax_errors']
    
    print(f"🎯 执行建议:")
    if complexity_level in ["complex", "mega"]:
        print(f"  🚨 当前项目为{complexity_level}级别复杂度")
        print(f"  🚨 语法错误数量: {syntax_errors}")
        print(f"  🚨 必须使用统一自动修复系统的分批模式")
        print(f"  🚨 禁止任何简单修复脚本的使用")
        sys.exit(1)  # 返回错误码,阻止简单修复
    else:
        print(f"  ✅ 当前项目為{complexity_level}级别复杂度")
        print(f"  ✅ 可以使用统一自动修复系统")
        sys.exit(0)  # 返回成功码,允许继续


if __name__ == "__main__":
    main()