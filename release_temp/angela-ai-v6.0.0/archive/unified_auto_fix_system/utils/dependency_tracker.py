"""
依赖跟踪器 - 分析项目中的依赖关系
"""

import ast
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from ..core.fix_result import FixContext


@dataclass
class DependencyIssue:
    """依赖问题"""

    dependency_name: str
    issue_type: str  # missing, version_conflict, circular, unused
    current_version: Optional[str] = None
    required_version: Optional[str] = None
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    severity: str = "error"
    description: str = ""


@dataclass
class DependencyGraph:
    """依赖图"""
    nodes: Set[str]
    edges: Dict[str, Set[str]]
    circular_dependencies: List[List[str]]
    unused_dependencies: Set[str]
    missing_dependencies: Set[str]


class DependencyTracker:
    """依赖关系跟踪器"""
    
    def __init__(self):
        self.dependency_graph = DependencyGraph(
            nodes=set(),
            edges=defaultdict(set),
            circular_dependencies=[],
            unused_dependencies=set(),
            missing_dependencies=set()
        )
        self.import_usage = defaultdict(set)
        self.requirements_cache = {}
        self.package_cache = {}

    
    def analyze_project_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析项目依赖关系"""
        result = {
            "python_dependencies": self._analyze_python_dependencies(context),
            "javascript_dependencies": self._analyze_javascript_dependencies(context),
            "system_dependencies": self._analyze_system_dependencies(context),
            "internal_dependencies": self._analyze_internal_dependencies(context),
            "circular_dependencies": [],
            "unused_dependencies": [],
            "missing_dependencies": [],
            "version_conflicts": [],
            "recommendations": []
        }
        
        # 分析循环依赖
        result["circular_dependencies"] = self._detect_circular_dependencies()
        
        # 分析未使用依赖
        result["unused_dependencies"] = self._find_unused_dependencies()
        
        # 分析缺失依赖
        result["missing_dependencies"] = self._find_missing_dependencies()
        
        # 分析版本冲突
        result["version_conflicts"] = self._find_version_conflicts()
        
        # 生成建议
        result["recommendations"] = self._generate_dependency_recommendations(result)

        
        return result
    
    def _analyze_python_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析Python依赖"""
        python_deps = {
            "requirements_files": [],
            "installed_packages": {},
            "import_usage": {},
            "version_specifications": {},
            "dependency_issues": []
        }
        
         # 查找requirements文件
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt", 
            "requirements-test.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg"
        ]
        
        for req_file in requirements_files:
            req_path = context.project_root / req_file
            if req_path.exists():
                python_deps["requirements_files"].append(str(req_path))
                
                if req_file.endswith(".txt"):
                    deps = self._parse_requirements_txt(req_path)
                elif req_file == "pyproject.toml":
                    deps = self._parse_pyproject_toml(req_path)
                elif req_file == "setup.py":
                    deps = self._parse_setup_py(req_path)
                elif req_file == "setup.cfg":
                    deps = self._parse_setup_cfg(req_path)
                else:
                    deps = {}
                
                python_deps["version_specifications"].update(deps)
        
        # 获取已安装的包
        python_deps["installed_packages"] = self._get_installed_python_packages()
        
         # 分析导入使用情况
        python_deps["import_usage"] = self._analyze_python_import_usage(context)
        
         # 检测依赖问题
        python_deps["dependency_issues"] = self._detect_python_dependency_issues(python_deps)
        
        return python_deps
    
    def _analyze_javascript_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析JavaScript依赖"""
        js_deps = {
            "package_files": [],
            "installed_packages": {},
            "import_usage": {},
            "version_specifications": {},
            "dependency_issues": []
        }
        
        # 查找package.json文件
        package_files = ["package.json", "package-lock.json"]
        
        for pkg_file in package_files:
            pkg_path = context.project_root / pkg_file
            if pkg_path.exists():
                js_deps["package_files"].append(str(pkg_path))
                
                if pkg_file == "package.json":
                    deps = self._parse_package_json(pkg_path)
                    js_deps["version_specifications"].update(deps)
        
         # 获取已安装的包
        js_deps["installed_packages"] = self._get_installed_javascript_packages()
        
        # 分析导入使用情况
        js_deps["import_usage"] = self._analyze_javascript_import_usage(context)

        
        return js_deps
    
    def _analyze_system_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析系统依赖"""
        system_deps = {
            "docker_files": [],
            "system_packages": {},
            "environment_variables": {},
            "binary_dependencies": [],
            "dependency_issues": []
        }
        
        # 查找Docker文件
        docker_files = ["Dockerfile", "docker-compose.yml"]
        for docker_file in docker_files:
            docker_path = context.project_root / docker_file
            if docker_path.exists():
                system_deps["docker_files"].append(str(docker_path))
        
        # 分析环境变量使用
        system_deps["environment_variables"] = self._analyze_environment_variables(context)
        
        # 检查二进制依赖
        system_deps["binary_dependencies"] = self._check_binary_dependencies()
        
        return system_deps
    
    def _analyze_internal_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析内部依赖"""
        internal_deps = {
            "module_dependencies": {},
            "file_dependencies": {},
            "circular_imports": []
        }
        
        # 分析模块依赖
        internal_deps["module_dependencies"] = self._analyze_module_dependencies(context)
        
        # 分析文件依赖
        internal_deps["file_dependencies"] = self._analyze_file_dependencies_all(context)
        
        # 检测循环导入
        internal_deps["circular_imports"] = self._detect_circular_imports(context)
        
        return internal_deps
    
    def _parse_requirements_txt(self, req_path: Path) -> Dict[str, str]:
        """解析requirements.txt文件"""
        dependencies = {}
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析包名和版本
                        if '==' in line:
                            name, version = line.split('==', 1)
                            dependencies[name.strip()] = version.strip()
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            dependencies[name.strip()] = f">={version.strip()}"
                        elif '<=' in line:
                            name, version = line.split('<=', 1)
                            dependencies[name.strip()] = f"<={version.strip()}"
                        else:
                            dependencies[line.strip()] = ""
        except Exception as e:
            print(f"解析requirements.txt失败 {req_path}: {e}")
        return dependencies
    
    def _parse_pyproject_toml(self, pyproject_path: Path) -> Dict[str, str]:
        """解析pyproject.toml文件"""
        dependencies = {}
        try:
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单解析，实际应该使用toml库
                dep_sections = ['dependencies', 'dev-dependencies']
                for section in dep_sections:
                    pattern = rf'{section}\s*=\s*\[([^\]]+)\]'
                    match = re.search(pattern, content)
                    if match:
                        deps_str = match.group(1)
                        # 解析依赖项
                        deps = [dep.strip().strip('"\'') for dep in deps_str.split(',')]
                        for dep in deps:
                            if dep:
                                dependencies[dep] = ""
        except Exception as e:
            print(f"解析pyproject.toml失败 {pyproject_path}: {e}")
        return dependencies
    
    def _parse_package_json(self, package_path: Path) -> Dict[str, str]:
        """解析package.json文件"""
        dependencies = {}
        try:
            with open(package_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 获取dependencies和devDependencies
                for section in ['dependencies', 'devDependencies']:
                    if section in data:
                        dependencies.update(data[section])
        except Exception as e:
            print(f"解析package.json失败 {package_path}: {e}")
        return dependencies
    
    def _get_installed_python_packages(self) -> Dict[str, str]:
        """获取已安装的Python包"""
        packages = {}
        try:
            result = subprocess.run(['pip', 'list', '--format=json'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for pkg in data:
                    packages[pkg['name']] = pkg['version']
        except Exception as e:
            print(f"获取Python包列表失败: {e}")
        return packages
    
    def _get_installed_javascript_packages(self) -> Dict[str, str]:
        """获取已安装的JavaScript包"""
        packages = {}
        try:
            # 检查npm包
            result = subprocess.run(['npm', 'list', '--json', '--depth=0'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'dependencies' in data:
                    packages.update(data['dependencies'])
        except Exception as e:
            print(f"获取JavaScript包列表失败: {e}")
        return packages
    
    def _analyze_python_import_usage(self, context: FixContext) -> Dict[str, List[str]]:
        """分析Python导入使用情况"""
        import_usage = defaultdict(list)
        
        # 查找所有Python文件
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if not self._should_analyze_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析AST
                tree = ast.parse(content, filename=str(py_file))
                
                # 分析导入语句
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_usage[alias.name].append(str(py_file))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            import_usage[node.module].append(str(py_file))
                            
            except Exception as e:
                print(f"分析Python导入使用情况失败 {py_file}: {e}")
        
        return dict(import_usage)
    
    def _analyze_javascript_import_usage(self, context: FixContext) -> Dict[str, List[str]]:
        """分析JavaScript导入使用情况"""
        import_usage = defaultdict(list)
        
        # 查找所有JavaScript文件
        js_files = list(context.project_root.rglob("*.js"))
        
        for js_file in js_files:
            if not self._should_analyze_file(js_file):
                continue
                
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单的导入分析
                import_patterns = [
                    r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                    r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                    r'from\s+[\'"]([^\'"]+)[\'"]'
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        import_usage[match].append(str(js_file))

            except Exception as e:
                print(f"分析JavaScript导入使用情况失败 {js_file}: {e}")
        
        return dict(import_usage)
    
    def _detect_python_dependency_issues(self, python_deps: Dict[str, Any]) -> List[DependencyIssue]:
        """检测Python依赖问题"""
        issues = []
        required_deps = python_deps["version_specifications"]
        installed_deps = python_deps["installed_packages"]
        import_usage = python_deps["import_usage"]
        
        # 检查缺失的依赖
        for dep, version_spec in required_deps.items():
            if dep not in installed_deps:
                issues.append(DependencyIssue(
                    dependency_name=dep,
                    issue_type="missing",
                    required_version=version_spec,
                    severity="error",
                    description=f"缺少依赖包: {dep}"
                ))
            elif version_spec and not self._version_satisfies(installed_deps[dep], version_spec):
                issues.append(DependencyIssue(
                    dependency_name=dep,
                    issue_type="version_conflict",
                    current_version=installed_deps[dep],
                    required_version=version_spec,
                    severity="warning",
                    description=f"版本冲突: 安装版本 {installed_deps[dep]} 不满足要求 {version_spec}"
                ))
        
        # 检查未使用的依赖
        for dep in required_deps:
            if dep not in import_usage and dep not in ['setuptools', 'wheel']:
                issues.append(DependencyIssue(
                    dependency_name=dep,
                    issue_type="unused",
                    severity="info",
                    description=f"可能未使用的依赖: {dep}"
                ))
        
        return issues
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """检测循环依赖"""
        circular = []
        visited = set()
        rec_stack = []
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = rec_stack.index(node)
                cycle = path[cycle_start:] + [node]
                circular.append(cycle)
                return
            
            if node in visited:
                return

            
            visited.add(node)
            rec_stack.append(node)
            
            for neighbor in self.dependency_graph.edges.get(node, set()):
                dfs(neighbor, path + [node])
            
            rec_stack.pop()
        
        for node in self.dependency_graph.nodes:
            if node not in visited:
                dfs(node, [])
        
        return circular
    
    def _find_unused_dependencies(self) -> List[str]:
        """查找未使用的依赖"""
        return list(self.dependency_graph.unused_dependencies)
    
    def _find_missing_dependencies(self) -> List[str]:
        """查找缺失的依赖"""
        return list(self.dependency_graph.missing_dependencies)
    
    def _find_version_conflicts(self) -> List[DependencyIssue]:
        """查找版本冲突"""
        conflicts = []
        # 实现版本冲突检测逻辑
        return conflicts
    
    def _generate_dependency_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成依赖建议"""
        recommendations = []

        
        if analysis_result["circular_dependencies"]:
            recommendations.append("发现循环依赖,建议重构代码结构")
        
        if analysis_result["unused_dependencies"]:
            recommendations.append(f"发现 {len(analysis_result['unused_dependencies'])} 个未使用依赖,建议移除")
        
        if analysis_result["missing_dependencies"]:
            recommendations.append(f"发现 {len(analysis_result['missing_dependencies'])} 个缺失依赖,需要安装")
        
        return recommendations
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """检查是否应该分析文件"""
        excluded_patterns = ["__pycache__", ".git", "node_modules", "venv", ".venv"]
        return not any(pattern in str(file_path) for pattern in excluded_patterns)
    
    def _get_module_name(self, file_path: Path, project_root: Path) -> str:
        """获取模块名称"""
        relative_path = file_path.relative_to(project_root)
        module_parts = list(relative_path.parts[:-1])  # 去掉文件名
        
        if file_path.name != "__init__.py":
            module_name = file_path.stem
            if module_parts:
                return '.'.join(module_parts) + '.' + module_name
            else:
                return module_name
        else:
            if module_parts:
                return '.'.join(module_parts)
            else:
                return ""
    
    def _analyze_file_dependencies(self, file_path: Path, context: FixContext) -> Dict[str, Any]:
        """分析文件依赖关系"""
        dependencies = {
            "imports": [],
            "function_calls": [],
            "class_instantiations": [],
            "external_dependencies": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies["imports"].append(node.module)
                elif isinstance(node, ast.Call):
                    func_name = self._get_call_name(node.func)
                    if func_name:
                        dependencies["function_calls"].append(func_name)
        except Exception as e:
            print(f"分析文件依赖失败 {file_path}: {e}")
        
        return dependencies
    
    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """获取调用名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
    
    def _analyze_file_dependencies_all(self, context: FixContext) -> Dict[str, Any]:
        """分析所有文件的依赖关系"""
        all_dependencies = {}
        
        # 查找所有Python文件
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if not self._should_analyze_file(py_file):
                continue
            all_dependencies[str(py_file)] = self._analyze_file_dependencies(py_file, context)
        
        return all_dependencies
    
    def _analyze_module_dependencies(self, context: FixContext) -> Dict[str, Set[str]]:
        """分析模块依赖关系"""
        module_deps = defaultdict(set)
        
        # 查找所有Python文件
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if not self._should_analyze_file(py_file):
                continue
                
            module_name = self._get_module_name(py_file, context.project_root)
            if not module_name:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_deps[module_name].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_deps[module_name].add(node.module)
                            
            except Exception as e:
                print(f"分析模块依赖失败 {py_file}: {e}")
        
        return dict(module_deps)
    
    def _detect_circular_imports(self, context: FixContext) -> List[List[str]]:
        """检测循环导入"""
        # 简化的循环导入检测
        return []
    
    def _analyze_environment_variables(self, context: FixContext) -> Dict[str, List[str]]:
        """分析环境变量使用"""
        env_usage = defaultdict(list)
        
        # 查找所有Python文件
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if not self._should_analyze_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找os.environ, os.getenv等使用
                env_patterns = [
                    r'os\.environ\[["\']([^"\']+)["\']\]',
                    r'os\.getenv\(["\']([^"\']+)["\']',
                    r'environ\[["\']([^"\']+)["\']\]'
                ]
                
                for pattern in env_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        env_usage[match].append(str(py_file))
                        
            except Exception as e:
                print(f"分析环境变量使用失败 {py_file}: {e}")
        
        return dict(env_usage)
    
    def _check_binary_dependencies(self) -> List[str]:
        """检查二进制依赖"""
        binaries = []
        
        # 常见的二进制依赖
        common_binaries = ['git', 'docker', 'node', 'npm', 'python', 'pip']
        
        for binary in common_binaries:
            try:
                result = subprocess.run(['which', binary], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    binaries.append(binary)
            except Exception:
                pass
        
        return binaries
    
    def _version_satisfies(self, installed_version: str, required_spec: str) -> bool:
        """检查版本是否满足要求"""
        # 简化的版本比较
        if not required_spec:
            return True
            
        try:
            if required_spec.startswith('=='):
                return installed_version == required_spec[2:].strip()
            elif required_spec.startswith('>='):
                # 简化版本比较
                return True  # 实际应该实现版本比较逻辑
            elif required_spec.startswith('<='):
                return True  # 实际应该实现版本比较逻辑
        except Exception:
            pass
            
        return True