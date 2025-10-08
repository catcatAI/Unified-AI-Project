#!/usr/bin/env python3
"""
分析根目录Python脚本的分类和处理建议
确定哪些需要归档、哪些可以融合、哪些可以保留
"""

import os
import re
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class RootScriptAnalyzer:
    """根目录脚本分析器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.root_scripts = list(self.project_root.glob("*.py"))
        
        # 分类定义
        self.system_scripts = {  # 系统必需脚本
            'COMPLEXITY_ASSESSMENT_SYSTEM.py',
            'quick_complexity_check.py', 
            'enforce_no_simple_fixes.py',
            'quick_verify.py',
            'verify_progress.py'
        }
        
        self.simple_fix_patterns = [  # 简单修复脚本模式
            r'fix_.*\.py$',
            r'check_.*\.py$', 
            r'.*fix.*\.py$',
            r'.*repair.*\.py$',
            r'syntax.*\.py$',
            r'.*checker.*\.py$'
        ]
        
    def analyze_all_scripts(self) -> Dict:
        """分析所有根目录脚本"""
        print("🔍 开始分析根目录Python脚本...")
        print(f"📊 发现 {len(self.root_scripts)} 个Python脚本")
        print()
        
        categories = {
            'system_essential': [],      # 系统必需 - 保留
            'simple_fix_scripts': [],    # 简单修复 - 归档
            'fusion_candidates': [],     # 可融合 - 集成到统一系统
            'utility_scripts': [],       # 工具脚本 - 评估保留
            'obsolete_scripts': [],      # 废弃脚本 - 归档
            'unknown_scripts': []        # 未知类型 - 需要分析
        }
        
        for script_path in self.root_scripts:
            script_name = script_path.name
            
            # 跳过系统必需脚本
            if script_name in self.system_scripts:
                categories['system_essential'].append(script_name)
                continue
                
            # 分析脚本内容和特征
            analysis = self._analyze_script_content(script_path)
            
            # 分类判断
            category = self._categorize_script(script_name, analysis)
            categories[category].append({
                'name': script_name,
                'analysis': analysis
            })
        
        return categories
        
    def _analyze_script_content(self, script_path: Path) -> Dict:
        """分析单个脚本的内容和特征"""
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            # 基本统计
            analysis = {
                'total_lines': len(lines),
                'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
                'has_main': '__main__' in content,
                'has_functions': len(re.findall(r'^def\s+', content, re.MULTILINE)),
                'has_classes': len(re.findall(r'^class\s+', content, re.MULTILINE)),
                'has_imports': len(re.findall(r'^(import|from)\s+', content, re.MULTILINE)),
                'file_size': script_path.stat().st_size,
                'modified_time': script_path.stat().st_mtime
            }
            
            # 功能分析
            analysis['functionality'] = self._identify_functionality(content)
            analysis['complexity'] = self._assess_complexity(content)
            analysis['unified_system_compatible'] = self._check_unified_system_compatible(content)
            
            return analysis
            
        except Exception as e:
            return {
                'error': str(e),
                'total_lines': 0,
                'file_size': 0
            }
            
    def _identify_functionality(self, content: str) -> List[str]:
        """识别脚本功能类型"""
        functionality = []
        
        content_lower = content.lower()
        
        # 修复相关功能
        if any(keyword in content_lower for keyword in ['fix', 'repair', 'correct']):
            functionality.append('repair')
            
        # 检查相关功能  
        if any(keyword in content_lower for keyword in ['check', 'verify', 'validate']):
            functionality.append('check')
            
        # 语法相关
        if any(keyword in content_lower for keyword in ['syntax', 'indent', 'ast']):
            functionality.append('syntax')
            
        # 分析相关
        if any(keyword in content_lower for keyword in ['analyze', 'analysis', 'scan']):
            functionality.append('analysis')
            
        # 系统相关
        if any(keyword in content_lower for keyword in ['system', 'unified', 'comprehensive']):
            functionality.append('system')
            
        # 工具相关
        if any(keyword in content_lower for keyword in ['utility', 'tool', 'helper']):
            functionality.append('utility')
            
        return functionality
        
    def _assess_complexity(self, content: str) -> str:
        """评估脚本复杂度"""
        lines = content.split('\n')
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        if code_lines < 50:
            return "simple"
        elif code_lines < 200:
            return "medium"
        elif code_lines < 500:
            return "complex"
        else:
            return "mega"
            
    def _check_unified_system_compatible(self, content: str) -> bool:
        """检查是否与统一自动修复系统兼容"""
        # 检查是否有统一的错误处理、日志、配置等
        has_proper_structure = all([
            'def ' in content,  # 有函数定义
            'import' in content,  # 有导入
            len(content.split('\n')) > 20  # 不是太简单
        ])
        
        # 检查是否有不良做法
        has_bad_practices = any([
            'subprocess.run(' in content and 'python' in content,  # 调用其他Python脚本
            'subprocess' in content and 'python' in content,
            'glob(' in content and '*.py' in content,  # 批量处理Python文件
            're.sub(' in content and '.*' in content,  # 简单的全局替换
        ], shell=False, check=True)
        
        return has_proper_structure and not has_bad_practices
        
    def _categorize_script(self, script_name: str, analysis: Dict) -> str:
        """分类脚本"""
        if 'error' in analysis:
            return 'obsolete_scripts'
            
        functionality = analysis.get('functionality', [])
        complexity = analysis.get('complexity', 'simple')
        is_compatible = analysis.get('unified_system_compatible', False)
        
        # 简单修复脚本识别
        is_simple_fix = (
            any(re.match(pattern, script_name) for pattern in self.simple_fix_patterns) and
            complexity == 'simple' and
            not is_compatible
        )
        
        if is_simple_fix:
            return 'simple_fix_scripts'
            
        # 融合候选识别
        if ('repair' in functionality or 'syntax' in functionality) and is_compatible:
            return 'fusion_candidates'
            
        # 工具脚本识别
        if 'utility' in functionality or 'tool' in functionality:
            return 'utility_scripts'
            
        # 废弃脚本识别
        if complexity == 'simple' and len(functionality) <= 1:
            return 'obsolete_scripts'
            
        return 'unknown_scripts'
        
    def generate_recommendations(self, categories: Dict) -> List[str]:
        """生成处理建议"""
        recommendations = []
        
        # 系统必需脚本 - 保留
        if categories['system_essential']:
            recommendations.append(f"✅ 系统必需脚本（保留）: {len(categories['system_essential'])}个")
            for script in categories['system_essential']:
                recommendations.append(f"   - {script}: 保留，系统运行必需")
                
        # 简单修复脚本 - 归档
        if categories['simple_fix_scripts']:
            recommendations.append(f"🚨 简单修复脚本（必须归档）: {len(categories['simple_fix_scripts'])}个")
            for script_info in categories['simple_fix_scripts']:
                script = script_info['name']
                complexity = script_info['analysis']['complexity']
                recommendations.append(f"   - {script}: 归档到archived_fix_scripts/，规则简陋，复杂度{complexity}")
                
        # 可融合脚本 - 集成到统一系统
        if categories['fusion_candidates']:
            recommendations.append(f"🔄 可融合脚本（集成到统一系统）: {len(categories['fusion_candidates'])}个")
            for script_info in categories['fusion_candidates']:
                script = script_info['name']
                functionality = script_info['analysis']['functionality']
                recommendations.append(f"   - {script}: 融合到unified_auto_fix_system/modules/，功能:{',
                '.join(functionality)}")
                
        # 工具脚本 - 评估保留
        if categories['utility_scripts']:
            recommendations.append(f"🛠️ 工具脚本（评估保留）: {len(categories['utility_scripts'])}个")
            for script_info in categories['utility_scripts']:
                script = script_info['name']
                lines = script_info['analysis']['total_lines']
                recommendations.append(f"   - {script}: 评估是否保留，{lines}行")
                
        # 废弃脚本 - 归档
        if categories['obsolete_scripts']:
            recommendations.append(f"🗑️ 废弃脚本（归档）: {len(categories['obsolete_scripts'])}个")
            for script_info in categories['obsolete_scripts']:
                script = script_info['name']
                lines = script_info['analysis']['total_lines']
                recommendations.append(f"   - {script}: 归档到archived_fix_scripts/，过于简单({lines}行)")
                
        return recommendations
        
    def print_analysis_report(self, categories: Dict, recommendations: List[str]):
        """打印分析报告"""
        print("\n" + "="*80)
        print("🔍 根目录Python脚本分析报告")
        print("="*80)
        print(f"分析时间: {datetime.now()}")
        print(f"项目根目录: {self.project_root.absolute()}")
        print()
        
        # 分类统计
        print("📊 分类统计:")
        total_analyzed = sum(len(scripts) for scripts in categories.values())
        
        for category, scripts in categories.items():
            if scripts:
                category_names = {
                    'system_essential': '系统必需脚本',
                    'simple_fix_scripts': '简单修复脚本',
                    'fusion_candidates': '可融合脚本',
                    'utility_scripts': '工具脚本',
                    'obsolete_scripts': '废弃脚本',
                    'unknown_scripts': '未知脚本'
                }
                print(f"  {category_names.get(category, category)}: {len(scripts)}个")
        
        print(f"  📈 总计分析: {total_analyzed}个脚本")
        print()
        
        # 详细建议
        print("🎯 处理建议:")
        for rec in recommendations:
            print(f"  {rec}")
        
        print("\n" + "="*80)
        
        # 返回关键统计
        simple_fix_count = len(categories['simple_fix_scripts'])
        fusion_count = len(categories['fusion_candidates'])
        obsolete_count = len(categories['obsolete_scripts'])
        
        return {
            'simple_fix_scripts': simple_fix_count,
            'fusion_candidates': fusion_count, 
            'obsolete_scripts': obsolete_count,
            'total_analyzed': total_analyzed
        }


def main():
    """主函数"""
    analyzer = RootScriptAnalyzer()
    
    # 分析所有脚本
    categories = analyzer.analyze_all_scripts()
    
    # 生成建议
    recommendations = analyzer.generate_recommendations(categories)
    
    # 打印报告
    stats = analyzer.print_analysis_report(categories, recommendations)
    
    print(f"\n🎯 关键发现:")
    print(f"  🚨 需要归档的简单修复脚本: {stats['simple_fix_scripts']}个")
    print(f"  🔄 可融合到统一系统的脚本: {stats['fusion_candidates']}个") 
    print(f"  🗑️ 需要归档的废弃脚本: {stats['obsolete_scripts']}个")
    
    # 总体建议
    print(f"\n📋 总体建议:")
    if stats['simple_fix_scripts'] > 0:
        print(f"  ⚠️  发现{stats['simple_fix_scripts']}个简单修复脚本，建议立即归档")
        
    if stats['fusion_candidates'] > 0:
        print(f"  🔄 发现{stats['fusion_candidates']}个可融合脚本，建议集成到统一修复系统")
        
    if stats['obsolete_scripts'] > 0:
        print(f"  🧹 发现{stats['obsolete_scripts']}个废弃脚本，建议归档清理")
        
    print(f"\n💡 建议优先级:")
    print(f"  1. 🚨 立即归档简单修复脚本（防止继续使用）")
    print(f"  2. 🔄 逐步融合有用脚本到统一系统")
    print(f"  3. 🧹 清理归档废弃脚本（保持整洁）")


if __name__ == "__main__":
    main()