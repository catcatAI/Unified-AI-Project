"""
交互式统一自动修复系统
提供交互式界面来修复项目中的语法错误
使用方式: 启动>输入待修复内容>输入开始修复>执行修复>返回修复结果
"""

import os
import ast
import importlib.util
import sys
import traceback
from typing import List, Dict, Any, Tuple
from pathlib import Path

class InteractiveAutoFixSystem:
    """交互式统一自动修复系统"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.fix_scripts = self._discover_fix_scripts()
        self.applied_fixes = []
        self.target_files = []
        self.target_code = None
        
    def _discover_fix_scripts(self) -> List[Dict[str, Any]]:
        """发现所有修复脚本"""
        fix_scripts = []
        
        # 查找修复脚本的模式
        fix_patterns = [
            "**/*fix*.py",
            "**/*auto_fix*.py",
            "**/*syntax*fix*.py"
        ]
        
        # 要排除的目录
        exclude_dirs = {"node_modules", "__pycache__", ".git", "venv", ".venv"}
        
        for pattern in fix_patterns:
            for file_path in self.project_root.glob(pattern):
                # 检查是否在排除目录中
                if any(exclude_dir in str(file_path) for exclude_dir in exclude_dirs):
                    continue
                    
                # 检查是否是Python文件
                if file_path.suffix == ".py":
                    # 获取脚本名称和描述
                    script_name = file_path.stem
                    script_description = self._extract_script_description(file_path)
                    
                    fix_scripts.append({
                        "path": str(file_path),
                        "name": script_name,
                        "description": script_description,
                        "module": None
                    })
        
        return fix_scripts
    
    def _extract_script_description(self, file_path: Path) -> str:
        """从脚本文件中提取描述"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 读取前几行寻找描述
                lines = f.readlines()[:10]
                for line in lines:
                    line = line.strip()
                    if line.startswith('"""') or line.startswith("'''"):
                        # 找到文档字符串的开始
                        if '"""' in line[3:] or "'''" in line[3:]:
                            # 单行文档字符串
                            return line[3:-3] if '"""' in line else line[3:-3]
                        else:
                            # 多行文档字符串，继续读取下一行
                            continue
                    elif line and not line.startswith('#'):
                        # 第一个非注释行作为简短描述
                        return line[:50] + "..." if len(line) > 50 else line
        except Exception:
            pass
        
        return "未提供描述"
    
    def load_fix_scripts(self) -> None:
        """加载所有修复脚本"""
        print("正在加载修复脚本...")
        
        for script_info in self.fix_scripts:
            try:
                # 动态加载模块
                spec = importlib.util.spec_from_file_location(
                    script_info["name"], 
                    script_info["path"]
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[script_info["name"]] = module
                    spec.loader.exec_module(module)
                    
                    script_info["module"] = module
                    print(f"  已加载: {script_info['name']} - {script_info['description']}")
            except Exception as e:
                print(f"  跳过 {script_info['name']}: {str(e)}")
    
    def has_syntax_error(self, file_path: str) -> Tuple[bool, str]:
        """检查文件是否有语法错误"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return False, ""
        except SyntaxError as e:
            return True, str(e)
        except Exception as e:
            return True, str(e)
    
    def get_files_with_syntax_errors(self) -> List[Tuple[str, str]]:
        """获取所有有语法错误的Python文件"""
        py_files_with_errors = []
        
        # 遍历项目目录下的所有Python文件
        for file_path in self.project_root.rglob("*.py"):
            # 跳过排除目录
            if any(exclude_dir in str(file_path) for exclude_dir in {"node_modules", "__pycache__", ".git", "venv", ".venv"}):
                continue
                
            has_error, error_msg = self.has_syntax_error(str(file_path))
            if has_error:
                py_files_with_errors.append((str(file_path), error_msg))
        
        return py_files_with_errors
    
    def set_target_files(self, file_paths: List[str]) -> bool:
        """设置待修复的文件"""
        valid_files = []
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path.endswith('.py'):
                valid_files.append(file_path)
            else:
                print(f"警告: 文件 {file_path} 不存在或不是Python文件")
        
        if valid_files:
            self.target_files = valid_files
            print(f"已设置待修复文件: {len(valid_files)} 个")
            return True
        else:
            print("错误: 没有有效的文件可修复")
            return False
    
    def set_target_code(self, code: str) -> None:
        """设置待修复的代码"""
        self.target_code = code
        print("已设置待修复代码")
    
    def run_fix_on_files(self) -> Dict[str, Any]:
        """对指定文件运行修复"""
        if not self.target_files:
            return {
                "status": "error",
                "message": "未设置待修复文件",
                "files_fixed": 0,
                "errors": []
            }
        
        print(f"开始修复 {len(self.target_files)} 个文件...")
        
        # 应用各种修复策略
        results = {
            "status": "partial",
            "files_fixed": 0,
            "total_files": len(self.target_files),
            "errors": []
        }
        
        # 按优先级顺序应用修复脚本
        fix_priority = [
            "layered_auto_fix",      # 分层修复
            "enhanced_specialized_auto_fix",  # 增强的专门修复缺少冒号的问题
            "enhanced_comprehensive_auto_fix", # 增强的全面修复
            "improved_specialized_auto_fix",  # 改进的专门修复缺少冒号的问题
            "improved_comprehensive_auto_fix", # 改进的全面修复
            "specialized_auto_fix",  # 专门修复缺少冒号的问题
            "comprehensive_auto_fix", # 全面修复
            "auto_fix_syntax",       # 基础语法修复
            "enhanced_auto_fix",     # 增强修复
            "precise_auto_fix",      # 精确修复
            "intelligent_auto_fix",  # 智能修复
            "final_auto_fix",        # 最终修复
            "complete_auto_fix",     # 完整修复
        ]
        
        # 按优先级排序修复脚本
        sorted_fix_scripts = sorted(
            [s for s in self.fix_scripts if s["module"] is not None],
            key=lambda x: (
                fix_priority.index(x["name"]) if x["name"] in fix_priority else len(fix_priority),
                x["name"]
            )
        )
        
        # 对每个文件应用修复
        for file_path in self.target_files:
            print(f"正在修复: {file_path}")
            
            # 检查文件是否有语法错误
            has_error, error_msg = self.has_syntax_error(file_path)
            if not has_error:
                print(f"  文件无语法错误，跳过")
                continue
                
            print(f"  错误: {error_msg}")
            
            file_fixed = False
            
            # 尝试按优先级应用修复脚本
            for script_info in sorted_fix_scripts:
                try:
                    module = script_info["module"]
                    
                    # 检查模块是否有修复函数
                    fix_function = None
                    if hasattr(module, "comprehensive_fix_file"):
                        fix_function = module.comprehensive_fix_file
                    elif hasattr(module, "specialized_fix_file"):
                        fix_function = module.specialized_fix_file
                    elif hasattr(module, "fix_file_syntax"):
                        fix_function = module.fix_file_syntax
                    elif hasattr(module, "precise_fix_file"):
                        fix_function = module.precise_fix_file
                    elif hasattr(module, "advanced_fix_file"):
                        fix_function = module.advanced_fix_file
                    
                    if fix_function:
                        if fix_function(file_path):
                            print(f"  使用 {script_info['name']} 修复成功")
                            file_fixed = True
                            results["files_fixed"] += 1
                            self.applied_fixes.append({
                                "file": file_path,
                                "script": script_info["name"],
                                "error": error_msg
                            })
                            break
                except Exception as e:
                    print(f"  使用 {script_info['name']} 修复时出错: {str(e)}")
                    continue
            
            if not file_fixed:
                results["errors"].append({
                    "file": file_path,
                    "error": error_msg,
                    "message": "无法使用任何修复脚本修复"
                })
        
        # 更新状态
        if results["files_fixed"] == results["total_files"]:
            results["status"] = "success"
            results["message"] = f"成功修复所有 {results['files_fixed']} 个文件"
        elif results["files_fixed"] > 0:
            results["message"] = f"成功修复 {results['files_fixed']} 个文件，{results['total_files'] - results['files_fixed']} 个文件无法修复"
        else:
            results["status"] = "error"
            results["message"] = "未能修复任何文件"
        
        return results
    
    def run_fix_on_code(self) -> Dict[str, Any]:
        """对代码字符串运行修复"""
        if not self.target_code:
            return {
                "status": "error",
                "message": "未设置待修复代码",
                "fixed_code": None,
                "error": None
            }
        
        print("开始修复代码...")
        
        # 创建临时文件来测试修复
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.target_code)
            temp_file_path = f.name
        
        try:
            # 检查原始代码是否有语法错误
            try:
                ast.parse(self.target_code)
                original_has_error = False
                original_error = ""
            except SyntaxError as e:
                original_has_error = True
                original_error = str(e)
            except Exception as e:
                original_has_error = True
                original_error = str(e)
            
            if not original_has_error:
                print("代码无语法错误，无需修复")
                return {
                    "status": "success",
                    "message": "代码无语法错误，无需修复",
                    "fixed_code": self.target_code,
                    "error": None
                }
            
            print(f"原始代码错误: {original_error}")
            
            # 按优先级顺序应用修复脚本
            fix_priority = [
                "layered_auto_fix",      # 分层修复
                "enhanced_specialized_auto_fix",  # 增强的专门修复缺少冒号的问题
                "enhanced_comprehensive_auto_fix", # 增强的全面修复
                "improved_specialized_auto_fix",  # 改进的专门修复缺少冒号的问题
                "improved_comprehensive_auto_fix", # 改进的全面修复
                "specialized_auto_fix",  # 专门修复缺少冒号的问题
                "comprehensive_auto_fix", # 全面修复
                "auto_fix_syntax",       # 基础语法修复
                "enhanced_auto_fix",     # 增强修复
                "precise_auto_fix",      # 精确修复
                "intelligent_auto_fix",  # 智能修复
                "final_auto_fix",        # 最终修复
                "complete_auto_fix",     # 完整修复
            ]
            
            # 按优先级排序修复脚本
            sorted_fix_scripts = sorted(
                [s for s in self.fix_scripts if s["module"] is not None],
                key=lambda x: (
                    fix_priority.index(x["name"]) if x["name"] in fix_priority else len(fix_priority),
                    x["name"]
                )
            )
            
            # 尝试应用修复
            code_fixed = False
            for script_info in sorted_fix_scripts:
                try:
                    module = script_info["module"]
                    
                    # 检查模块是否有修复函数
                    fix_function = None
                    if hasattr(module, "comprehensive_fix_file"):
                        fix_function = module.comprehensive_fix_file
                    elif hasattr(module, "specialized_fix_file"):
                        fix_function = module.specialized_fix_file
                    elif hasattr(module, "fix_file_syntax"):
                        fix_function = module.fix_file_syntax
                    elif hasattr(module, "precise_fix_file"):
                        fix_function = module.precise_fix_file
                    elif hasattr(module, "advanced_fix_file"):
                        fix_function = module.advanced_fix_file
                    
                    if fix_function:
                        # 将代码写入临时文件并尝试修复
                        with open(temp_file_path, 'w', encoding='utf-8') as f:
                            f.write(self.target_code)
                        
                        if fix_function(temp_file_path):
                            print(f"  使用 {script_info['name']} 修复成功")
                            code_fixed = True
                            # 读取修复后的代码
                            with open(temp_file_path, 'r', encoding='utf-8') as f:
                                fixed_code = f.read()
                            break
                except Exception as e:
                    print(f"  使用 {script_info['name']} 修复时出错: {str(e)}")
                    continue
            
            if code_fixed:
                # 验证修复后的代码
                try:
                    ast.parse(fixed_code)
                    return {
                        "status": "success",
                        "message": "代码修复成功",
                        "fixed_code": fixed_code,
                        "error": None
                    }
                except SyntaxError as e:
                    return {
                        "status": "error",
                        "message": "修复后的代码仍有语法错误",
                        "fixed_code": fixed_code,
                        "error": str(e)
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": "修复后的代码验证失败",
                        "fixed_code": fixed_code,
                        "error": str(e)
                    }
            else:
                return {
                    "status": "error",
                    "message": "无法使用任何修复脚本修复代码",
                    "fixed_code": self.target_code,
                    "error": original_error
                }
                
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def generate_fix_report(self) -> str:
        """生成修复报告"""
        report = "自动修复报告\n"
        report += "=" * 50 + "\n\n"
        
        report += f"已应用的修复: {len(self.applied_fixes)}\n\n"
        
        if self.applied_fixes:
            report += "详细修复记录:\n"
            report += "-" * 30 + "\n"
            for fix in self.applied_fixes:
                report += f"文件: {fix['file']}\n"
                report += f"使用的脚本: {fix['script']}\n"
                report += f"原始错误: {fix['error']}\n"
                report += "-" * 30 + "\n"
        
        return report
    
    def save_fix_report(self, output_file: str = "auto_fix_report.txt") -> None:
        """保存修复报告到文件"""
        report = self.generate_fix_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"修复报告已保存到: {output_file}")


def interactive_mode():
    """交互式模式"""
    print("交互式自动修复系统")
    print("=" * 30)
    print("使用方式：")
    print("1. 启动系统")
    print("2. 输入待修复的文件路径或代码")
    print("3. 输入'开始修复'执行修复")
    print("4. 查看修复结果")
    print("5. 输入'退出'退出系统")
    print("=" * 30)
    
    # 创建交互式修复系统实例
    fix_system = InteractiveAutoFixSystem()
    
    # 加载修复脚本
    fix_system.load_fix_scripts()
    
    while True:
        print("\n请选择操作:")
        print("1. 设置待修复文件")
        print("2. 设置待修复代码")
        print("3. 开始修复")
        print("4. 查看修复报告")
        print("5. 退出")
        
        choice = input("请输入选择 (1-5): ").strip()
        
        if choice == "1":
            print("\n请输入待修复的文件路径（多个文件用逗号分隔）:")
            file_paths_input = input().strip()
            if file_paths_input:
                file_paths = [path.strip() for path in file_paths_input.split(",")]
                fix_system.set_target_files(file_paths)
            else:
                print("未输入文件路径")
                
        elif choice == "2":
            print("\n请输入待修复的代码（输入'END'结束）:")
            code_lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                code_lines.append(line)
            
            if code_lines:
                code = "\n".join(code_lines)
                fix_system.set_target_code(code)
            else:
                print("未输入代码")
                
        elif choice == "3":
            if fix_system.target_files:
                print("\n开始修复文件...")
                results = fix_system.run_fix_on_files()
                print("\n修复结果:")
                print(f"  状态: {results['status']}")
                print(f"  消息: {results['message']}")
                print(f"  修复文件数: {results['files_fixed']}")
                
                if results["errors"]:
                    print(f"\n无法修复的文件 ({len(results['errors'])}):")
                    for error in results["errors"][:5]:  # 只显示前5个错误
                        print(f"  {error['file']}: {error['error']}")
                    if len(results["errors"]) > 5:
                        print(f"  ... 还有 {len(results['errors']) - 5} 个文件")
                        
            elif fix_system.target_code:
                print("\n开始修复代码...")
                results = fix_system.run_fix_on_code()
                print("\n修复结果:")
                print(f"  状态: {results['status']}")
                print(f"  消息: {results['message']}")
                
                if results['status'] == 'success' and results.get('fixed_code'):
                    print("\n修复后的代码:")
                    print("-" * 30)
                    print(results['fixed_code'])
                    print("-" * 30)
                elif results.get('error'):
                    print(f"  错误: {results['error']}")
            else:
                print("请先设置待修复的文件或代码")
                
        elif choice == "4":
            report = fix_system.generate_fix_report()
            print("\n" + report)
            
        elif choice == "5":
            print("退出系统...")
            break
            
        else:
            print("无效选择，请重新输入")


def main():
    """主函数"""
    interactive_mode()


if __name__ == "__main__":
    main()