"""
统一自动修复系统 (简化版)
整合所有修复功能并提供交互式界面来修复项目中的语法错误
使用方式：启动>输入待修复内容>输入开始修复>执行修复>返回修复结果
"""

import os
import re
import ast
import traceback
import tempfile
from typing import List, Tuple
from pathlib import Path

class UnifiedAutoFixSystem:
    """统一自动修复系统"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.applied_fixes = []
        self.target_files = []
        self.target_code = None
    
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
    
    def fix_missing_colons(self, content: str) -> str:
        """修复缺少冒号的問題"""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # 跳過空行和註釋行
            if not stripped_line or stripped_line.startswith('#'):
                fixed_lines.append(line)
                continue
            
            # 修復類定義缺少冒號的問題
            if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?\s*$', stripped_line):
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed class definition missing colon on line {i+1}")
                continue
            
            # 修復函數定義缺少冒號的問題
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line):
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed function definition missing colon on line {i+1}")
                continue
            
            # 修復控制流語句缺少冒號的問題
            control_flow_patterns = [
                r'^\s*if\s+.*$',
                r'^\s*elif\s+.*$',
                r'^\s*else\s*$',
                r'^\s*for\s+.*$',
                r'^\s*while\s+.*$',
                r'^\s*try\s*$',
                r'^\s*except\s*.*$',
                r'^\s*finally\s*$',
                r'^\s*with\s+.*$'
            ]
            
            is_control_flow = False
            for pattern in control_flow_patterns:
                if re.match(pattern, stripped_line) and not stripped_line.endswith(':'):
                    is_control_flow = True
                    break
            
            if is_control_flow:
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed control flow statement missing colon on line {i+1}")
                continue
            
            # 保持其他行不變
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def fix_indentation_issues(self, content: str) -> str:
        """修復縮進問題"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            
            # 跳過空行和註釋行
            if not stripped_line or stripped_line.startswith('#'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # 檢查是否是需要縮進塊的語句
            control_flow_patterns = [
                r'^\s*def\s+\w+\s*\([^)]*\):\s*$',
                r'^\s*class\s+\w+(?:\s*\([^)]*\))?:\s*$',
                r'^\s*if\s+.*:\s*$',
                r'^\s*elif\s+.*:\s*$',
                r'^\s*else\s*:\s*$',
                r'^\s*for\s+.*:\s*$',
                r'^\s*while\s+.*:\s*$',
                r'^\s*try\s*:\s*$',
                r'^\s*except\s*.*:\s*$',
                r'^\s*finally\s*:\s*$',
                r'^\s*with\s+.*:\s*$'
            ]
            
            needs_indent_block = False
            for pattern in control_flow_patterns:
                if re.match(pattern, line):
                    needs_indent_block = True
                    break
            
            # 如果需要縮進塊，但下一行沒有縮進且不是空行或註釋
            if (needs_indent_block and 
                i + 1 < len(lines) and 
                lines[i + 1].strip() and 
                not lines[i + 1].startswith(' ') and 
                not lines[i + 1].startswith('\t') and
                not lines[i + 1].startswith('#') and
                lines[i + 1].strip() not in ['else:', 'elif', 'except:', 'finally:']):
                # 下一行應該縮進
                fixed_lines.append(line)
                fixed_lines.append(f"    {lines[i + 1]}")
                print(f"  Fixed indentation issue on line {i+2}")
                i += 2
                continue
            
            # 保持其他行不變
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines)
    
    def fix_syntax_issues(self, content: str) -> str:
        """修復常見語法問題"""
        original_content = content
        
        # 修復函數調用後面的冒號問題
        content = re.sub(r'(\w+\s*\([^)]*\))\s*:', r'\1', content)
        
        # 修復 super() 調用
        content = re.sub(r'super\s*\.', 'super().', content)
        
        # 修復函數調用後的括號問題
        content = re.sub(r'(\w+)\s*\(\s*\)\s*:', r'\1()', content)
        content = re.sub(r'(\w+)\s*\(\s*([^)]*)\s*\)\s*:', r'\1(\2)', content)
        
        # 修復類型註解中的問題
        content = re.sub(r'(\w+)\s*:\s*Any\s*:', r'\1: Any', content)
        content = re.sub(r'(\w+)\s*:\s*str\s*:', r'\1: str', content)
        content = re.sub(r'(\w+)\s*:\s*int\s*:', r'\1: int', content)
        content = re.sub(r'(\w+)\s*:\s*bool\s*:', r'\1: bool', content)
        
        # 修復註釋中的冒號
        content = re.sub(r'(#.*)\s*:', r'\1', content)
        
        return content
    
    def comprehensive_fix_file(self, file_path: str) -> bool:
        """全面修復文件中的語法問題"""
        try:
            # 讀取原始內容
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 創建內容副本進行修改
            content = original_content
            
            # 修復缺少冒號的問題
            content = self.fix_missing_colons(content)
            
            # 修復縮進問題
            content = self.fix_indentation_issues(content)
            
            # 修復其他常見語法問題
            content = self.fix_syntax_issues(content)
            
            # 只有在內容有變化時才寫入文件
            if content != original_content:
                # 驗證修復後的語法
                try:
                    ast.parse(content)
                    # 語法正確，寫入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Successfully fixed syntax issues in {file_path}")
                    return True
                except SyntaxError as e:
                    # 修復後仍有語法錯誤，不寫入文件
                    print(f"Warning: Fix for {file_path} resulted in invalid syntax, skipped")
                    return False
            else:
                print(f"No issues found in {file_path}")
                return False
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            traceback.print_exc()
            return False
    
    def run_fix_on_files(self) -> dict:
        """对指定文件运行修复"""
        if not self.target_files:
            return {
                "status": "error",
                "message": "未设置待修复文件",
                "files_fixed": 0,
                "errors": []
            }
        
        print(f"开始修复 {len(self.target_files)} 个文件...")
        
        # 应用修复
        results = {
            "status": "partial",
            "files_fixed": 0,
            "total_files": len(self.target_files),
            "errors": []
        }
        
        # 对每个文件应用修复
        for file_path in self.target_files:
            print(f"正在修复: {file_path}")
            
            # 检查文件是否有语法错误
            has_error, error_msg = self.has_syntax_error(file_path)
            if not has_error:
                print(f"  文件无语法错误，跳过")
                continue
                
            print(f"  错误: {error_msg}")
            
            try:
                if self.comprehensive_fix_file(file_path):
                    results["files_fixed"] += 1
                    self.applied_fixes.append({
                        "file": file_path,
                        "error": error_msg
                    })
                else:
                    results["errors"].append({
                        "file": file_path,
                        "error": error_msg,
                        "message": "修复失败"
                    })
            except Exception as e:
                print(f"  修复时出错: {str(e)}")
                results["errors"].append({
                    "file": file_path,
                    "error": error_msg,
                    "message": f"修复时出错: {str(e)}"
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
    
    def run_fix_on_code(self) -> dict:
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
            
            # 尝试应用修复
            try:
                # 将代码写入临时文件并尝试修复
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.target_code)
                
                if self.comprehensive_fix_file(temp_file_path):
                    print("  代码修复成功")
                    # 读取修复后的代码
                    with open(temp_file_path, 'r', encoding='utf-8') as f:
                        fixed_code = f.read()
                    
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
                        "message": "无法修复代码",
                        "fixed_code": self.target_code,
                        "error": original_error
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"修复代码时出错: {str(e)}",
                    "fixed_code": self.target_code,
                    "error": str(e)
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
    print("统一自动修复系统")
    print("=" * 30)
    print("使用方式：")
    print("1. 启动系统")
    print("2. 输入待修复的文件路径或代码")
    print("3. 输入'开始修复'执行修复")
    print("4. 查看修复结果")
    print("5. 输入'退出'退出系统")
    print("=" * 30)
    
    # 创建统一修复系统实例
    fix_system = UnifiedAutoFixSystem()
    
    while True:
        print("\n请选择操作:")
        print("1. 设置待修复文件")
        print("2. 设置待修复代码")
        print("3. 开始修复")
        print("4. 查看修复报告")
        print("5. 修复整个项目")
        print("6. 退出")
        
        choice = input("请输入选择 (1-6): ").strip()
        
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
            print("\n开始修复整个项目...")
            files_with_errors = fix_system.get_files_with_syntax_errors()
            if files_with_errors:
                file_paths = [file_info[0] for file_info in files_with_errors]
                fix_system.set_target_files(file_paths)
                results = fix_system.run_fix_on_files()
                print("\n项目修复结果:")
                print(f"  状态: {results['status']}")
                print(f"  消息: {results['message']}")
                print(f"  修复文件数: {results['files_fixed']}")
                
                if results["errors"]:
                    print(f"\n无法修复的文件 ({len(results['errors'])}):")
                    for error in results["errors"][:5]:  # 只显示前5个错误
                        print(f"  {error['file']}: {error['error']}")
                    if len(results["errors"]) > 5:
                        print(f"  ... 还有 {len(results['errors']) - 5} 个文件")
            else:
                print("项目中未发现有语法错误的文件")
                
        elif choice == "6":
            print("退出系统...")
            break
            
        else:
            print("无效选择，请重新输入")


def main():
    """主函数"""
    interactive_mode()


if __name__ == "__main__":
    main()