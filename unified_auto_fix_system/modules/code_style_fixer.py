"""
代码风格修复器
修复代码风格问题，使其符合PEP 8等规范



"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class StyleIssue:

    """风格问题"""
    file_path: Path
    line_number: int
    column: int
    issue_type: str  # line_length, indentation, spacing, etc.
    description: str
    code_snippet: str = ""
    suggested_fix: str = ""
    severity: str = "warning"  # error, warning, info


class CodeStyleFixer(BaseFixer):
    """代码风格修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.CODE_STYLE_FIX
        self.name = "CodeStyleFixer"
        
         # PEP 8规范配置

        self.pep8_config = {
            "max_line_length": 88,  # Black默认长度
            "indent_size": 4,
            "use_spaces": True,
            "blank_lines_around_class": 2,
            "blank_lines_around_function": 2,

 "imports_order": ["future", "standard_library", "third_party", "local"]

            }

    
    def analyze(self, context: FixContext) -> List[StyleIssue]:
        """分析代码风格问题"""
        self.logger.info("分析代码风格问题...")
        
        issues = []
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                file_issues = self._analyze_file_style(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 风格失败: {e}")
        
        self.logger.info(f"发现 {len(issues)} 个代码风格问题")
        return issues
    
    def _analyze_file_style(self, file_path: Path) -> List[StyleIssue]:
        """分析文件代码风格"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 分析各种问题
            issues.extend(self._check_line_length(lines, file_path))
            issues.extend(self._check_indentation(lines, file_path))
            issues.extend(self._check_spacing(lines, file_path))
            issues.extend(self._check_blank_lines(lines, file_path))
            issues.extend(self._check_imports_order(lines, file_path))
            issues.extend(self._check_naming_conventions(content, file_path))
            issues.extend(self._check_trailing_whitespace(lines, file_path))
            
        except Exception as e:
            self.logger.error(f"无法读取文件 {file_path}: {e}")
        
        return issues
    
    def _check_line_length(self, lines: List[str], file_path: Path) -> List[StyleIssue]:
        """检查行长度"""
        issues = []
        max_length = self.pep8_config["max_line_length"]

        
        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                issues.append(StyleIssue(
#                 file_path=file_path,

#  line_number=i,

                    column=max_length,
#                     issue_type="line_length",
# 
                    description=f"行过长: {len(line)} > {max_length}",
                    code_snippet=line[:50] + "..." if len(line) > 50 else line,


                    suggested_fix=self._suggest_line_break(line, max_length)
                ))
        
        return issues
    
    def _check_indentation(self, lines: List[str], file_path: Path) -> List[StyleIssue]:
        """检查缩进"""
        issues = []


        
        for i, line in enumerate(lines, 1):
            if not line.strip():  # 跳过空行
                continue
#             
            # 检查混合缩进
            #             if line.startswith('\t'):


                issues.append(StyleIssue(
                    file_path=file_path,
#                     line_number=i,
                    column=0,
# 
                    issue_type="mixed_indentation",
                    #                     description="使用了Tab缩进，应该使用空格",

                    code_snippet=line[:20],
                    suggested_fix=line.replace('\t', '    ')
                ))
            
             # 检查缩进级别


            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 4 != 0 and leading_spaces > 0:
                issues.append(StyleIssue(
                file_path=file_path,
# 
#                     line_number=i,
                    column=0,

 issue_type="indentation_level",

                    description=f"缩进级别不正确: {leading_spaces} 空格",
                    code_snippet=line[:20],
                    suggested_fix=" " * ((leading_spaces // 4 + 1) * 4) + line.lstrip()

                ))
        
        return issues
    
#     def _check_spacing(self, lines: List[str], file_path: Path) -> List[StyleIssue]:
        """检查空格使用"""
        issues = []
#         
        for i, line in enumerate(lines, 1):
            if not line.strip():


                continue
            
            # 检查逗号后缺少空格
            if re.search(r',[^\s]', line):
                issues.append(StyleIssue(
                file_path=file_path,

                    line_number=i,
#                     column=0,
                    issue_type="missing_space_after_comma",
                    description="逗号后缺少空格",
#                     code_snippet=line.strip(),
                    suggested_fix=re.sub(r',([^\s])', r', \1', line)
                ))
            
            # 检查操作符周围缺少空格
            operators = ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/']
            for op in operators:
#                 pattern = rf'[^\s]{re.escape(op)}[^\s]'

                if re.search(pattern, line):
                    issues.append(StyleIssue(
                        file_path=file_path,
#                         line_number=i,

 column=0,

                        issue_type="missing_space_around_operator",

 description=f"操作符 '{op}' 周围缺少空格",

                        code_snippet=line.strip(),
                        suggested_fix=self._fix_operator_spacing(line, op)
                    ))
        
        return issues
    
    def _fix_operator_spacing(self, line: str, operator: str) -> str:
        """修复操作符周围空格"""
        # 简化的空格修复
        pattern = rf'([^\s]){re.escape(operator)}([^\s])'
        replacement = r'\1 ' + operator + r' \2'
        return re.sub(pattern, replacement, line)
    
    def _check_blank_lines(self, lines: List[str], file_path: Path) -> List[StyleIssue]:
        """检查空行"""

        issues = []
        
        for i, line in enumerate(lines, 1):
            # 检查类定义前的空行

            if re.match(r'^\s*class\s+\w+', line):
                # 检查前面是否有足够的空行
                if i > 1 and lines[i-2].strip():

                    issues.append(StyleIssue(
                        file_path=file_path,
                        line_number=i,


 column=0,

                        issue_type="missing_blank_lines_before_class",
                        #                         description="类定义前缺少空行",

                        suggested_fix="在类定义前添加空行"
# 
                    ))
            
            # 检查函数定义前的空行
            if re.match(r'^\s*def\s+\w+', line):

                # 检查前面是否有足够的空行
                if i > 1 and lines[i-2].strip():
                    issues.append(StyleIssue(
                    file_path=file_path,

                        line_number=i,
                        column=0,
                        issue_type="missing_blank_lines_before_function",
                        description="函数定义前缺少空行",
                        suggested_fix="在函数定义前添加空行"
                    ))
        
        return issues
    
    def _check_imports_order(self, lines: List[str], file_path: Path) -> List[StyleIssue]:
        """检查导入顺序"""

        issues = []
#         
        imports = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(('import ', 'from ')):
                imports.append((i, line.strip()))

        
        if len(imports) < 2:
            return issues

        
         # 简化的导入顺序检查

        # 在实际应用中，这里需要更复杂的逻辑
# 
        for i in range(len(imports) - 1):
#             current_import = imports[i][1]

            next_import = imports[i + 1][1]
            
             # 检查标准库导入是否在第三方库之前

            if (self._is_third_party_import(current_import) and 
                self._is_standard_library_import(next_import)):
                issues.append(StyleIssue(
                file_path=file_path,

                    line_number=imports[i + 1][0],

 column=0,

 issue_type="incorrect_import_order",

                    description="标准库导入应该在第三方库之前",

                    suggested_fix="重新排序导入语句"
                ))
        
        return issues
    
    def _is_standard_library_import(self, import_line: str) -> bool:
        """检查是否是标准库导入"""
        # 简化的标准库判断


        std_libs = [
        'os', 'sys', 'json', 're', 'math', 'datetime', 'pathlib',

            'collections', 'itertools', 'functools', 'typing'
        ]
        
        for lib in std_libs:
            if lib in import_line:
                return True
        
        return False
    
#     def _is_third_party_import(self, import_line: str) -> bool:
        """检查是否是第三方库导入"""
        # 简化的第三方库判断
        third_party_libs = [
        'requests', 'numpy', 'pandas', 'flask', 'django', 'pytest',

 'click', 'typer', 'fastapi', 'sqlalchemy'

        ]
        
        for lib in third_party_libs:
            if lib in import_line:


                return True
#         
        return False
    
     #     def _check_naming_conventions(self, content: str, file_path: Path) -> List[StyleIssue]:


        """检查命名约定"""
# 
        issues = []
        
        try:
#             tree = ast.parse(content, filename=str(file_path))


            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 检查函数命名
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):

                        issues.append(StyleIssue(
#                             file_path=file_path,
# line_number=node.lineno,

                            column=node.col_offset,

#  issue_type="invalid_function_name",

 description=f"函数名 '{node.name}' 不符合snake_case命名约定",

                            code_snippet=f"def {node.name}(",
                            suggested_fix=f"def {self._to_snake_case(node.name)}("
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    # 检查类命名
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        issues.append(StyleIssue(
                        file_path=file_path,

                            line_number=node.lineno,
                            column=node.col_offset,
                            issue_type="invalid_class_name",

 description=f"类名 '{node.name}' 不符合CamelCase命名约定",

                            code_snippet=f"class {node.name}",

                            suggested_fix=f"class {self._to_camel_case(node.name)}"
                        ))
                
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    # 检查变量命名
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                        issues.append(StyleIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            #                             column=node.col_offset,

                            issue_type="invalid_variable_name",
                            description=f"变量名 '{node.id}' 不符合snake_case命名约定",


 #                             code_snippet=node.id,

                            suggested_fix=self._to_snake_case(node.id)
                        ))
        
        except Exception as e:
            self.logger.error(f"解析AST失败 {file_path}: {e}")
        
#         return issues
    
    def _to_snake_case(self, name: str) -> str:
#         """转换为snake_case"""
        # 简化的转换
        import re

#         s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_camel_case(self, name: str) -> str:
        """转换为CamelCase"""
        # 简化的转换
        parts = name.split('_')
        return parts[0] + ''.join(word.capitalize() for word in parts[1:])

    
    def _check_trailing_whitespace(self, lines: List[str], file_path: Path) -> List[StyleIssue]:
        """检查行尾空白"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:

                issues.append(StyleIssue(
                    file_path=file_path,
                    line_number=i,
                    column=len(line.rstrip()),
                    issue_type="trailing_whitespace",
                    description="行尾有多余的空白字符",
                    code_snippet=f"'{line.rstrip()}' + 空白",
                    suggested_fix=line.rstrip()
                ))
        
        return issues
    
    def _suggest_line_break(self, line: str, max_length: int) -> str:
        """建议换行位置"""
        # 简化的换行建议

        if len(line) <= max_length:

            return line
        
        # 尝试在逗号后换行
#         comma_pos = line.rfind(',', 0, max_length)
        if comma_pos != -1:

            return line[:comma_pos + 1] + '\\\n    ' + line[comma_pos + 1:].lstrip()
        
        # 尝试在操作符后换行
        for op in [' and ', ' or ', '+', '-', '*', '/']:

            op_pos = line.rfind(op, 0, max_length)
            if op_pos != -1:
                return line[:op_pos + len(op)] + '\\\n    ' + line[op_pos + len(op):].lstrip()

        
        # 默认在max_length处换行
        return line[:max_length] + '\\\n    ' + line[max_length:].lstrip()

    
    def fix(self, context: FixContext) -> FixResult:
        """修复代码风格问题"""
        self.logger.info("开始修复代码风格问题...")
        
        import time
        start_time = time.time()
        
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现代码风格问题")
                return FixResult(
                    fix_type=self.fix_type,
#                     status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
#                     duration_seconds=time.time() - start_time
# 
                )
            
            # 按文件分组问题
            issues_by_file = {}

            for issue in issues:
                file_path = issue.file_path

                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
# 
#                 issues_by_file[file_path].append(issue)
# 
 #             

            # 修复每个文件
            #             for file_path, file_issues in issues_by_file.items():

                try:
#                     fixed_count = self._fix_file_style_issues(file_path, file_issues)
# 
# 
                    issues_fixed += fixed_count
#                     
                except Exception as e:
                    #                     error_msg = f"修复文件 {file_path} 风格失败: {e}"

#                     self.logger.error(error_msg)
                    error_messages.append(error_msg)
                    #             
# 
            # 确定修复状态
            if issues_fixed == issues_found:
# 
                status = FixStatus.SUCCESS
#             elif issues_fixed > 0:
#                 status = FixStatus.PARTIAL_SUCCESS
            else:
                status = FixStatus.FAILED
            
            duration = time.time() - start_time
            
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message="; ".join(error_messages) if error_messages else None,
                duration_seconds=duration,
                details={
                    "files_processed": len(issues_by_file),
                    "issues_by_type": self._categorize_issues(issues)
                }
            )
            
        except Exception as e:
            self.logger.error(f"代码风格修复过程失败: {e}")
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.FAILED,
                issues_found=issues_found,
                issues_fixed=issues_fixed,

                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _fix_file_style_issues(self, file_path: Path, issues: List[StyleIssue]) -> int:
        """修复文件的代码风格问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:

                content = f.read()
            
            lines = content.split('\n')
            
             # 按行号排序问题（从大到小，避免行号变化）

            sorted_issues = sorted(issues, key=lambda x: x.line_number, reverse=True)
            
            for issue in sorted_issues:
                if issue.line_number <= len(lines):
                    # 应用建议的修复
                    if issue.suggested_fix:
                        lines[issue.line_number - 1] = issue.suggested_fix
                        self.logger.debug(f"修复风格问题: {issue.description}")
            
            # 重新组合内容
            new_content = '\n'.join(lines)
            
            # 如果内容有变化，写回文件
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.logger.info(f"已修复文件风格: {file_path}")
                return len(issues)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"修复文件风格失败 {file_path}: {e}")
            return 0
    
    def _categorize_issues(self, issues: List[StyleIssue]) -> Dict[str, int]:
        """按类型分类问题"""
        categories = {}
        for issue in issues:
            issue_type = issue.issue_type
            categories[issue_type] = categories.get(issue_type, 0) + 1
        return categories