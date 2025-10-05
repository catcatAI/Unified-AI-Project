"""
依赖跟踪器 - 分析项目中的依赖关系
"""

import ast
import json
import subprocess
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
        docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]
        for docker_file in docker_files:
            docker_path = context.project_root / docker_file
            if docker_path.exists():
                system_deps["docker_files"].append(str(docker_path))
                docker_deps = self._parse_dockerfile(docker_path)
                system_deps["system_packages"].update(docker_deps)
        
        # 分析环境变量依赖
        system_deps["environment_variables"] = self._analyze_environment_variable_dependencies(context)
        
        # 分析二进制依赖
        system_deps["binary_dependencies"] = self._analyze_binary_dependencies(context)
        
        return system_deps
    
    def _analyze_internal_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析内部依赖关系"""
        internal_deps = {
            "module_dependencies": {},
            "function_call_graph": {},
            "class_inheritance": {},
            "import_graph": {},
            "circular_imports": [],
            "unused_internal_imports": []
        }
        
        # 构建模块依赖图
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                file_deps = self._analyze_file_dependencies(py_file, context)
                module_name = self._get_module_name(py_file, context.project_root)
                internal_deps["module_dependencies"][module_name] = file_deps
        
        # 构建函数调用图
        internal_deps["function_call_graph"] = self._build_function_call_graph(python_files, context)
        
        # 构建类继承关系
        internal_deps["class_inheritance"] = self._build_class_inheritance_graph(python_files, context)
        
        # 检测循环导入
        internal_deps["circular_imports"] = self._detect_circular_imports(internal_deps["module_dependencies"])
        
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
                            dependencies[name.strip()] = f"=={version.strip()}"
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            dependencies[name.strip()] = f">={version.strip()}"
                        else:
                            dependencies[line] = None
        except Exception as e:
            print(f"解析requirements.txt失败 {req_path}: {e}")
        return dependencies
    
    def _parse_pyproject_toml(self, pyproject_path: Path) -> Dict[str, str]:
        """解析pyproject.toml文件"""
        dependencies = {}
        try:
            import toml
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # 提取依赖信息
            if 'project' in data and 'dependencies' in data['project']:
                for dep in data['project']['dependencies']:
                    if isinstance(dep, str):
                        name, version = self._parse_dependency_string(dep)
                        dependencies[name] = version
        except Exception as e:
            print(f"解析pyproject.toml失败 {pyproject_path}: {e}")
        return dependencies
    
    def _parse_setup_py(self, setup_path: Path) -> Dict[str, str]:
        """解析setup.py文件"""
        dependencies = {}
        try:
            # 使用AST分析提取依赖信息
            with open(setup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'setup':
                    for keyword in node.keywords:
                        if keyword.arg in ['install_requires', 'requires']:
                            if isinstance(keyword.value, ast.List):
                                for elt in keyword.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        name, version = self._parse_dependency_string(elt.value)
                                        dependencies[name] = version
        except Exception as e:
            print(f"解析setup.py失败 {setup_path}: {e}")
        return dependencies
    
    def _parse_package_json(self, pkg_path: Path) -> Dict[str, str]:
        """解析package.json文件"""
        dependencies = {}
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取依赖信息
            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                if dep_type in data:
                    dependencies.update(data[dep_type])
        except Exception as e:
            print(f"解析package.json失败 {pkg_path}: {e}")
        return dependencies
    
    def _parse_dependency_string(self, dep_string: str) -> Tuple[str, str]:
        """解析依赖字符串"""
        dep_string = dep_string.strip()
        
        # 处理各种版本规范格式
        for operator in ['>=', '<=', '==', '>', '<', '!=', '~=']:
            if operator in dep_string:
                name, version = dep_string.split(operator, 1)
                return name.strip(), f"{operator}{version.strip()}"
        
        return dep_string, None
    
    def _get_installed_python_packages(self) -> Dict[str, str]:
        """获取已安装的Python包"""
        packages = {}
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                package_list = json.loads(result.stdout)
                for package in package_list:
                    packages[package['name']] = package['version']
        except Exception as e:
            print(f"获取已安装Python包失败: {e}")
        return packages
    
    def _get_installed_javascript_packages(self) -> Dict[str, str]:
        """获取已安装的JavaScript包"""
        packages = {}
        try:
            # 检查node_modules是否存在
            node_modules = Path.cwd() / "node_modules"
            if node_modules.exists():
                # 简单的包检测
                for item in node_modules.iterdir():
                    if item.is_dir():
                        pkg_json = item / "package.json"
                        if pkg_json.exists():
                            try:
                                with open(pkg_json, 'r', encoding='utf-8') as f:
                                    pkg_data = json.load(f)
                                packages[pkg_data.get('name', item.name)] = pkg_data.get('version', 'unknown')
                            except:
                                packages[item.name] = 'unknown'
        except Exception as e:
            print(f"获取已安装JavaScript包失败: {e}")
        return packages
    
    def _analyze_python_import_usage(self, context: FixContext) -> Dict[str, List[str]]:
        """分析Python导入使用情况"""
        import_usage = defaultdict(list)
        
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content, filename=str(py_file))
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                            name = node.id
                            import_usage[name].append(str(py_file))
                except Exception as e:
                    print(f"分析导入使用情况失败 {py_file}: {e}")
        
        return dict(import_usage)
    
    def _analyze_javascript_import_usage(self, context: FixContext) -> Dict[str, List[str]]:
        """分析JavaScript导入使用情况"""
        import_usage = defaultdict(list)
        
        js_files = list(context.project_root.rglob("*.js")) + list(context.project_root.rglob("*.ts"))
        
        for js_file in js_files:
            if self._should_analyze_file(js_file):
                try:
                    with open(js_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 简单的导入分析
                    import_patterns = [
                        r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                        r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                        r'from\s+[\'"]([^\'"]+)[\'"]'
                    ]
                    
                    import re
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
            recommendations.append("发现循环依赖，建议重构代码结构")
        
        if analysis_result["unused_dependencies"]:
            recommendations.append(f"发现 {len(analysis_result['unused_dependencies'])} 个未使用依赖，建议移除")
        
        if analysis_result["missing_dependencies"]:
            recommendations.append(f"发现 {len(analysis_result['missing_dependencies'])} 个缺失依赖，需要安装")
        
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
    
    def _build_function_call_graph(self, python_files: List[Path], context: FixContext) -> Dict[str, List[str]]:
        """构建函数调用图"""
        call_graph = defaultdict(list)
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content, filename=str(py_file))
                    
                    current_function = None
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            current_function = node.name
                        elif isinstance(node, ast.Call) and current_function:
                            func_name = self._get_call_name(node.func)
                            if func_name:
                                call_graph[current_function].append(func_name)
                except Exception as e:
                    print(f"构建函数调用图失败 {py_file}: {e}")
        
        return dict(call_graph)
    
    def _build_class_inheritance_graph(self, python_files: List[Path], context: FixContext) -> Dict[str, List[str]]:
        """构建类继承图"""
        inheritance_graph = defaultdict(list)
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content, filename=str(py_file))
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            for base in node.bases:
                                if isinstance(base, ast.Name):
                                    base_name = base.id
                                    inheritance_graph[class_name].append(base_name)
                except Exception as e:
                    print(f"构建类继承图失败 {py_file}: {e}")
        
        return dict(inheritance_graph)
    
    def _detect_circular_imports(self, module_dependencies: Dict[str, Any]) -> List[List[str]]:
        """检测循环导入"""
        # 构建导入图
        import_graph = defaultdict(set)
        
        for module, deps in module_dependencies.items():
            for imp in deps.get("imports", []):
                import_graph[module].add(imp)
        
        # 使用DFS检测循环
        circular_imports = []
        visited = set()
        rec_stack = []
        
        def dfs(module, path):
            if module in rec_stack:
                cycle_start = rec_stack.index(module)
                cycle = path[cycle_start:] + [module]
                circular_imports.append(cycle)
                return
            
            if module in visited:
                return
            
            visited.add(module)
            rec_stack.append(module)
            
            for imported in import_graph.get(module, set()):
                dfs(imported, path + [module])
            
            rec_stack.pop()
        
        for module in import_graph:
            if module not in visited:
                dfs(module, [])
        
        return circular_imports
    
    def _analyze_environment_variable_dependencies(self, context: FixContext) -> Dict[str, Any]:
        """分析环境变量依赖"""
        env_deps = {
            "required_variables": [],
            "optional_variables": [],
            "missing_variables": [],
            "usage_analysis": {}
        }
        
        # 扫描代码中的环境变量使用
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 简单的环境变量模式匹配
                    env_patterns = [
                        r'os\.environ\[\s*[\'"]([^\'"]+)[\'"]\s*\]',
                        r'os\.environ\.get\(\s*[\'"]([^\'"]+)[\'"]',
                        r'os\.getenv\(\s*[\'"]([^\'"]+)[\'"]',
                        r'environ\[\s*[\'"]([^\'"]+)[\'"]\s*\]'
                    ]
                    
                    import re
                    for pattern in env_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match not in env_deps["required_variables"]:
                                env_deps["required_variables"].append(match)
                            
                            if match not in env_deps["usage_analysis"]:
                                env_deps["usage_analysis"][match] = []
                            env_deps["usage_analysis"][match].append(str(py_file))
                except Exception as e:
                    print(f"分析环境变量依赖失败 {py_file}: {e}")
        
        # 检查缺失的环境变量
        current_env = dict(os.environ)
        for var in env_deps["required_variables"]:
            if var not in current_env:
                env_deps["missing_variables"].append(var)
        
        return env_deps
    
    def _analyze_binary_dependencies(self, context: FixContext) -> List[str]:
        """分析二进制依赖"""
        binaries = []
        
        # 查找对系统命令的调用
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找subprocess调用
                    import re
                    subprocess_patterns = [
                        r'subprocess\.(run|call|check_output|check_call|Popen)\s*\([^)]*[\'"]([^\'"]+)[\'"]',
                        r'os\.system\s*\(\s*[\'"]([^\'"]+)[\'"]'
                    ]
                    
                    for pattern in subprocess_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple):
                                binary = match[-1]  # 取最后一个组
                            else:
                                binary = match
                            
                            if binary and binary not in binaries:
                                binaries.append(binary)
                except Exception as e:
                    print(f"分析二进制依赖失败 {py_file}: {e}")
        
        return binaries
    
    def _parse_dockerfile(self, docker_path: Path) -> Dict[str, str]:
        """解析Dockerfile"""
        system_packages = {}
        try:
            with open(docker_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith('RUN') and 'apt-get' in line:
                    # 提取apt-get安装的包
                    import re
                    matches = re.findall(r'apt-get\s+install\s+(-y\s+)?([^\s&|;]+)', line)
                    for match in matches:
                        packages = match[1].split()
                        for pkg in packages:
                            if pkg and not pkg.startswith('-'):
                                system_packages[pkg] = "latest"
        except Exception as e:
            print(f"解析Dockerfile失败 {docker_path}: {e}")
        
        return system_packages
    
    def _version_satisfies(self, current_version: str, required_version: str) -> bool:
        """检查版本是否满足要求"""
        try:
            from packaging import version
            
            if required_version.startswith('=='):
                return current_version == required_version[2:]
            elif required_version.startswith('>='):
                return version.parse(current_version) >= version.parse(required_version[2:])
            elif required_version.startswith('<='):
                return version.parse(current_version) <= version.parse(required_version[2:])
            elif required_version.startswith('>'):
                return version.parse(current_version) > version.parse(required_version[1:])
            elif required_version.startswith('<'):
                return version.parse(current_version) < version.parse(required_version[1:])
            else:
                return True
        except Exception:
            # 简化版本比较
            return True