#!/usr/bin/env python3
"""
Angela AI v6.0 全面质量检查工具
Comprehensive Quality Check Tool
"""

import ast
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple, Set
import logging
logger = logging.getLogger(__name__)

# 颜色代码
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class AngelaCodeChecker:
    """Angela AI代码质量检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        self.autonomous_dir = Path("apps/backend/src/core/autonomous")
        
    def log_issue(self, msg: str, level="error"):
        """记录问题"""
        if level == "error":
            self.issues.append(msg)
            print(f"{RED}❌ {msg}{RESET}")
        elif level == "warning":
            self.warnings.append(msg)
            print(f"{YELLOW}⚠️  {msg}{RESET}")
        else:
            self.info.append(msg)
            print(f"{BLUE}ℹ️  {msg}{RESET}")
    
    def check_syntax(self, filepath: Path) -> bool:
        """检查Python语法"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True
        except SyntaxError as e:
            self.log_issue(f"语法错误在 {filepath}: {e}")
            return False
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.log_issue(f"无法解析 {filepath}: {e}")

            return False
    
    def check_imports(self, filepath: Path) -> List[str]:
        """检查导入语句"""
        broken_imports = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        try:
                            # 尝试导入模块
                            if module_name in ['asyncio', 'typing', 'datetime', 'enum', 'dataclasses', 'pathlib', 'json', 'random', 'math', 'time', 'collections', 'abc']:
                                continue  # 跳过标准库
                            if module_name.startswith('apps.'):
                                continue  # 跳过本地模块
                            if '.' in module_name:
                                module_name = module_name.split('.')[0]
                            __import__(module_name)
                        except ImportError:
                            broken_imports.append(f"{module_name} in {filepath}")
                            self.log_issue(f"无法导入模块: {module_name} 在 {filepath}", "warning")
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.log_issue(f"检查导入时出错 {filepath}: {e}", "warning")

        
        return broken_imports
    
    def check_class_structure(self, filepath: Path) -> Dict[str, List[str]]:
        """检查类结构"""
        issues = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    class_issues = []
                    
                    # 检查是否有__init__方法
                    has_init = any(
                        isinstance(n, ast.FunctionDef) and n.name == '__init__' 
                        for n in node.body
                    )
                    if not has_init and not any(n.name.startswith('_') for n in node.body if isinstance(n, ast.FunctionDef)):
                        class_issues.append("缺少__init__方法")
                    
                    # 检查方法定义
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    for method in methods:
                        # 检查是否使用了self参数
                        if method.args.args:
                            first_arg = method.args.args[0].arg
                            if first_arg != 'self' and first_arg != 'cls':
                                class_issues.append(f"方法{method.name}的第一个参数不是self/cls")
                    
                    if class_issues:
                        issues[class_name] = class_issues
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.log_issue(f"检查类结构时出错 {filepath}: {e}", "warning")

        
        return issues
    
    def check_method_calls(self, filepath: Path, class_name: str) -> List[str]:
        """检查类中是否调用了未定义的方法"""
        undefined_calls = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    # 获取所有定义的方法
                    defined_methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
                    
                    # 检查所有方法调用
                    for method_node in node.body:
                        if isinstance(method_node, ast.FunctionDef):
                            for subnode in ast.walk(method_node):
                                if isinstance(subnode, ast.Call):
                                    if isinstance(subnode.func, ast.Attribute):
                                        if isinstance(subnode.func.value, ast.Name):
                                            if subnode.func.value.id == 'self':
                                                method_name = subnode.func.attr
                                                if method_name not in defined_methods and not method_name.startswith('_'):
                                                    undefined_calls.append(f"{method_name} in {method_node.name}")
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass

        
        return undefined_calls
    
    def check_cross_module_connections(self) -> List[str]:
        """检查跨模块连接"""
        print("\n" + "="*70)
        print("🔗 检查跨模块连接")
        print("="*70)
        
        connection_issues = []
        
        # 检查导入关系
        files_to_check = list(self.autonomous_dir.glob("*.py"))
        
        # 提取所有导出
        exports = {}
        for filepath in files_to_check:
            if filepath.name == '__init__.py':
                continue
            module_name = filepath.stem
            exports[module_name] = self._get_exports_from_file(filepath)
        
        # 检查每个文件引用了什么
        for filepath in files_to_check:
            if filepath.name == '__init__.py':
                continue
            
            module_name = filepath.stem
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否引用了其他模块的类
            for other_module, other_exports in exports.items():
                if other_module == module_name:
                    continue
                
                for export in other_exports:
                    if export in content and f"from .{other_module}" not in content:
                        if export not in content:  # 简单检查
                            continue
                        # 这是一个跨模块引用
                        pass
        
        # 检查关键集成点
        integrator_files = [
            "biological_integrator.py",
            "digital_life_integrator.py",
            "memory_neuroplasticity_bridge.py"
        ]
        
        for integrator in integrator_files:
            filepath = self.autonomous_dir / integrator
            if not filepath.exists():
                connection_issues.append(f"集成器文件缺失: {integrator}")
                self.log_issue(f"关键集成器缺失: {integrator}")
            else:
                self.log_issue(f"集成器存在: {integrator}", "info")
        
        return connection_issues
    
    def _get_exports_from_file(self, filepath: Path) -> List[str]:
        """从文件获取导出的类名"""
        exports = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    exports.append(node.name)
        except Exception as e:
            logger.error(f'Unexpected error in {__name__}: {e}', exc_info=True)
            pass

        return exports
    
    def check_tech_stack(self) -> Dict[str, bool]:
        """检查技术栈"""
        print("\n" + "="*70)
        print("🛠️  技术栈检查")
        print("="*70)
        
        tech_checks = {
            "Python 3.11+": True,  # 假设当前环境
            "asyncio": True,
            "dataclasses": True,
            "typing": True,
            "FastAPI": False,
            "Live2D": False,
            "OpenAI/Gemini API": False,
            "pygame": False,
        }
        
        # 检查requirements.txt
        req_file = Path("requirements.txt")
        if req_file.exists():
            with open(req_file, 'r') as f:
                content = f.read().lower()
                if 'fastapi' in content:
                    tech_checks["FastAPI"] = True
                if 'openai' in content or 'google-generativeai' in content:
                    tech_checks["OpenAI/Gemini API"] = True
                if 'pygame' in content or 'pyglet' in content:
                    tech_checks["pygame"] = True
        
        for tech, available in tech_checks.items():
            if available:
                self.log_issue(f"技术栈: {tech}", "info")
            else:
                self.log_issue(f"技术栈缺失或未检测: {tech}", "warning")
        
        return tech_checks
    
    def check_documentation(self) -> bool:
        """检查文档完整性"""
        print("\n" + "="*70)
        print("📚 文档检查")
        print("="*70)
        
        required_docs = [
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "requirements.txt",
            "setup.py",
        ]
        
        all_present = True
        for doc in required_docs:
            if Path(doc).exists():
                self.log_issue(f"文档存在: {doc}", "info")
            else:
                self.log_issue(f"文档缺失: {doc}")
                all_present = False
        
        return all_present
    
    def check_test_coverage(self) -> Dict[str, int]:
        """检查测试覆盖情况"""
        print("\n" + "="*70)
        print("🧪 测试覆盖检查")
        print("="*70)
        
        stats = {
            "total_files": 0,
            "files_with_tests": 0,
            "test_files": 0,
        }
        
        # 统计自主系统文件
        autonomous_files = [f for f in self.autonomous_dir.glob("*.py") if f.name != '__init__.py']
        stats["total_files"] = len(autonomous_files)
        
        # 检查对应的测试文件
        test_dir = Path("apps/backend/tests")
        if test_dir.exists():
            test_files = list(test_dir.rglob("test_*.py"))
            stats["test_files"] = len(test_files)
            
            # 检查哪些文件有测试
            for af in autonomous_files:
                expected_test = f"test_{af.stem}.py"
                has_test = any(expected_test in str(tf) for tf in test_files)
                if has_test:
                    stats["files_with_tests"] += 1
                else:
                    self.log_issue(f"缺少测试: {af.name}", "warning")
        else:
            self.log_issue("测试目录不存在", "warning")
        
        return stats
    
    def run_all_checks(self):
        """运行所有检查"""
        print("="*70)
        print("🔍 Angela AI v6.0 全面质量检查")
        print("="*70)
        
        # 1. 语法检查
        print("\n" + "="*70)
        print("📝 语法检查")
        print("="*70)
        
        syntax_errors = 0
        for filepath in self.autonomous_dir.glob("*.py"):
            if not self.check_syntax(filepath):
                syntax_errors += 1
        
        if syntax_errors == 0:
            self.log_issue("所有文件语法正确", "info")
        
        # 2. 导入检查
        print("\n" + "="*70)
        print("📦 导入检查")
        print("="*70)
        
        for filepath in self.autonomous_dir.glob("*.py"):
            broken = self.check_imports(filepath)
        
        # 3. 类结构检查
        print("\n" + "="*70)
        print("🏗️ 类结构检查")
        print("="*70)
        
        for filepath in self.autonomous_dir.glob("*.py"):
            issues = self.check_class_structure(filepath)
            for class_name, class_issues in issues.items():
                for issue in class_issues:
                    self.log_issue(f"{filepath.name}::{class_name}: {issue}", "warning")
        
        # 4. 跨模块连接
        self.check_cross_module_connections()
        
        # 5. 技术栈
        self.check_tech_stack()
        
        # 6. 文档
        self.check_documentation()
        
        # 7. 测试
        test_stats = self.check_test_coverage()
        
        # 总结报告
        self.print_summary(syntax_errors, test_stats)
    
    def print_summary(self, syntax_errors: int, test_stats: Dict):
        """打印总结报告"""
        print("\n" + "="*70)
        print("📊 质量检查总结报告")
        print("="*70)
        
        print(f"\n错误数: {len(self.issues)}")
        print(f"警告数: {len(self.warnings)}")
        print(f"信息数: {len(self.info)}")
        print(f"语法错误: {syntax_errors}")
        
        print(f"\n自主系统文件: {test_stats['total_files']}")
        print(f"有测试的文件: {test_stats['files_with_tests']}")
        print(f"测试覆盖率: {test_stats['files_with_tests']/test_stats['total_files']*100:.1f}%" if test_stats['total_files'] > 0 else "N/A")
        
        if len(self.issues) == 0 and syntax_errors == 0:
            print(f"\n{GREEN}✅ 代码质量良好，可以发布！{RESET}")
        elif len(self.issues) == 0:
            print(f"\n{YELLOW}⚠️  有警告但没有严重错误{RESET}")
        else:
            print(f"\n{RED}❌ 存在严重问题，需要修复后才能发布{RESET}")


if __name__ == "__main__":
    checker = AngelaCodeChecker()
    checker.run_all_checks()
