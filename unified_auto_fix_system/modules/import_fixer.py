"""
导入路径修复器
修复Python导入路径问题,包括相对导入和绝对导入
"""

import ast
import re
import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class ImportIssue:
    """导入问题"""
    file_path: Path
    line_number: int
    import_statement: str
    issue_type: str  # absolute_import, relative_import, circular_import, missing_module, etc.
    target_module: str
    current_module: str
    suggested_fix: str = ""
    severity: str = "error"  # error, warning, info


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    path: Path
    is_package: bool
    imports: List[str]
    imported_by: List[str]


class ImportFixer(BaseFixer):
    """导入路径修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.IMPORT_FIX
        self.name = "ImportFixer"
        
        # 项目结构分析
        self.module_map = {}
        self.package_map = {}
        self._analyze_project_structure()
        
         # 常见导入问题模式

        self.import_patterns = {
            "absolute_import_issue": r"from\s+([\w.]+)\s+import",
            "relative_import_issue": r"from\s+(\.+[\w.]*)\s+import",
            "import_error": r"ImportError.*No module named ['\"]([\w.]+)['\"]",
            "module_not_found": r"ModuleNotFoundError.*No module named ['\"]([\w.]+)['\"]"
        }
        
        # 导入映射规则
        self.import_mappings = self._load_import_mappings()

    
    def _analyze_project_structure(self):
        """分析项目结构"""
        self.logger.info("分析项目结构...")
        
        # 查找所有Python模块
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            # 计算模块名
            module_name = self._calculate_module_name(py_file)
            
            # 检查是否是包
            is_package = py_file.name == "__init__.py"

            
            self.module_map[module_name] = ModuleInfo(
                name=module_name,
                path=py_file,
                is_package=is_package,
                imports=[],
                imported_by=[]
            )
            
            if is_package:
                package_name = module_name.rstrip('.')
                self.package_map[package_name] = py_file.parent
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """检查是否应该跳过文件"""
        skip_patterns = [
            "__pycache__", ".git", "node_modules", "venv", ".venv",
            "backup", "unified_fix_backups", "dist", "build", ".pytest_cache"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _calculate_module_name(self, file_path: Path) -> str:
        """计算模块名"""
        # 相对于项目根目录的路径
        relative_path = file_path.relative_to(self.project_root)
        
        # 转换为模块名
        module_parts = list(relative_path.parts[:-1])  # 去掉文件名
        
        if file_path.name != "__init__.py":
            module_name = file_path.stem
            if module_parts:
                return '.'.join(module_parts) + '.' + module_name
            else:
                return module_name
        else:
            # 包的情况
            if module_parts:
                return '.'.join(module_parts)
            else:
                return ""  # 根包
    
    def _load_import_mappings(self) -> Dict[str, str]:
        """加载导入映射"""
        # 项目特定的导入映射
        mappings = {
            # 常见的错误导入映射
            "apps.backend.src": "..",
            "apps.frontend_dashboard": "../../frontend-dashboard",
            "apps.desktop_app": "../../desktop-app",
            "core": "..core",
            "services": "..services",
            "utils": "..utils",
            "ai": "..ai",
            "memory": "..memory",
            "concept_models": "..concept_models"
        }
        
        return mappings
    
    def analyze(self, context: FixContext) -> List[ImportIssue]:
        """分析导入问题"""
        self.logger.info("分析导入问题...")
        
        issues = []
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                file_issues = self._analyze_file_imports(file_path)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.error(f"分析文件 {file_path} 导入失败: {e}")
        
        # 分析循环导入
        circular_issues = self._analyze_circular_imports()
        issues.extend(circular_issues)

        
        self.logger.info(f"发现 {len(issues)} 个导入问题")
        return issues
    
    def _analyze_file_imports(self, file_path: Path) -> List[ImportIssue]:
        """分析文件的导入"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
             # 解析AST

            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError:
                # 如果文件有语法错误,使用正则表达式提取导入
                return self._analyze_imports_with_regex(content, file_path)

            
             # 分析导入语句

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_issues = self._check_import_validity(
                            file_path, node.lineno, f"import {alias.name}", alias.name)
                        issues.extend(import_issues)

                
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ""

                    level = node.level  # 相对导入级别
                    
                    import_statement = f"from {'.' * level}{module_name} import "
                    import_statement += ", ".join(alias.name for alias in node.names)
                    import_issues = self._check_import_from_validity(
                        file_path, node.lineno, import_statement, module_name, level

                    )
                    issues.extend(import_issues)

        except Exception as e:
            self.logger.error(f"无法分析文件 {file_path} {e}")
        
        return issues
    
    def _analyze_imports_with_regex(self, content: str, file_path: Path) -> List[ImportIssue]:
        """使用正则表达式分析导入"""

        issues = []
        
        # 匹配导入语句
        import_pattern = r'^(?:from\s+(\.+[\w.]*)|import\s+([\w.]+))'

        
        for i, line in enumerate(content.split('\n'), 1):
            match = re.match(import_pattern, line.strip())
            if match:
                from_module = match.group(1)

                import_module = match.group(2)
                
                if from_module:
                    # from导入

                    import_issues = self._check_import_from_validity(
                        file_path, i, line.strip(), from_module, from_module.count('.')

                    )
                else:
                    # import导入
                    import_issues = self._check_import_validity(
                        file_path, i, line.strip(), import_module
                    )
                
                issues.extend(import_issues)
        
        return issues
    
    def _check_import_validity(self, file_path: Path, line_number: int, import_statement: str, module_name: str) -> List[ImportIssue]:
        """检查导入的有效性"""
        issues = []
        
        current_module = self._calculate_module_name(file_path)
        
        # 检查模块是否存在
        if not self._module_exists(module_name):
            # 尝试查找可能的正确路径
            suggested_fix = self._suggest_import_fix(module_name, current_module)


            
            issues.append(ImportIssue(
                file_path=file_path,
                line_number=line_number,
                import_statement=import_statement,
                issue_type="missing_module",
                target_module=module_name,
                current_module=current_module,
                suggested_fix=suggested_fix,
                severity="error"
            ))
        
         # 检查是否应该使用相对导入

        if self._should_use_relative_import(module_name, current_module):
            suggested_fix = self._convert_to_relative_import(module_name, current_module)

            
            issues.append(ImportIssue(
                file_path=file_path,
                line_number=line_number,
                import_statement=import_statement,
                issue_type="absolute_import",
                target_module=module_name,
                current_module=current_module,
                suggested_fix=suggested_fix,
                severity="warning"
            ))
        
        return issues
    
    def _check_import_from_validity(self, file_path: Path, line_number: int, import_statement: str, module_name: str, level: int) -> List[ImportIssue]:
        """检查from导入的有效性"""
        issues = []
        
        current_module = self._calculate_module_name(file_path)
        
        # 解析完整的模块名(考虑相对导入)
        if level > 0:
            # 相对导入
            full_module_name = self._resolve_relative_import(current_module, module_name, level)
        else:
            # 绝对导入

            full_module_name = module_name
        
         # 检查模块是否存在

        if full_module_name and not self._module_exists(full_module_name):
            # 尝试查找可能的正确路径
            suggested_fix = self._suggest_import_fix(full_module_name, current_module)
            
            issues.append(ImportIssue(
                file_path=file_path,
                line_number=line_number,
                import_statement=import_statement,
                issue_type="missing_module",
                target_module=module_name,
                current_module=current_module,
                suggested_fix=suggested_fix,
                severity="error"

            ))
        
        # 检查是否应该使用绝对导入
        if level > 0 and self._should_use_absolute_import(module_name, current_module):
            suggested_fix = self._convert_to_absolute_import(module_name, current_module)
            
            issues.append(ImportIssue(
                file_path=file_path,
                line_number=line_number,
                import_statement=import_statement,
                issue_type="relative_import",
                target_module=module_name,
                current_module=current_module,
                suggested_fix=suggested_fix,
                severity="warning"
            ))
        
        return issues
    
    def _module_exists(self, module_name: str) -> bool:
        """检查模块是否存在"""
        return module_name in self.module_map
    
    def _resolve_relative_import(self, current_module: str, target_module: str, level: int) -> str:
        """解析相对导入"""
        if not current_module:
            return target_module
        
        # 分解当前模块
        current_parts = current_module.split('.')

        
        # 根据级别向上移动
        if level > len(current_parts):
            return ""  # 无效级别

        
        base_parts = current_parts[:-level]
        
        # 添加目标模块
        if target_module:
            target_parts = target_module.split('.')
            full_parts = base_parts + target_parts
        else:
            full_parts = base_parts

        
        return '.'.join(full_parts)
    
    def _should_use_relative_import(self, target_module: str, current_module: str) -> bool:
        """检查是否应该使用相对导入"""
        # 简化的逻辑：如果目标模块是当前模块的子模块或兄弟模块,建议使用相对导入
        
        if not current_module or not target_module:
            return False
        
        current_parts = current_module.split('.')
        target_parts = target_module.split('.')


        
        # 检查是否是子模块
        if len(target_parts) > len(current_parts):
            if target_parts[:len(current_parts)] == current_parts:
                return True
        
        # 检查是否是兄弟模块
        if len(current_parts) > 1 and len(target_parts) >= len(current_parts) - 1:
            if target_parts[:len(current_parts)-1] == current_parts[:-1]:
                return True
        
        return False
    
    def _should_use_absolute_import(self, target_module: str, current_module: str) -> bool:
        """检查是否应该使用绝对导入"""
        # 与相对导入相反的情况
        return not self._should_use_relative_import(target_module, current_module)
    
    def _convert_to_relative_import(self, target_module: str, current_module: str) -> str:
        """转换为相对导入"""
        current_parts = current_module.split('.')
        target_parts = target_module.split('.')
        
        # 找到共同的前缀
        common_length = 0

        for i in range(min(len(current_parts), len(target_parts))):
            if current_parts[i] == target_parts[i]:
                common_length += 1
            else:
                break

        
        # 计算相对级别
        level = len(current_parts) - common_length
        
        # 剩余的目标部分
        remaining_parts = target_parts[common_length:]
        
        # 构建相对导入
        relative_import = '.' * level
        if remaining_parts:
            relative_import += '.'.join(remaining_parts)
        
        return f"from {relative_import} import"
    
    def _convert_to_absolute_import(self, target_module: str, current_module: str) -> str:
        """转换为绝对导入"""

        # 已经是绝对导入,返回原样
        return f"from {target_module} import"
    
    def _suggest_import_fix(self, missing_module: str, current_module: str) -> str:
        """建议导入修复"""
        # 在模块映射中查找相似的模块

        similar_modules = self._find_similar_modules(missing_module)
        
        if similar_modules:
            # 返回最相似的模块
            best_match = similar_modules[0]
            
             # 检查是否应该使用相对导入

            if self._should_use_relative_import(best_match, current_module):
                return self._convert_to_relative_import(best_match, current_module)
            else:
                return f"from {best_match} import"
        
        # 尝试使用导入映射
        for wrong_import, correct_import in self.import_mappings.items():
            if wrong_import in missing_module:
                corrected = missing_module.replace(wrong_import, correct_import)
                return f"from {corrected} import"
        
        return f"# TODO, Fix import - module '{missing_module}' not found"
    
    def _find_similar_modules(self, target_module: str) -> List[str]:
        """查找相似的模块"""
        similar_modules = []

        
        for module_name in self.module_map.keys():
            # 简单的相似度计算
            if target_module in module_name or module_name in target_module:
                similar_modules.append(module_name)
        
        # 按相似度排序
        similar_modules.sort(key=lambda x: len(x))

        
        return similar_modules[:3]  # 返回前3个最相似的
    
    def _analyze_circular_imports(self) -> List[ImportIssue]:
        """分析循环导入"""

        issues = []

        
        # 构建依赖图
        dependency_graph = self._build_dependency_graph()
        
        # 检测循环
        cycles = self._detect_cycles(dependency_graph)
        
        for cycle in cycles:
            # 为循环中的每个模块创建问题
            for i, module in enumerate(cycle):
                next_module = cycle[(i + 1) % len(cycle)]
                
                if module in self.module_map:
                    module_info = self.module_map[module]
                    
                    issues.append(ImportIssue(
                        file_path=module_info.path,
                        line_number=0,  # 循环导入不具体到行
                        import_statement=f"import {next_module}",
                        issue_type="circular_import",
                        target_module=next_module,
                        current_module=module,
                        suggested_fix=f"# 循环导入, {' -> '.join(cycle)} -> {cycle[0]}",
                        severity="warning"
                    ))
        
        return issues
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}
        
        for module_name, module_info in self.module_map.items():
            try:
                imports = self._extract_imports_from_file(module_info.path)
                graph[module_name] = imports

            except Exception as e:
                self.logger.error(f"提取导入失败 {module_info.path} {e}")
                graph[module_name] = []
        
        return graph
    
    def _extract_imports_from_file(self, file_path: Path) -> List[str]:
        """从文件提取导入"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])  # 只取顶级模块名
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])  # 只取顶级模块名
        
        except Exception as e:
            self.logger.error(f"解析文件失败 {file_path} {e}")
        
        return imports
    
    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """检测循环"""
        cycles = []
        visited = set()

        rec_stack = set()
        path = []
        
        def dfs(node):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)

                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)

            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in graph:  # 只考虑在项目内的模块,:
                    dfs(neighbor)
            
            rec_stack.remove(node)
            path.pop()
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def fix(self, context: FixContext) -> FixResult:
        """修复导入问题"""
        self.logger.info("修复导入问题...")
        
        start_time = time.time()
        issues_found = 0
        issues_fixed = 0
        error_message = None
        backup_path = None
        
        try:
            # 创建备份
            if context.backup_enabled:
                # 使用现有的_create_backup方法
                if context.target_path and context.target_path.exists():
                    backup_path = self._create_backup(context.target_path)
                else:
                    # 如果没有特定目标，为项目根目录创建备份
                    backup_path = self._create_backup(self.project_root)
            
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if not issues:
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    target_path=context.target_path,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
            # 修复问题
            fixed_count = 0
            for issue in issues:
                if self._fix_import_issue(issue, context):
                    fixed_count += 1
            
            issues_fixed = fixed_count
            
            # 确定最终状态
            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS
            elif issues_fixed > 0:
                status = FixStatus.PARTIAL_SUCCESS
            else:
                status = FixStatus.FAILED
            
            # 验证修复 (简化验证)
            if issues_fixed > 0:
                # 简单验证：重新分析看是否还有问题
                remaining_issues = self.analyze(context)
                if len(remaining_issues) > 0:
                    self.logger.warning(f"修复验证发现仍有 {len(remaining_issues)} 个问题未修复")
                    if status == FixStatus.SUCCESS:
                        status = FixStatus.PARTIAL_SUCCESS
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"修复导入问题失败: {e}")
            status = FixStatus.FAILED
            traceback_str = traceback.format_exc()
            
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                target_path=context.target_path,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message=error_message,
                traceback=traceback_str,
                duration_seconds=time.time() - start_time,
                backup_path=backup_path
            )
        
        return FixResult(
            fix_type=self.fix_type,
            status=status,
            target_path=context.target_path,
            issues_found=issues_found,
            issues_fixed=issues_fixed,
            error_message=error_message,
            duration_seconds=time.time() - start_time,
            backup_path=backup_path
        )
    
    def _fix_import_issue(self, issue: ImportIssue, context: FixContext) -> bool:
        """修复单个导入问题"""
        if not issue.suggested_fix:
            return False
        
        try:
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            
            original_content = content
            lines = content.split('\n')
            
            if issue.line_number <= len(lines):
                # 应用建议的修复
                lines[issue.line_number - 1] = issue.suggested_fix
                self.logger.debug(f"修复导入, {issue.import_statement} -> {issue.suggested_fix}")
            
            # 重新组合内容
            new_content = '\n'.join(lines)
            
            # 如果内容有变化,写回文件
            if new_content != original_content:
                with open(issue.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.logger.info(f"已修复文件导入, {issue.file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"修复文件导入失败 {issue.file_path} {e}")
            return False
