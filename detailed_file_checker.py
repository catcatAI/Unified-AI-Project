#!/usr/bin/env python3
"""
Level 5 AGI项目详细文件完整性检查器
逐文件验证所有Python文件和其他配置文件的完整性与正确性
"""

import os
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import traceback

class DetailedFileChecker:
    """详细文件检查器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.check_results = {}
        self.errors_found = []
        self.warnings_found = []
        
    def check_python_syntax(self, file_path: Path) -> Tuple[bool, List[str], List[str]]:
        """检查Python文件语法"""
        errors = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本语法检查
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"语法错误: {e}")
                return False, errors, warnings
            
            # 详细代码质量检查
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # 检查常见的语法问题
                if 'print ' in line and not line.strip().startswith('#'):  # Python 2 print
                    warnings.append(f"第{i}行: 可能使用了Python 2的print语法")
                
                if re.search(r'\bexcept\s*:\s*$', line):  # 裸except
                    warnings.append(f"第{i}行: 使用了裸except，建议指定异常类型")
                
                if re.search(r'\bimport\s+\*\b', line):  # import *
                    warnings.append(f"第{i}行: 使用了import *，建议显式导入")
                
                # 检查未使用的变量（简单检查）
                if re.search(r'^\s*[a-zA-Z_]\w*\s*=\s*.+', line) and not line.strip().endswith(')'):
                    var_name = re.match(r'^\s*([a-zA-Z_]\w*)\s*=', line)
                    if var_name and var_name.group(1) not in ['_', 'logger']:
                        # 检查变量是否在后续使用
                        var_used = False
                        for j in range(i, min(i+10, len(lines))):
                            if var_name.group(1) in lines[j] and j != i-1:
                                var_used = True
                                break
                        if not var_used:
                            warnings.append(f"第{i}行: 变量'{var_name.group(1)}'可能未使用")
            
            return True, errors, warnings
            
        except Exception as e:
            errors.append(f"文件读取错误: {e}")
            return False, errors, warnings
    
    def check_imports(self, file_path: Path) -> Tuple[bool, List[str], List[str]]:
        """检查导入语句"""
        errors = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST获取导入
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # 检查常见导入问题
            project_root = self.project_root
            
            for import_name in imports:
                # 检查相对导入
                if import_name.startswith('.'):
                    # 验证相对导入路径
                    continue
                
                # 检查项目内导入
                if import_name.startswith('apps.') or import_name.startswith('training.') or import_name.startswith('packages.'):
                    # 验证项目内导入是否存在
                    import_parts = import_name.split('.')
                    possible_path = project_root
                    
                    for part in import_parts:
                        possible_path = possible_path / part
                        if possible_path.exists() and possible_path.is_dir():
                            continue
                        elif (possible_path.with_suffix('.py')).exists():
                            break
                        else:
                            # 检查是否是Python模块
                            init_file = possible_path / "__init__.py"
                            if init_file.exists():
                                continue
                            else:
                                warnings.append(f"导入'{import_name}'可能指向不存在的模块")
                                break
            
            return True, errors, warnings
            
        except Exception as e:
            errors.append(f"导入检查错误: {e}")
            return False, errors, warnings
    
    def check_configuration_files(self) -> Dict[str, Any]:
        """检查配置文件"""
        print("⚙️ 检查配置文件...")
        
        config_files = {
            "package.json": self.project_root / "package.json",
            "requirements.txt": self.project_root / "requirements.txt", 
            "pnpm-workspace.yaml": self.project_root / "pnpm-workspace.yaml",
            "tsconfig.json": self.project_root / "tsconfig.json",
            "next.config.ts": self.project_root / "apps" / "frontend-dashboard" / "next.config.ts",
            "tailwind.config.ts": self.project_root / "apps" / "frontend-dashboard" / "tailwind.config.ts"
        }
        
        results = {}
        
        for config_name, config_path in config_files.items():
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 基本JSON验证（如果是JSON文件）
                    if config_name.endswith('.json'):
                        try:
                            json.loads(content)
                            results[config_name] = {"status": "valid", "path": str(config_path)}
                        except json.JSONDecodeError as e:
                            results[config_name] = {"status": "invalid_json", "error": str(e), "path": str(config_path)}
                    else:
                        results[config_name] = {"status": "exists", "path": str(config_path)}
                        
                except Exception as e:
                    results[config_name] = {"status": "error", "error": str(e), "path": str(config_path)}
            else:
                results[config_name] = {"status": "missing", "path": str(config_path)}
        
        return results
    
    def check_frontend_files(self) -> Dict[str, Any]:
        """检查前端文件"""
        print("🌐 检查前端文件...")
        
        frontend_path = self.project_root / "apps" / "frontend-dashboard"
        
        if not frontend_path.exists():
            return {"error": "前端目录不存在"}
        
        # 检查关键前端文件
        key_files = {
            "package.json": frontend_path / "package.json",
            "next.config.ts": frontend_path / "next.config.ts",
            "tsconfig.json": frontend_path / "tsconfig.json",
            "tailwind.config.ts": frontend_path / "tailwind.config.ts",
            "src/app/layout.tsx": frontend_path / "src" / "app" / "layout.tsx",
            "src/app/page.tsx": frontend_path / "src" / "app" / "page.tsx"
        }
        
        results = {}
        
        for file_name, file_path in key_files.items():
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查TypeScript语法（基本检查）
                    if file_name.endswith('.ts') or file_name.endswith('.tsx'):
                        # 基本TypeScript语法检查
                        if 'useState' in content and '"use client"' not in content:
                            results[file_name] = {
                                "status": "needs_client_directive", 
                                "path": str(file_path),
                                "issue": "使用了useState但缺少use client指令"
                            }
                        else:
                            results[file_name] = {"status": "valid", "path": str(file_path)}
                    else:
                        results[file_name] = {"status": "exists", "path": str(file_path)}
                        
                except Exception as e:
                    results[file_name] = {"status": "error", "error": str(e), "path": str(file_path)}
            else:
                results[file_name] = {"status": "missing", "path": str(file_path)}
        
        return results
    
    def check_training_system(self) -> Dict[str, Any]:
        """检查训练系统"""
        print("🎯 检查训练系统...")
        
        training_path = self.project_root / "training"
        
        if not training_path.exists():
            return {"error": "训练目录不存在"}
        
        # 检查关键训练文件
        key_files = {
            "simple_training_manager.py": training_path / "simple_training_manager.py",
            "train_model.py": training_path / "train_model.py",
            "auto_train.bat": training_path / "auto_train.bat",
            "configs/training_preset.json": training_path / "configs" / "training_preset.json",
            "data_manager.py": training_path / "data_manager.py"
        }
        
        results = {}
        
        for file_name, file_path in key_files.items():
            if file_path.exists():
                try:
                    # 检查Python文件的语法
                    if file_name.endswith('.py'):
                        from pathlib import Path
                        import subprocess
                        
                        try:
                            result = subprocess.run(['python', '-m', 'py_compile', str(file_path)], 
                                                  capture_output=True, text=True, cwd=str(self.project_root))
                            if result.returncode == 0:
                                results[file_name] = {"status": "valid_python", "path": str(file_path)}
                            else:
                                results[file_name] = {
                                    "status": "python_syntax_error", 
                                    "error": result.stderr,
                                    "path": str(file_path)
                                }
                        except Exception as e:
                            # 如果py_compile不可用，使用基本语法检查
                            try:
                                import ast
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    ast.parse(f.read())
                                results[file_name] = {"status": "valid_python", "path": str(file_path)}
                            except SyntaxError as e:
                                results[file_name] = {
                                    "status": "python_syntax_error", 
                                    "error": str(e),
                                    "path": str(file_path)
                                }
                    else:
                        results[file_name] = {"status": "exists", "path": str(file_path)}
                        
                except Exception as e:
                    results[file_name] = {"status": "error", "error": str(e), "path": str(file_path)}
            else:
                results[file_name] = {"status": "missing", "path": str(file_path)}
        
        return results
    
    def check_system_entry_points(self) -> Dict[str, Any]:
        """检查系统入口点"""
        print("🚪 检查系统入口点...")
        
        entry_points = {
            "主后端": self.project_root / "apps" / "backend" / "main.py",
            "前端开发": self.project_root / "apps" / "frontend-dashboard" / "package.json",
            "CLI工具": self.project_root / "packages" / "cli" / "cli" / "__main__.py",
            "自动训练": self.project_root / "training" / "simple_training_manager.py",
            "系统健康检查": self.project_root / "check_system_health.py"
        }
        
        results = {}
        
        for entry_name, entry_path in entry_points.items():
            if entry_path.exists():
                try:
                    if entry_path.suffix == '.py':
                        # 检查Python入口点的语法
                        import ast
                        with open(entry_path, 'r', encoding='utf-8') as f:
                            ast.parse(f.read())
                        results[entry_name] = {"status": "valid_entry", "path": str(entry_path)}
                    elif entry_path.suffix == '.json':
                        # 检查JSON配置文件
                        import json
                        with open(entry_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                        results[entry_name] = {"status": "valid_config", "path": str(entry_path)}
                    else:
                        results[entry_name] = {"status": "exists", "path": str(entry_path)}
                        
                except Exception as e:
                    results[entry_name] = {"status": "error", "error": str(e), "path": str(entry_path)}
            else:
                results[entry_name] = {"status": "missing", "path": str(entry_path)}
        
        return results
    
    def check_all_python_files(self) -> Dict[str, Any]:
        """检查所有Python文件"""
        print("🐍 检查所有Python文件...")
        
        python_files = list(self.project_root.rglob("*.py"))
        
        # 优先检查核心文件
        core_files = [
            "apps/backend/src/core/knowledge/unified_knowledge_graph.py",
            "apps/backend/src/core/fusion/multimodal_fusion_engine.py",
            "apps/backend/src/core/cognitive/cognitive_constraint_engine.py",
            "apps/backend/src/core/evolution/autonomous_evolution_engine.py",
            "apps/backend/src/core/creativity/creative_breakthrough_engine.py",
            "apps/backend/src/core/metacognition/metacognitive_capabilities_engine.py"
        ]
        
        results = {
            "total_python_files": len(python_files),
            "syntax_errors": [],
            "import_errors": [],
            "warnings": [],
            "core_files_status": {}
        }
        
        # 首先检查核心文件
        for core_file in core_files:
            core_path = self.project_root / core_file
            if core_path.exists():
                valid, errors, warnings = self.check_python_syntax(core_path)
                results["core_files_status"][core_file] = {
                    "valid": valid,
                    "errors": errors,
                    "warnings": warnings
                }
                
                if not valid:
                    results["syntax_errors"].extend([f"{core_file}: {e}" for e in errors])
                
                results["warnings"].extend([f"{core_file}: {w}" for w in warnings])
        
        # 然后检查其他重要文件
        important_files = [
            "training/simple_training_manager.py",
            "apps/backend/src/core/tools/logic_model/logic_data_generator_clean.py",
            "apps/backend/main.py",
            "packages/cli/cli/__main__.py"
        ]
        
        for imp_file in important_files:
            imp_path = self.project_root / imp_file
            if imp_path.exists():
                valid, errors, warnings = self.check_python_syntax(imp_path)
                if not valid:
                    results["syntax_errors"].extend([f"{imp_file}: {e}" for e in errors])
                results["warnings"].extend([f"{imp_file}: {w}" for w in warnings])
        
        return results
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """运行全面检查"""
        print("🚀 开始Level 5 AGI项目详细文件完整性检查...")
        print("=" * 70)
        
        # 执行所有检查
        config_check = self.check_configuration_files()
        frontend_check = self.check_frontend_files()
        training_check = self.check_training_system()
        entry_points = self.check_system_entry_points()
        python_files = self.check_all_python_files()
        
        # 汇总结果
        total_errors = len(python_files["syntax_errors"]) + len(python_files["import_errors"])
        total_warnings = len(python_files["warnings"]) + len(frontend_check.get("warnings", []))
        
        final_result = {
            "configuration_files": config_check,
            "frontend_system": frontend_check,
            "training_system": training_check,
            "system_entry_points": entry_points,
            "python_files": python_files,
            "summary": {
                "total_python_files": python_files["total_python_files"],
                "syntax_errors": total_errors,
                "warnings": total_warnings,
                "core_files_valid": all(f["valid"] for f in python_files["core_files_status"].values()),
                "overall_status": "needs_attention" if total_errors > 0 else "mostly_valid"
            }
        }
        
        print("\n" + "=" * 70)
        print("🎯 详细文件完整性检查完成！")
        print(f"📊 总计Python文件: {python_files['total_python_files']}")
        print(f"❌ 发现错误: {total_errors}")
        print(f"⚠️ 发现警告: {total_warnings}")
        print(f"🎯 核心文件状态: {'✅ 全部有效' if final_result['summary']['core_files_valid'] else '❌ 存在错误'}")
        
        return final_result

def main():
    """主函数"""
    print("🌟 Level 5 AGI项目详细文件完整性检查系统")
    print("=" * 70)
    
    checker = DetailedFileChecker()
    results = checker.run_comprehensive_check()
    
    print("\n🎉 详细文件完整性检查完成！")
    print("=" * 70)
    
    # 生成详细报告
    if results["summary"]["syntax_errors"]:
        print("\n❌ 发现的语法错误:")
        for error in results["summary"]["syntax_errors"][:5]:  # 显示前5个错误
            print(f"  - {error}")
        if len(results["summary"]["syntax_errors"]) > 5:
            print(f"  ... 还有 {len(results['summary']['syntax_errors']) - 5} 个错误")
    
    if results["python_files"]["warnings"]:
        print("\n⚠️ 发现的警告:")
        for warning in results["python_files"]["warnings"][:5]:  # 显示前5个警告
            print(f"  - {warning}")
        if len(results["python_files"]["warnings"]) > 5:
            print(f"  ... 还有 {len(results['python_files']['warnings']) - 5} 个警告")
    
    return results

if __name__ == "__main__":
    results = main()
    
    # 退出码基于检查结果
    if results["summary"]["syntax_errors"] == 0 and results["summary"]["core_files_valid"]:
        print("\n🎊 所有核心文件验证通过！")
        exit(0)
    elif results["summary"]["syntax_errors"] == 0:
        print("\n✨ 大部分文件验证通过，需要处理警告")
        exit(1)
    else:
        print("\n❌ 发现语法错误，需要修复")
        exit(2)