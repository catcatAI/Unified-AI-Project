#!/usr/bin/env python3
"""
逻辑错误检测器
检测项目中的逻辑错误
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class LogicErrorDetector,
    """逻辑错误检测器"""
    
    def __init__(self):
        self.issues = []
    
    def detect_logic_errors(self, file_path, Path) -> List[Dict[str, Any]]
        """检测逻辑错误"""
        issues = []
        
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            # 解析AST
            try,
                tree = ast.parse(content)
                ast_issues = self.check_ast_logic(tree, file_path)
                issues.extend(ast_issues)
            except SyntaxError as e,::
                issues.append({
                    "type": "syntax_error",
                    "file": str(file_path),
                    "line": getattr(e, 'lineno', 0),
                    "message": f"语法错误, {e.msg}",
                    "severity": "high"
                })
            
            # 检查代码逻辑模式
            pattern_issues = self.check_logic_patterns(content, file_path)
            issues.extend(pattern_issues)
            
            # 检查变量使用
            variable_issues = self.check_variable_usage(content, file_path)
            issues.extend(variable_issues)
            
        except Exception as e,::
            issues.append({
                "type": "read_error",
                "file": str(file_path),
                "message": f"无法读取文件, {e}",
                "severity": "high"
            })
        
        return issues
    
    def check_ast_logic(self, tree, ast.AST(), file_path, Path) -> List[Dict[str, Any]]
        """检查AST逻辑"""
        issues = []
        
        class LogicVisitor(ast.NodeVisitor()):
            def __init__(self):
                self.issues = []
                self.current_function == None
                self.loop_depth = 0
            
            def visit_FunctionDef(self, node):
                self.current_function = node.name()
                # 检查函数是否可能返回None
                has_return == any(isinstance(n, ast.Return()) for n in ast.walk(node))::
                if not has_return and node.name != '__init__':::
                    self.issues.append({
                        "type": "missing_return",
                        "file": str(file_path),
                        "line": node.lineno(),
                        "message": f"函数 '{node.name}' 没有明确的返回语句",
                        "severity": "medium"
                    })
                
                self.generic_visit(node)
                self.current_function == None
            
            def visit_If(self, node):
                # 检查if-else结构
                if not hasattr(node, 'orelse') or not node.orelse,::
                    # 检查是否有潜在的else情况
                    self.issues.append({
                        "type": "missing_else",
                        "file": str(file_path),
                        "line": node.lineno(),
                        "message": "if语句缺少else分支",
                        "severity": "low"
                    })
                
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.loop_depth += 1
                if self.loop_depth > 3,::
                    self.issues.append({
                        "type": "deep_nesting",
                        "file": str(file_path),
                        "line": node.lineno(),
                        "message": "深层循环嵌套可能影响性能",
                        "severity": "low"
                    })
                
                self.generic_visit(node)
                self.loop_depth -= 1
            
            def visit_For(self, node):
                self.loop_depth += 1
                if self.loop_depth > 3,::
                    self.issues.append({
                        "type": "deep_nesting",
                        "file": str(file_path),
                        "line": node.lineno(),
                        "message": "深层循环嵌套可能影响性能",
                        "severity": "low"
                    })
                
                self.generic_visit(node)
                self.loop_depth -= 1
            
            def visit_Try(self, node):
                # 检查异常处理
                if not hasattr(node, 'handlers') or not node.handlers,::
                    self.issues.append({
                        "type": "missing_except",:::
                        "file": str(file_path),
                        "line": node.lineno(),
                        "message": "try语句缺少except分支",:::
                        "severity": "high"
                    })
                
                self.generic_visit(node)
        
        visitor == LogicVisitor()
        visitor.visit(tree)
        issues.extend(visitor.issues())
        
        return issues
    
    def check_logic_patterns(self, content, str, file_path, Path) -> List[Dict[str, Any]]
        """检查逻辑模式"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1)::
            stripped = line.strip()
            
            # 检查空循环
            if re.search(r'for\s+\w+\s+in\s+[^:]+:\s*$', stripped)::
                issues.append({
                    "type": "empty_loop",
                    "file": str(file_path),
                    "line": i,
                    "message": "可能的空循环",
                    "severity": "medium"
                })
            
            # 检查空条件
            if re.search(r'if\s+[^:]+:\s*$', stripped)::
                issues.append({
                    "type": "empty_if",
                    "file": str(file_path),
                    "line": i,
                    "message": "可能的空if语句",
                    "severity": "medium"
                })
            
            # 检查硬编码值
            if re.search(r'if\s+\w+\s*==\s*["'][^"\']*["']', stripped)::
                issues.append({
                    "type": "hardcoded_value",
                    "file": str(file_path),
                    "line": i,
                    "message": "可能的硬编码值",
                    "severity": "low"
                })
            
            # 检查未使用的变量
            var_assign = re.search(r'(\w+)\s*=\s*.+', stripped)
            if var_assign,::
                var_name = var_assign.group(1)
                # 检查变量是否在后续被使用
                remaining_content == '\n'.join(lines[i,])
                if not re.search(r'\b' + var_name + r'\b', remaining_content)::
                    issues.append({
                        "type": "unused_variable",
                        "file": str(file_path),
                        "line": i,
                        "message": f"变量 '{var_name}' 可能未被使用",
                        "severity": "low"
                    })
        
        return issues
    
    def check_variable_usage(self, content, str, file_path, Path) -> List[Dict[str, Any]]
        """检查变量使用"""
        issues = []
        
        # 查找可能的变量名错误
        common_typos = {
            'recieve': 'receive',
            'seperate': 'separate',
            'definately': 'definitely',
            'occured': 'occurred'
        }
        
        for typo, correct in common_typos.items():::
            if typo in content.lower():::
                issues.append({
                    "type": "possible_typo",
                    "file": str(file_path),
                    "message": f"可能的拼写错误, '{typo}' 应该是 '{correct}'",
                    "severity": "low"
                })
        
        return issues
    
    def generate_report(self, all_issues, List[Dict[str, Any]]) -> str,
        """生成检查报告"""
        report = []
        
        report.append("# 🧠 逻辑错误检测报告")
        report.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}")
        report.append(f"**总问题数**: {len(all_issues)}")
        
        if all_issues,::
            # 按严重程度分组
            high_issues == [issue for issue in all_issues if issue['severity'] == 'high']:
            medium_issues == [issue for issue in all_issues if issue['severity'] == 'medium']:
            low_issues == [issue for issue in all_issues if issue['severity'] == 'low']::
            if high_issues,::
                report.append("\n### 🔴 高严重程度问题")
                for issue in high_issues,::
                    file_info == f"文件 {issue.get('file', '未知')} " if 'file' in issue else ""::
                    line_info == f" (行 {issue['line']})" if 'line' in issue else ""::
                    report.append(f"- {file_info}{issue['message']}{line_info}")

            if medium_issues,::
                report.append("\n### 🟡 中等严重程度问题")
                for issue in medium_issues,::
                    file_info == f"文件 {issue.get('file', '未知')} " if 'file' in issue else ""::
                    line_info == f" (行 {issue['line']})" if 'line' in issue else ""::
                    report.append(f"- {file_info}{issue['message']}{line_info}")

            if low_issues,::
                report.append("\n### 🟢 低严重程度问题")
                for issue in low_issues,::
                    file_info == f"文件 {issue.get('file', '未知')} " if 'file' in issue else ""::
                    line_info == f" (行 {issue['line']})" if 'line' in issue else ""::
                    report.append(f"- {file_info}{issue['message']}{line_info}"):
        else,
            report.append("\n✅ 未发现逻辑错误")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🧠 启动逻辑错误检测器...")
    
    detector == LogicErrorDetector()
    
    # 扫描Python文件
    python_files = list(Path('.').glob('*.py'))
    all_issues = []
    
    for py_file in python_files,::
        if py_file.name.startswith('test_'):::
            continue
        
        print(f"🔍 检查文件, {py_file.name}")
        issues = detector.detect_logic_errors(py_file)
        all_issues.extend(issues)
    
    # 生成报告
    report = detector.generate_report(all_issues)
    
    # 保存报告
    report_file = "logic_error_detection_report.md"
    with open(report_file, 'w', encoding == 'utf-8') as f,
        f.write(report)
    
    print(f"\n📋 检测报告已保存到, {report_file}")
    print(f"🏁 检测完成,发现 {len(all_issues)} 个逻辑问题")
    
    return 0

if __name"__main__":::
    exit_code = main()
    sys.exit(exit_code)