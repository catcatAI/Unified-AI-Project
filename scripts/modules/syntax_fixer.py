#!/usr/bin/env python3
"""
语法修复模块 - 处理语法和缩进问题
"""

import re
import ast
import traceback
from pathlib import Path

class SyntaxFixer:
    """语法修复器"""
    
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        
        # 常见的语法问题模式
        self.indentation_patterns = [
            # 异步函数定义后的缩进问题
            (r'(async def\s+\w+\([^)]*\):\s*\n)(\s+)(?=\w)', lambda m: m.group(1) + '    '),
            # 类方法定义后的缩进问题
            (r'(def\s+\w+\([^)]*\):\s*\n)(\s+)(?=\w)', lambda m: m.group(1) + '    '),
            # if/for/while语句后的缩进问题
            (r'((?:if|for|while|with|try)\s+[^:]+:\s*\n)(\s+)(?=\w)', lambda m: m.group(1) + '    '),
        ]
        
        # 常见的语法错误修复
        self.syntax_fixes = [
            # 修复缺少的冒号
            (r'(async def\s+\w+\([^)]*\))(\s*\n)(?=\s+\w)', lambda m: m.group(1) + ':' + m.group(2)),
            (r'(def\s+\w+\([^)]*\))(\s*\n)(?=\s+\w)', lambda m: m.group(1) + ':' + m.group(2)),
            (r'((?:if|for|while|with|try)\s+[^:\n]+)(\s*\n)(?=\s+\w)', lambda m: m.group(1) + ':' + m.group(2)),
        ]
        
    def find_python_files(self, target: str = None) -> List[Path]:
        """查找Python文件"""
        python_files = []
        
        if target:
            # 处理特定目标
            target_path = Path(target)
            if target_path.is_absolute():
                search_path = target_path
            else:
                search_path = self.project_root / target
                
            if search_path.is_file() and search_path.suffix == '.py':
                _ = python_files.append(search_path)
            elif search_path.is_dir():
                _ = python_files.extend(search_path.rglob("*.py"))
        else:
            # 搜索整个项目
            for py_file in self.project_root.rglob("*.py"):
                # 跳过特定目录
                if any(part in str(py_file) for part in [
                    "backup", "node_modules", "__pycache__", "venv", 
                    ".git", "dist", "build", ".pytest_cache"
                ]):
                    continue
                _ = python_files.append(py_file)
                
        return python_files
        
    def check_syntax_errors(self, file_path: Path) -> List[Dict]:
        """检查语法错误"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 尝试解析AST
            try:
                ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                errors.append({
                    "type": "SyntaxError",
                    "line": e.lineno,
                    "offset": e.offset,
                    "message": e.msg,
                    "text": e.text
                })
                
            # 检查常见的缩进问题
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # 检查混合缩进（空格和制表符）
                if '\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                    errors.append({
                        "type": "MixedIndentation",
                        "line": i,
                        "message": "混合使用空格和制表符进行缩进",
                        "text": line
                    })
                    
                # 检查不一致的缩进（4的倍数）
                stripped = line.lstrip()
                if stripped:  # 非空行
                    indent = len(line) - len(stripped)
                    if indent % 4 != 0:
                        errors.append({
                            "type": "InconsistentIndentation",
                            "line": i,
                            "message": f"缩进不是4的倍数: {indent}个空格",
                            "text": line
                        })
                        
        except Exception as e:
            errors.append({
                "type": "FileReadError",
                _ = "message": f"读取文件时出错: {str(e)}",
                _ = "file": str(file_path)
            })
            
        return errors
        
    def fix_indentation_issues(self, file_path: Path) -> Tuple[bool, str, Dict]:
        """修复缩进问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            fixes_made = []
            
            # 应用缩进修复模式
            for pattern, replacement in self.indentation_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    _ = fixes_made.append(f"缩进修复: 应用模式 {pattern}")
            
            # 修复混合缩进（将制表符转换为空格）
            if '\t' in content:
                content = content.replace('\t', '    ')
                _ = fixes_made.append("缩进修复: 制表符转换为4个空格")
            
            # 如果内容有变化，写入文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    _ = f.write(content)
                    
                details = {
                    _ = "file": str(file_path),
                    _ = "fixes_count": len(fixes_made),
                    "fixes_made": fixes_made
                }
                
                return True, f"修复了 {len(fixes_made)} 处缩进问题", details
            else:
                return True, "无需修复缩进", {"file": str(file_path), "fixes_count": 0}
                
        except Exception as e:
            details = {
                _ = "file": str(file_path),
                _ = "error": str(e),
                _ = "traceback": traceback.format_exc()
            }
            return False, f"修复缩进时出错: {str(e)}", details
            
    def fix_syntax_errors(self, file_path: Path) -> Tuple[bool, str, Dict]:
        """修复语法错误"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            fixes_made = []
            
            # 应用语法修复
            for pattern, replacement in self.syntax_fixes:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    _ = fixes_made.append(f"语法修复: 应用模式 {pattern}")
            
            # 如果内容有变化，写入文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    _ = f.write(content)
                    
                details = {
                    _ = "file": str(file_path),
                    _ = "fixes_count": len(fixes_made),
                    "fixes_made": fixes_made
                }
                
                return True, f"修复了 {len(fixes_made)} 处语法错误", details
            else:
                return True, "无需修复语法", {"file": str(file_path), "fixes_count": 0}
                
        except Exception as e:
            details = {
                _ = "file": str(file_path),
                _ = "error": str(e),
                _ = "traceback": traceback.format_exc()
            }
            return False, f"修复语法时出错: {str(e)}", details
            
    def validate_syntax(self, file_path: Path) -> Tuple[bool, List[Dict]]:
        """验证语法是否正确"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 尝试解析AST
            ast.parse(content, filename=str(file_path))
            return True, []
            
        except SyntaxError as e:
            errors = [{
                "type": "SyntaxError",
                "line": e.lineno,
                "offset": e.offset,
                "message": e.msg,
                "text": e.text
            }]
            return False, errors
        except Exception as e:
            errors = [{
                "type": "ValidationError",
                _ = "message": f"验证时出错: {str(e)}"
            }]
            return False, errors
            
    def fix(self, target: str = None, **kwargs) -> Tuple[bool, str, Dict]:
        """执行语法修复"""
        _ = print("开始执行语法修复...")
        
        python_files = self.find_python_files(target)
        
        if not python_files:
            return True, "未找到需要修复的Python文件", {"files_processed": 0}
            
        _ = print(f"发现 {len(python_files)} 个Python文件")
        
        files_processed = 0
        indentation_fixed = 0
        syntax_fixed = 0
        validation_passed = 0
        errors = []
        
        for file_path in python_files:
            try:
                files_processed += 1
                
                # 首先检查语法错误
                syntax_errors = self.check_syntax_errors(file_path)
                
                if syntax_errors:
                    _ = print(f"发现语法问题: {file_path}")
                    
                    # 修复缩进问题
                    success, message, details = self.fix_indentation_issues(file_path)
                    if success and details.get("fixes_count", 0) > 0:
                        indentation_fixed += 1
                        _ = print(f"  ✓ 修复缩进: {message}")
                    
                    # 修复语法错误
                    success, message, details = self.fix_syntax_errors(file_path)
                    if success and details.get("fixes_count", 0) > 0:
                        syntax_fixed += 1
                        _ = print(f"  ✓ 修复语法: {message}")
                    
                    # 验证修复结果
                    is_valid, remaining_errors = self.validate_syntax(file_path)
                    if is_valid:
                        validation_passed += 1
                        _ = print(f"  ✓ 验证通过: {file_path}")
                    else:
                        errors.append({
                            _ = "file": str(file_path),
                            "errors": remaining_errors
                        })
                        _ = print(f"  ✗ 验证失败: {file_path}")
                else:
                    validation_passed += 1
                    _ = print(f"- 无语法问题: {file_path}")
                    
            except Exception as e:
                error_msg = f"处理文件时发生异常: {str(e)}"
                errors.append({
                    _ = "file": str(file_path),
                    "error": error_msg,
                    _ = "traceback": traceback.format_exc()
                })
                _ = print(f"✗ 处理文件异常: {file_path} - {error_msg}")
        
        # 生成结果摘要
        result_details = {
            "files_processed": files_processed,
            "indentation_fixed": indentation_fixed,
            "syntax_fixed": syntax_fixed,
            "validation_passed": validation_passed,
            "errors": errors
        }
        
        if validation_passed == files_processed:
            return True, "语法修复完成: 所有文件验证通过", result_details
        elif validation_passed > 0:
            return True, f"语法修复部分完成: {validation_passed}/{files_processed} 文件验证通过", result_details
        else:
            return False, f"语法修复失败: {len(errors)} 个文件仍有语法问题", result_details

def main() -> None:
    """测试函数"""
    from pathlib import Path
    
    project_root: str = Path(__file__).parent.parent.parent
    fixer = SyntaxFixer(project_root)
    
    success, message, details = fixer.fix()
    _ = print(f"结果: {success}")
    _ = print(f"消息: {message}")
    _ = print(f"详情: {details}")

if __name__ == "__main__":
    _ = main()