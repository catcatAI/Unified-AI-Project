#!/usr/bin/env python3
"""
重复功能分析器
扫描Unified AI Project中的重复功能模块和相似代码实现
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import difflib

class DuplicateAnalyzer:
    def __init__(self):
        self.function_patterns = defaultdict(list)
        self.class_definitions = defaultdict(list)
        self.import_patterns = defaultdict(list)
        self.file_contents = {}
        self.similarity_threshold = 0.8
        
    def scan_project(self, root_path: str) -> Dict:
        """扫描整个项目"""
        root = Path(root_path)
        python_files = list(root.rglob("*.py"))
        
        print(f"扫描 {len(python_files)} 个Python文件...")
        
        # 限制分析的文件数量，优先分析关键目录
        key_dirs = ['apps', 'tools', 'training', 'scripts']
        priority_files = []
        other_files = []
        
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
                
            # 检查是否在关键目录中
            in_key_dir = any(key_dir in str(py_file) for key_dir in key_dirs)
            if in_key_dir or py_file.name.startswith(('check_', 'test_', 'fix_', 'repair', 'enhanced')):
                priority_files.append(py_file)
            else:
                other_files.append(py_file)
        
        # 只分析优先级文件和前1000个其他文件
        files_to_analyze = priority_files + other_files[:1000]
        print(f"实际分析 {len(files_to_analyze)} 个文件（优先级 + 前1000个）...")
        
        # 第一步：收集所有函数和类定义
        for i, py_file in enumerate(files_to_analyze):
            if i % 100 == 0:
                print(f"进度: {i}/{len(files_to_analyze)} 文件已分析")
                
            try:
                content = py_file.read_text(encoding='utf-8')
                self.file_contents[str(py_file)] = content
                self._analyze_file(str(py_file), content)
            except Exception as e:
                print(f"警告: 无法读取文件 {py_file}: {e}")
        
        # 第二步：分析重复模式
        return self._analyze_duplicates()
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """跳过不应该分析的文件"""
        skip_patterns = [
            '__pycache__', '.git', 'venv/', 'env/', 'node_modules/',
            '.pytest_cache', 'dist/', 'build/', '*.egg-info/'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: str, content: str):
        """分析单个文件"""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._analyze_function(file_path, node)
                elif isinstance(node, ast.ClassDef):
                    self._analyze_class(file_path, node)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._analyze_import(file_path, node)
                    
        except SyntaxError:
            pass  # 跳过语法错误的文件
    
    def _analyze_function(self, file_path: str, func_node: ast.FunctionDef):
        """分析函数定义"""
        func_name = func_node.name
        
        # 提取函数签名
        args = [arg.arg for arg in func_node.args.args]
        signature = f"{func_name}({', '.join(args)})"
        
        # 提取函数体的前几行作为模式
        if func_node.body:
            body_start = self._get_node_source(func_node.body[:3]) if len(func_node.body) > 3 else self._get_node_source(func_node.body)
        else:
            body_start = ""
            
        pattern = {
            'file': file_path,
            'name': func_name,
            'signature': signature,
            'args': args,
            'body_start': body_start,
            'line_num': func_node.lineno
        }
        
        self.function_patterns[func_name].append(pattern)
    
    def _analyze_class(self, file_path: str, class_node: ast.ClassDef):
        """分析类定义"""
        class_name = class_node.name
        
        # 提取方法
        methods = []
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
        
        pattern = {
            'file': file_path,
            'name': class_name,
            'methods': methods,
            'line_num': class_node.lineno,
            'bases': [self._get_name(base) for base in class_node.bases]
        }
        
        self.class_definitions[class_name].append(pattern)
    
    def _analyze_import(self, file_path: str, import_node):
        """分析导入语句"""
        if isinstance(import_node, ast.Import):
            for alias in import_node.names:
                self.import_patterns[alias.name].append(file_path)
        elif isinstance(import_node, ast.ImportFrom):
            module = import_node.module or ''
            for alias in import_node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                self.import_patterns[full_name].append(file_path)
    
    def _get_name(self, node):
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_node_source(self, nodes):
        """获取节点源码（简化版）"""
        # 这里简化处理，实际应该使用ast.get_source_segment
        return str(nodes)
    
    def _analyze_duplicates(self) -> Dict:
        """分析重复模式"""
        results = {
            'duplicate_functions': [],
            'duplicate_classes': [],
            'similar_files': [],
            'import_duplicates': [],
            'repair_systems': [],
            'check_scripts': [],
            'agent_managers': []
        }
        
        print("分析重复模式...")
        
        # 1. 分析重复函数（只分析出现次数>1的函数）
        duplicate_funcs = {k: v for k, v in self.function_patterns.items() if len(v) > 1}
        print(f"发现 {len(duplicate_funcs)} 个重复函数模式")
        
        for func_name, instances in duplicate_funcs.items():
            similarity = self._calculate_group_similarity(instances)
            results['duplicate_functions'].append({
                'name': func_name,
                'count': len(instances),
                'similarity': similarity,
                'instances': instances[:3]  # 只保留前3个实例
            })
        
        # 2. 分析重复类
        duplicate_classes = {k: v for k, v in self.class_definitions.items() if len(v) > 1}
        print(f"发现 {len(duplicate_classes)} 个重复类模式")
        
        for class_name, instances in duplicate_classes.items():
            similarity = self._calculate_class_similarity(instances)
            results['duplicate_classes'].append({
                'name': class_name,
                'count': len(instances),
                'similarity': similarity,
                'instances': instances[:3]  # 只保留前3个实例
            })
        
        # 3. 分析相似文件（限制分析数量）
        print("分析相似文件...")
        results['similar_files'] = self._find_similar_files()
        
        # 4. 特定模式分析
        print("分析特定模式...")
        results['repair_systems'] = self._analyze_repair_systems()
        results['check_scripts'] = self._analyze_check_scripts()
        results['agent_managers'] = self._analyze_agent_managers()
        
        return results
    
    def _calculate_group_similarity(self, instances: List[Dict]) -> float:
        """计算函数组相似度"""
        if len(instances) < 2:
            return 0.0
            
        similarities = []
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                sim = self._calculate_function_similarity(instances[i], instances[j])
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_function_similarity(self, func1: Dict, func2: Dict) -> float:
        """计算两个函数的相似度"""
        # 基于函数名、参数和函数体开始部分计算相似度
        score = 0.0
        
        # 函数名相同
        if func1['name'] == func2['name']:
            score += 0.3
            
        # 参数相似度
        args_sim = difflib.SequenceMatcher(None, str(func1['args']), str(func2['args'])).ratio()
        score += args_sim * 0.3
        
        # 函数体相似度
        body_sim = difflib.SequenceMatcher(None, func1['body_start'], func2['body_start']).ratio()
        score += body_sim * 0.4
        
        return score
    
    def _calculate_class_similarity(self, instances: List[Dict]) -> float:
        """计算类相似度"""
        if len(instances) < 2:
            return 0.0
            
        similarities = []
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                sim = self._calculate_single_class_similarity(instances[i], instances[j])
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_single_class_similarity(self, class1: Dict, class2: Dict) -> float:
        """计算两个类的相似度"""
        score = 0.0
        
        # 类名相同
        if class1['name'] == class2['name']:
            score += 0.4
            
        # 方法相似度
        methods1 = set(class1['methods'])
        methods2 = set(class2['methods'])
        
        if methods1 or methods2:
            intersection = len(methods1.intersection(methods2))
            union = len(methods1.union(methods2))
            method_sim = intersection / union if union > 0 else 0
            score += method_sim * 0.4
        
        # 继承关系
        if class1['bases'] == class2['bases']:
            score += 0.2
            
        return score
    
    def _find_similar_files(self) -> List[Dict]:
        """查找相似文件"""
        similar_files = []
        file_paths = list(self.file_contents.keys())
        
        # 限制比较的文件数量
        max_comparisons = 1000
        comparison_count = 0
        
        for i in range(len(file_paths)):
            if comparison_count >= max_comparisons:
                break
                
            for j in range(i + 1, min(i + 50, len(file_paths))):  # 限制每个文件的比较数量
                if comparison_count >= max_comparisons:
                    break
                    
                content1 = self.file_contents[file_paths[i]]
                content2 = self.file_contents[file_paths[j]]
                
                # 快速预检查：如果文件大小差异很大，跳过详细比较
                if abs(len(content1) - len(content2)) > max(len(content1), len(content2)) * 0.5:
                    continue
                
                similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
                
                if similarity > self.similarity_threshold:
                    similar_files.append({
                        'file1': file_paths[i],
                        'file2': file_paths[j],
                        'similarity': similarity
                    })
                
                comparison_count += 1
        
        return similar_files
    
    def _analyze_repair_systems(self) -> List[Dict]:
        """分析修复系统"""
        repair_keywords = ['repair', 'fix', 'correct', 'heal', 'restore']
        repair_files = []
        
        for file_path, content in self.file_contents.items():
            file_name = os.path.basename(file_path).lower()
            
            # 检查文件名是否包含修复关键词
            if any(keyword in file_name for keyword in repair_keywords):
                # 分析文件内容
                lines = content.split('\n')
                class_count = 0
                function_count = 0
                
                for line in lines:
                    if line.strip().startswith('class '):
                        class_count += 1
                    elif line.strip().startswith('def '):
                        function_count += 1
                
                repair_files.append({
                    'file': file_path,
                    'classes': class_count,
                    'functions': function_count,
                    'size': len(content)
                })
        
        return repair_files
    
    def _analyze_check_scripts(self) -> List[Dict]:
        """分析检查脚本"""
        check_files = []
        
        for file_path, content in self.file_contents.items():
            file_name = os.path.basename(file_path)
            
            if file_name.startswith('check_') and file_name.endswith('.py'):
                # 分析检查脚本的模式
                lines = content.split('\n')
                has_ast = 'ast' in content
                has_file_open = 'open(' in content or 'with open' in content
                has_readlines = 'readlines' in content
                
                check_files.append({
                    'file': file_path,
                    'name': file_name,
                    'has_ast': has_ast,
                    'has_file_operations': has_file_open,
                    'has_readlines': has_readlines,
                    'lines': len(lines)
                })
        
        return check_files
    
    def _analyze_agent_managers(self) -> List[Dict]:
        """分析代理管理器"""
        manager_files = []
        
        for file_path, content in self.file_contents.items():
            file_name = os.path.basename(file_path).lower()
            
            if 'agent' in file_name and 'manager' in file_name:
                # 分析代理管理器
                has_subprocess = 'subprocess' in content
                has_asyncio = 'asyncio' in content
                has_threading = 'threading' in content
                
                manager_files.append({
                    'file': file_path,
                    'has_subprocess': has_subprocess,
                    'has_asyncio': has_asyncio,
                    'has_threading': has_threading
                })
        
        return manager_files
    
    def generate_report(self, results: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 80)
        report.append("Unified AI Project - 重复功能分析报告")
        report.append("=" * 80)
        report.append("")
        
        # 1. 重复函数
        report.append("🔧 重复函数分析")
        report.append("-" * 40)
        if results['duplicate_functions']:
            for dup in sorted(results['duplicate_functions'], key=lambda x: x['count'], reverse=True)[:10]:
                report.append(f"函数: {dup['name']} | 出现次数: {dup['count']} | 相似度: {dup['similarity']:.2f}")
                for inst in dup['instances'][:3]:  # 只显示前3个实例
                    report.append(f"  📁 {inst['file']}:{inst['line_num']}")
                report.append("")
        else:
            report.append("未发现明显的函数重复")
        report.append("")
        
        # 2. 重复类
        report.append("🏗️ 重复类分析")
        report.append("-" * 40)
        if results['duplicate_classes']:
            for dup in sorted(results['duplicate_classes'], key=lambda x: x['count'], reverse=True)[:10]:
                report.append(f"类: {dup['name']} | 出现次数: {dup['count']} | 相似度: {dup['similarity']:.2f}")
                for inst in dup['instances'][:3]:
                    report.append(f"  📁 {inst['file']}:{inst['line_num']}")
                report.append("")
        else:
            report.append("未发现明显的类重复")
        report.append("")
        
        # 3. 相似文件
        report.append("📄 相似文件分析")
        report.append("-" * 40)
        if results['similar_files']:
            for sim in sorted(results['similar_files'], key=lambda x: x['similarity'], reverse=True)[:10]:
                report.append(f"相似度: {sim['similarity']:.2f}")
                report.append(f"  📄 {sim['file1']}")
                report.append(f"  📄 {sim['file2']}")
                report.append("")
        else:
            report.append("未发现高度相似的文件")
        report.append("")
        
        # 4. 修复系统
        report.append("🔨 修复系统分析")
        report.append("-" * 40)
        if results['repair_systems']:
            report.append(f"发现 {len(results['repair_systems'])} 个修复相关文件:")
            for repair in sorted(results['repair_systems'], key=lambda x: x['size'], reverse=True)[:10]:
                file_name = os.path.basename(repair['file'])
                report.append(f"  🔧 {file_name}: {repair['classes']} 类, {repair['functions']} 函数, {repair['size']} 字节")
        report.append("")
        
        # 5. 检查脚本
        report.append("🔍 检查脚本分析")
        report.append("-" * 40)
        if results['check_scripts']:
            report.append(f"发现 {len(results['check_scripts'])} 个检查脚本:")
            patterns = defaultdict(int)
            for check in results['check_scripts']:
                pattern = f"AST:{check['has_ast']}_File:{check['has_file_operations']}_Lines:{check['lines']}"
                patterns[pattern] += 1
            
            for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  📋 模式 {pattern}: {count} 个文件")
        report.append("")
        
        # 6. 代理管理器
        report.append("🤖 代理管理器分析")
        report.append("-" * 40)
        if results['agent_managers']:
            report.append(f"发现 {len(results['agent_managers'])} 个代理管理器:")
            for manager in results['agent_managers']:
                file_name = os.path.basename(manager['file'])
                features = []
                if manager['has_subprocess']: features.append("subprocess")
                if manager['has_asyncio']: features.append("asyncio")
                if manager['has_threading']: features.append("threading")
                report.append(f"  🤖 {file_name}: {', '.join(features)}")
        report.append("")
        
        # 7. 整合建议
        report.append("💡 整合建议")
        report.append("-" * 40)
        report.append(self._generate_recommendations(results))
        
        return "\n".join(report)
    
    def _generate_recommendations(self, results: Dict) -> str:
        """生成整合建议"""
        recommendations = []
        
        # 基于分析结果生成建议
        if len(results['check_scripts']) > 10:
            recommendations.append("1. 📋 检查脚本整合:")
            recommendations.append("   - 合并相似的检查脚本，创建统一的检查框架")
            recommendations.append("   - 标准化检查脚本的参数和输出格式")
            recommendations.append("")
        
        if len(results['repair_systems']) > 5:
            recommendations.append("2. 🔨 修复系统整合:")
            recommendations.append("   - 统一修复系统的接口和配置")
            recommendations.append("   - 合并功能相似的修复类")
            recommendations.append("   - 建立统一的修复策略管理器")
            recommendations.append("")
        
        if len(results['agent_managers']) > 3:
            recommendations.append("3. 🤖 代理管理器整合:")
            recommendations.append("   - 统一代理生命周期管理")
            recommendations.append("   - 标准化代理通信协议")
            recommendations.append("   - 合并重复的代理管理功能")
            recommendations.append("")
        
        if results['duplicate_functions']:
            recommendations.append("4. 🔧 函数重复处理:")
            recommendations.append("   - 提取公共函数到工具模块")
            recommendations.append("   - 建立共享函数库")
            recommendations.append("   - 使用继承或组合减少重复")
            recommendations.append("")
        
        if results['similar_files']:
            recommendations.append("5. 📄 文件相似处理:")
            recommendations.append("   - 合并高度相似的文件")
            recommendations.append("   - 提取公共部分为基类或工具模块")
            recommendations.append("")
        
        if not recommendations:
            recommendations.append("基于当前分析，项目结构相对良好，重复功能较少。")
        
        return "\n".join(recommendations)

def main():
    """主函数"""
    analyzer = DuplicateAnalyzer()
    
    print("开始扫描Unified AI Project...")
    results = analyzer.scan_project("D:\\Projects\\Unified-AI-Project")
    
    print("\n生成分析报告...")
    report = analyzer.generate_report(results)
    
    # 保存报告
    report_file = "duplicate_analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n分析完成！报告已保存到: {report_file}")
    print(report)

if __name__ == "__main__":
    main()