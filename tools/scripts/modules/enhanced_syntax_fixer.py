#!/usr/bin/env python3
"""
增强版语法修复模块 - 使用AST和机器学习技术进行更精确的语法修复
"""

import re
import ast
import traceback
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 尝试导入机器学习相关库
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("警告: 未安装机器学习库，将使用基础修复功能")

class ErrorType(Enum):
    """错误类型枚举"""
    INDENTATION = "indentation"
    SYNTAX = "syntax"
    IMPORT = "import"
    NAMING = "naming"
    OTHER = "other"

@dataclass
class ErrorInfo:
    """错误信息类"""
    file_path: Path
    line_number: int
    error_type: ErrorType
    message: str
    code_snippet: str
    severity: str  # low, medium, high

class EnhancedSyntaxFixer:
    """增强版语法修复器"""
    
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        
        # 初始化机器学习模型（如果可用）
        self.ml_model = None
        if ML_AVAILABLE:
            _ = self._initialize_ml_model()
        
        # 修复历史记录
        self.fix_history = []
        
        # 常见的语法问题模式
        self.indentation_patterns = [
            # 异步函数定义后的缩进问题
            (r'(async def\s+\w+\([^)]*\):\s*\n)(\s+)(?=\w)', lambda m: m.group(1) + '    '),
            # 类方法定义后的缩进问题
            (r'(def\s+\w+\([^)]*\):\s*\n)(\s+)(?=\w)', lambda m: m.group(1) + '    '),
            # if/for/while语句后的缩进问题
            (r'((?:if|for|while|with|try)\s+[^:]+:\s*\n)(\s+)(?=\w)', lambda m: m.group(1) + '    '),
            # 处理不一致的缩进
            (r'(\n)(\s*)(if\s+.*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
            (r'(\n)(\s*)(for\s+.*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
            (r'(\n)(\s*)(while\s+.*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
            (r'(\n)(\s*)(try\s*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
            (r'(\n)(\s*)(except\s+.*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
            (r'(\n)(\s*)(else\s*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
            (r'(\n)(\s*)(elif\s+.*?:)\n(\s{1,3})(\w+)', lambda m: m.group(1) + m.group(2) + m.group(3) + '\n' + m.group(2) + '    ' + m.group(5)),
        ]
        
        # 常见的语法错误修复
        self.syntax_fixes = [
            # 修复缺少的冒号
            (r'(async def\s+\w+\([^)]*\))(\s*\n)(?=\s+\w)', lambda m: m.group(1) + ':' + m.group(2)),
            (r'(def\s+\w+\([^)]*\))(\s*\n)(?=\s+\w)', lambda m: m.group(1) + ':' + m.group(2)),
            (r'((?:if|for|while|with|try)\s+[^:\n]+)(\s*\n)(?=\s+\w)', lambda m: m.group(1) + ':' + m.group(2)),
            # 修复多余的冒号（更精确的模式）
            (r'(return\s+["\'][^"\']*["\']):\s*(\n)', lambda m: m.group(1) + m.group(2)),
            (r'(return\s+[^"\':,\n]+):\s*(\n)', lambda m: m.group(1) + m.group(2)),
            # 修复缩进问题
            (r'(\n\s+)(if\s+.*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
            (r'(\n\s+)(elif\s+.*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
            (r'(\n\s+)(else\s*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
            (r'(\n\s+)(for\s+.*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
            (r'(\n\s+)(while\s+.*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
            (r'(\n\s+)(try\s*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
            (r'(\n\s+)(except\s+.*?:)\n(\s*)(\w+)', lambda m: m.group(1) + m.group(2) + '\n' + m.group(1) + '    ' + m.group(4)),
        ]
        
    def _initialize_ml_model(self):
        """初始化机器学习模型"""
        try:
            # 创建示例训练数据
            training_data = [
                ("def function_name  :", "syntax"),  # 缺少括号
                ("async def function_name  :", "syntax"),  # 缺少括号
                ("if condition  :", "syntax"),  # 缺少条件
                ("for item in list  :", "syntax"),  # 缺少条件
                ("    print('hello')", "indentation"),  # 缩进不一致
                ("        print('hello')", "indentation"),  # 缩进过多
                ("import os", "import"),  # 正确的导入
                ("from os import path", "import"),  # 正确的导入
                ("variable_name = 10", "naming"),  # 正确的命名
                ("VariableName = 10", "naming"),  # 驼峰命名
            ]
            
            # 创建训练数据和标签
            texts = [item[0] for item in training_data]
            labels = [item[1] for item in training_data]
            
            # 创建管道
            self.ml_model = Pipeline([
                ('tfidf', TfidfVectorizer()),
                ('classifier', MultinomialNB())
            ])
            
            # 训练模型
            _ = self.ml_model.fit(texts, labels)
            
        except Exception as e:
            _ = print(f"初始化机器学习模型时出错: {e}")
            self.ml_model = None
    
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
                    ".git", "dist", "build", "data/runtime_data/.pytest_cache"
                ]):
                    continue
                # 跳过自动修复工具自身，避免循环修复问题
                if "unified_auto_fix.py" in str(py_file):
                    continue
                _ = python_files.append(py_file)
                
        return python_files
        
    def check_syntax_errors(self, file_path: Path) -> List[ErrorInfo]:
        """检查语法错误"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
                
            # 尝试解析AST
            try:
                ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                # 获取错误附近的代码片段
                line_number = e.lineno or 1
                start_line = max(1, line_number - 2)
                end_line = min(len(lines), line_number + 2)
                code_snippet = '\n'.join(lines[start_line-1:end_line])
                
                error_info = ErrorInfo(
                    file_path=file_path,
                    line_number=line_number,
                    error_type=ErrorType.SYNTAX,
                    message=e.msg,
                    code_snippet=code_snippet,
                    severity="high"
                )
                _ = errors.append(error_info)
                
            # 检查常见的缩进问题
            for i, line in enumerate(lines, 1):
                # 检查混合缩进（空格和制表符）
                if '\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                    error_info = ErrorInfo(
                        file_path=file_path,
                        line_number=i,
                        error_type=ErrorType.INDENTATION,
                        message="混合使用空格和制表符进行缩进",
                        code_snippet=line,
                        severity="medium"
                    )
                    _ = errors.append(error_info)
                    
                # 检查不一致的缩进（4的倍数）
                stripped = line.lstrip()
                if stripped:  # 非空行
                    indent = len(line) - len(stripped)
                    if indent % 4 != 0:
                        error_info = ErrorInfo(
                            file_path=file_path,
                            line_number=i,
                            error_type=ErrorType.INDENTATION,
                            message=f"缩进不是4的倍数: {indent}个空格",
                            code_snippet=line,
                            severity="low"
                        )
                        _ = errors.append(error_info)
                        
        except Exception as e:
            error_info = ErrorInfo(
                file_path=file_path,
                line_number=0,
                error_type=ErrorType.OTHER,
                message=f"读取文件时出错: {str(e)}",
                code_snippet="",
                severity="high"
            )
            _ = errors.append(error_info)
            
        return errors
        
    def classify_error(self, error_info: ErrorInfo) -> ErrorType:
        """使用机器学习模型分类错误类型"""
        if not self.ml_model:
            return error_info.error_type
            
        try:
            # 使用模型预测错误类型
            prediction = self.ml_model.predict([error_info.code_snippet])
            if prediction and len(prediction) > 0:
                predicted_type = prediction[0]
                if predicted_type == "indentation":
                    return ErrorType.INDENTATION
                elif predicted_type == "syntax":
                    return ErrorType.SYNTAX
                elif predicted_type == "import":
                    return ErrorType.IMPORT
                elif predicted_type == "naming":
                    return ErrorType.NAMING
        except Exception as e:
            _ = print(f"分类错误时出错: {e}")
            
        return error_info.error_type
        
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
                    "file": str(file_path),
                    "fixes_count": len(fixes_made),
                    "fixes_made": fixes_made
                }
                
                # 记录修复历史
                _ = self.fix_history.append({
                    "file": str(file_path),
                    "type": "indentation",
                    "fixes": fixes_made,
                    "timestamp": __import__('time').strftime("%Y-%m-%d %H:%M:%S")
                })
                
                return True, f"修复了 {len(fixes_made)} 处缩进问题", details
            else:
                return True, "无需修复", {"file": str(file_path), "fixes_count": 0}
                
        except Exception as e:
            details = {
                "file": str(file_path),
                "error": str(e),
                "traceback": traceback.format_exc()
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
                    # 在应用修复前，先备份内容
                    backup_content = content
                    content = re.sub(pattern, replacement, content)
                    
                    # 验证修复后的语法是否正确
                    try:
                        ast.parse(content, filename=str(file_path))
                        _ = fixes_made.append(f"语法修复: 应用模式 {pattern}")
                    except SyntaxError:
                        # 如果修复后语法不正确，回滚到修复前的内容
                        content = backup_content
                        _ = fixes_made.append(f"语法修复回滚: 模式 {pattern} 导致语法错误")
            
            # 如果内容有变化，写入文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    _ = f.write(content)
                    
                details = {
                    "file": str(file_path),
                    "fixes_count": len(fixes_made),
                    "fixes_made": fixes_made
                }
                
                # 记录修复历史
                _ = self.fix_history.append({
                    "file": str(file_path),
                    "type": "syntax",
                    "fixes": fixes_made,
                    "timestamp": __import__('time').strftime("%Y-%m-%d %H:%M:%S")
                })
                
                return True, f"修复了 {len(fixes_made)} 处语法错误", details
            else:
                return True, "无需修复语法", {"file": str(file_path), "fixes_count": 0}
                
        except Exception as e:
            details = {
                "file": str(file_path),
                "error": str(e),
                "traceback": traceback.format_exc()
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
                "message": f"验证时出错: {str(e)}"
            }]
            return False, errors
            
    def get_fix_history(self) -> List[Dict]:
        """获取修复历史"""
        return self.fix_history
        
    def save_fix_history(self, file_path: Optional[Path] = None):
        """保存修复历史到文件"""
        if file_path is None:
            file_path = self.project_root / "syntax_fix_history.json"
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.fix_history, f, ensure_ascii=False, indent=2)
            _ = print(f"✓ 修复历史已保存到 {file_path}")
        except Exception as e:
            _ = print(f"✗ 保存修复历史时出错: {e}")
            
    def fix(self, target: str = None, **kwargs) -> Tuple[bool, str, Dict]:
        """执行语法修复"""
        _ = print("开始执行增强版语法修复...")
        
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
                    
                    # 分类错误并按类型修复
                    indentation_errors = [e for e in syntax_errors if e.error_type == ErrorType.INDENTATION]
                    syntax_errors_filtered = [e for e in syntax_errors if e.error_type == ErrorType.SYNTAX]
                    
                    # 修复缩进问题
                    if indentation_errors:
                        success, message, details = self.fix_indentation_issues(file_path)
                        if success and details.get("fixes_count", 0) > 0:
                            indentation_fixed += 1
                            _ = print(f"  ✓ 修复缩进: {message}")
                    
                    # 修复语法错误
                    if syntax_errors_filtered:
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
                            "file": str(file_path),
                            "errors": remaining_errors
                        })
                        _ = print(f"  ✗ 验证失败: {file_path}")
                else:
                    validation_passed += 1
                    _ = print(f"- 无语法问题: {file_path}")
                    
            except Exception as e:
                error_msg = f"处理文件时发生异常: {str(e)}"
                errors.append({
                    "file": str(file_path),
                    "error": error_msg,
                    "traceback": traceback.format_exc()
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
        
        # 保存修复历史
        _ = self.save_fix_history()
        
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
    fixer = EnhancedSyntaxFixer(project_root)
    
    success, message, details = fixer.fix()
    _ = print(f"结果: {success}")
    _ = print(f"消息: {message}")
    _ = print(f"详情: {details}")

if __name__ == "__main__":
    _ = main()