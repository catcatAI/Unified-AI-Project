"""
输入输出分析器 - 分析项目中的输入输出依赖关系
"""

import ast
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

from ..core.fix_result import FixContext


@dataclass
class IOIssue:
    """输入输出问题"""

    file_path: Path
    line_number: int
    io_type: str  # input, output, missing_input, unreachable_output
    target_path: str
    description: str
    severity: str = "warning"
    suggested_fix: str = ""


@dataclass
class IOPathInfo:
    """输入输出路径信息"""
    path: str
    path_type: str  # file, directory, url, database
    is_variable: bool
    variable_name: Optional[str] = None
    line_number: int = 0
    context: str = ""


class IOAnalyzer:
    """输入输出分析器"""
    
    def __init__(self):
        self.io_paths = defaultdict(list)
        self.dependency_graph = defaultdict(set)
        self.missing_inputs = set()
        self.unreachable_outputs = set()
        self.variable_assignments = defaultdict(dict)
        self.logger = logging.getLogger(__name__)
    
    def analyze_project_io(self, context: FixContext) -> Dict[str, Any]:
        """分析项目的输入输出依赖"""
        result = {
            "input_paths": [],
            "output_paths": [],
            "missing_inputs": [],
            "unreachable_outputs": [],
            "variable_dependencies": {},
            "file_access_patterns": {},
            "database_connections": [],
            "api_endpoints": [],
            "recommendations": []
        }
        
        # 分析Python文件中的IO操作
        python_files = list(context.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                file_io = self._analyze_file_io(py_file)
                
                # 合并结果
                result["input_paths"].extend(file_io["input_paths"])
                result["output_paths"].extend(file_io["output_paths"])
                result["database_connections"].extend(file_io["database_connections"])
                result["api_endpoints"].extend(file_io["api_endpoints"])
        
        # 分析配置文件中的IO路径
        config_io = self._analyze_config_files(context)
        result["input_paths"].extend(config_io["input_paths"])
        result["output_paths"].extend(config_io["output_paths"])
        
        # 验证路径的存在性和可访问性
        self._validate_io_paths(result)
        
        # 分析变量依赖关系
        result["variable_dependencies"] = self._analyze_variable_dependencies()
        
        # 生成建议
        result["recommendations"] = self._generate_io_recommendations(result)
        
        return result
    
    def _analyze_file_io(self, file_path: Path) -> Dict[str, Any]:
        """分析单个文件的IO操作"""
        file_io = {
            "input_paths": [],
            "output_paths": [],
            "database_connections": [],
            "api_endpoints": [],
            "variable_assignments": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # 分析文件操作
            self._analyze_file_operations(tree, file_path, file_io)
            
            # 分析数据库操作
            self._analyze_database_operations(tree, file_path, file_io)
            
            # 分析API调用
            self._analyze_api_operations(tree, file_path, file_io)
            
            # 分析网络操作
            self._analyze_network_operations(tree, file_path, file_io)
            
            # 分析环境变量相关的IO
            self._analyze_env_var_io(tree, file_path, file_io)
            
        except Exception as e:
            print(f"分析文件IO失败 {file_path}: {e}")
        
        return file_io
    
    def _analyze_file_operations(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析文件操作"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name:
                    # 文件读取操作
                    if func_name in ['open', 'file']:
                        self._analyze_open_call(node, file_path, file_io)
                    
                    # JSON文件操作
                    elif func_name in ['json.load', 'json.loads', 'json.dump', 'json.dumps']:
                        self._analyze_json_operation(node, file_path, file_io)
                    
                    # CSV文件操作
                    elif func_name in ['csv.reader', 'csv.writer', 'csv.DictReader', 'csv.DictWriter']:
                        self._analyze_csv_operation(node, file_path, file_io)
                    
                    # Pickle文件操作
                    elif func_name in ['pickle.load', 'pickle.loads', 'pickle.dump', 'pickle.dumps']:
                        self._analyze_pickle_operation(node, file_path, file_io)
                    
                    # 文件系统操作
                    elif func_name in ['os.path.exists', 'os.path.isfile', 'os.path.isdir', 'os.makedirs']:
                        self._analyze_filesystem_operation(node, file_path, file_io)
                    
                    # Path操作
                    elif func_name.startswith('Path.') or func_name.startswith('pathlib.'):
                        self._analyze_path_operation(node, file_path, file_io)
    
    def _analyze_database_operations(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析数据库操作"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name:
                    # SQLAlchemy操作
                    if func_name.startswith('sqlalchemy.') or 'create_engine' in func_name:
                        self._analyze_sqlalchemy_operation(node, file_path, file_io)
                    
                    # SQLite操作
                    elif 'sqlite3' in func_name or 'sqlite' in func_name:
                        self._analyze_sqlite_operation(node, file_path, file_io)
                    
                    # MongoDB操作
                    elif 'mongo' in func_name.lower():
                        self._analyze_mongodb_operation(node, file_path, file_io)
                    
                     # Redis操作
                    elif 'redis' in func_name.lower():
                        self._analyze_redis_operation(node, file_path, file_io)

    
    def _analyze_api_operations(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析API操作"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name:
                    # requests库操作
                    if func_name.startswith('requests.'):
                        self._analyze_requests_operation(node, file_path, file_io)
                    
                    # urllib操作
                    elif func_name in ['urllib.request.urlopen', 'urllib.parse.urljoin']:
                        self._analyze_urllib_operation(node, file_path, file_io)
    
    def _analyze_network_operations(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析网络操作"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name:
                    # socket操作
                    if func_name.startswith('socket.'):
                        self._analyze_socket_operation(node, file_path, file_io)
                    
                    # ftplib操作
                    elif func_name.startswith('ftplib.'):
                        self._analyze_ftp_operation(node, file_path, file_io)
    
    def _analyze_env_var_io(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析环境变量相关的IO"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name:
                    # 环境变量操作
                    if func_name in ['os.getenv', 'os.environ.get']:
                        self._analyze_env_var_operation(node, file_path, file_io)
    
    def _analyze_config_files(self, context: FixContext) -> Dict[str, Any]:
        """分析配置文件"""
        config_io = {
            "input_paths": [],
            "output_paths": []
        }
        
        # 常见配置文件
        config_files = [
            "config.json", "settings.json", "appsettings.json",
            "config.yaml", "config.yml", "settings.yaml", "settings.yml",
            ".env", ".env.local", ".env.production",
            "docker-compose.yml", "docker-compose.yaml"
        ]
        
        for config_file in config_files:
            config_path = context.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 提取路径信息
                    paths = self._extract_paths_from_config(content, config_path)
                    config_io["input_paths"].extend(paths)
                    
                except Exception as e:
                    print(f"分析配置文件失败 {config_path}: {e}")
        
        return config_io
    
    def _extract_paths_from_config(self, content: str, config_path: Path) -> List[IOPathInfo]:
        """从配置文件中提取路径"""
        paths = []
        
        # 根据文件类型解析
        if config_path.suffix in ['.json']:
            try:
                data = json.loads(content)
                paths.extend(self._extract_paths_from_json(data, config_path))
            except json.JSONDecodeError:
                pass
        elif config_path.suffix in ['.yaml', '.yml']:
            # 简化处理YAML文件
            paths.extend(self._extract_paths_from_yaml(content, config_path))
        elif config_path.name.startswith('.env'):
            paths.extend(self._extract_paths_from_env(content, config_path))
        
        return paths
    
    def _extract_paths_from_json(self, data: Any, config_path: Path) -> List[IOPathInfo]:
        """从JSON数据中提取路径"""
        paths = []
        
        def traverse(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if self._is_path_like(key, value):
                        paths.append(IOPathInfo(
                            path=str(value),
                            path_type=self._determine_path_type(str(value)),
                            is_variable=False,
                            line_number=0,
                            context=f"JSON配置中的路径: {new_path}"
                        ))
                    traverse(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    traverse(item, new_path)
        
        traverse(data)
        return paths
    
    def _extract_paths_from_yaml(self, content: str, config_path: Path) -> List[IOPathInfo]:
        """从YAML内容中提取路径"""
        paths = []
        # 简化处理，实际应该使用yaml库
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                value = value.strip().strip('"\'')
                if self._is_path_like(key.strip(), value):
                    paths.append(IOPathInfo(
                        path=value,
                        path_type=self._determine_path_type(value),
                        is_variable=False,
                        line_number=i+1,
                        context=f"YAML配置中的路径: {key.strip()}"
                    ))
        return paths
    
    def _extract_paths_from_env(self, content: str, config_path: Path) -> List[IOPathInfo]:
        """从环境变量文件中提取路径"""
        paths = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"\'')
                if self._is_path_like(key, value):
                    paths.append(IOPathInfo(
                        path=value,
                        path_type=self._determine_path_type(value),
                        is_variable=False,
                        line_number=i+1,
                        context=f"环境变量中的路径: {key}"
                    ))
        return paths
    
    def _is_path_like(self, key: str, value: str) -> bool:
        """判断键值对是否像路径"""
        path_indicators = [
            'path' in key.lower(),
            'dir' in key.lower(),
            'file' in key.lower(),
            'folder' in key.lower(),
            'directory' in key.lower(),
            '/' in value,
            '\\' in value,
            value.endswith(('.txt', '.json', '.yaml', '.yml', '.csv', '.log', '.db', '.sqlite')),
            value.startswith(('http://', 'https://', 'ftp://', 'sftp://')),
            'file://' in value,
            '.com' in value or '.org' in value or '.net' in value
        ]
        
        return any(path_indicators)
    
    def _determine_path_type(self, path: str) -> str:
        """确定路径类型"""
        if path.startswith(('http://', 'https://')):
            return "url"
        elif path.startswith(('ftp://', 'sftp://')):
            return "ftp"
        elif path.endswith(('.db', '.sqlite', '.sqlite3')):
            return "database"
        elif path.endswith('.json'):
            return "json"
        elif path.endswith('.csv'):
            return "csv"
        elif '/' in path or '\\' in path:
            if path.endswith('/') or path.endswith('\\'):
                return "directory"
            else:
                return "file"
        else:
            return "unknown"
    
    def fix_io_issues(self, io_deps: Dict[str, Any], context: FixContext):
        """修复IO依赖问题"""
        # 修复缺失的输入文件
        for missing_input in io_deps.get("missing_inputs", []):
            self._fix_missing_input(missing_input, context)
        
        # 修复无法访问的输出路径
        for unreachable_output in io_deps.get("unreachable_outputs", []):
            self._fix_unreachable_output(unreachable_output, context)
    
    def _fix_missing_input(self, missing_input: Dict[str, Any], context: FixContext):
        """修复缺失的输入"""
        input_path = missing_input["path"]
        
        self.logger.info(f"修复缺失的输入路径: {input_path}")
        
        # 创建缺失的文件或目录
        full_path = Path(input_path)
        if not full_path.is_absolute():
            full_path = Path.cwd() / input_path
        
        if not context.dry_run:
            if input_path.endswith('/') or 'directory' in missing_input.get("type", ""):
                full_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建缺失的目录: {full_path}")
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
                self.logger.info(f"创建缺失的文件: {full_path}")
        else:
            self.logger.info(f"干运行 - 建议创建: {full_path}")
    
    def _fix_unreachable_output(self, unreachable_output: Dict[str, Any], context: FixContext):
        """修复无法访问的输出"""
        output_path = unreachable_output["path"]
        
        self.logger.info(f"修复无法访问的输出路径: {output_path}")
        
        full_path = Path(output_path)
        if not full_path.is_absolute():
            full_path = Path.cwd() / output_path
        
        parent_dir = full_path.parent
        if not context.dry_run:
            parent_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建输出目录: {parent_dir}")
        else:
            self.logger.info(f"干运行 - 建议创建目录: {parent_dir}")
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """检查是否应该分析文件"""
        excluded_patterns = ["__pycache__", ".git", "node_modules", "venv", ".venv"]
        return not any(pattern in str(file_path) for pattern in excluded_patterns)
    
    def _get_function_name(self, node: ast.AST) -> Optional[str]:
        """获取函数名"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_function_name(node.func)
        return None
    
    def _analyze_open_call(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析open调用"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type=self._determine_path_type(path),
                    is_variable=False,
                    line_number=node.lineno,
                    context="文件打开操作"
                ))
            elif isinstance(path_arg, ast.Name):
                # 变量路径
                file_io["input_paths"].append(IOPathInfo(
                    path=path_arg.id,
                    path_type="variable",
                    is_variable=True,
                    variable_name=path_arg.id,
                    line_number=node.lineno,
                    context="文件打开操作(变量路径)"
                ))
    
    def _analyze_json_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析JSON操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type="json",
                    is_variable=False,
                    line_number=node.lineno,
                    context="JSON操作"
                ))
    
    def _analyze_csv_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析CSV操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type="csv",
                    is_variable=False,
                    line_number=node.lineno,
                    context="CSV操作"
                ))
    
    def _analyze_pickle_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析Pickle操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type="file",
                    is_variable=False,
                    line_number=node.lineno,
                    context="Pickle操作"
                ))
    
    def _analyze_filesystem_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析文件系统操作"""
        func_name = self._get_function_name(node.func)
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type="file",
                    is_variable=False,
                    line_number=node.lineno,
                    context=f"文件系统操作: {func_name}"
                ))
    
    def _analyze_path_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析Path操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type=self._determine_path_type(path),
                    is_variable=False,
                    line_number=node.lineno,
                    context="Path操作"
                ))
    
    def _analyze_sqlalchemy_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析SQLAlchemy操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["database_connections"].append(IOPathInfo(
                    path=path,
                    path_type="database",
                    is_variable=False,
                    line_number=node.lineno,
                    context="SQLAlchemy数据库连接"
                ))
    
    def _analyze_sqlite_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析SQLite操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["database_connections"].append(IOPathInfo(
                    path=path,
                    path_type="database",
                    is_variable=False,
                    line_number=node.lineno,
                    context="SQLite数据库连接"
                ))
    
    def _analyze_mongodb_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析MongoDB操作"""
        file_io["database_connections"].append(IOPathInfo(
            path="mongodb://",
            path_type="database",
            is_variable=False,
            line_number=node.lineno,
            context="MongoDB数据库连接"
        ))
    
    def _analyze_redis_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析Redis操作"""
        file_io["database_connections"].append(IOPathInfo(
            path="redis://",
            path_type="database",
            is_variable=False,
            line_number=node.lineno,
            context="Redis数据库连接"
        ))
    
    def _analyze_requests_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析requests操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                if path.startswith(('http://', 'https://')):
                    file_io["api_endpoints"].append(IOPathInfo(
                        path=path,
                        path_type="url",
                        is_variable=False,
                        line_number=node.lineno,
                        context="HTTP API调用"
                    ))
    
    def _analyze_urllib_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析urllib操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                if path.startswith(('http://', 'https://')):
                    file_io["api_endpoints"].append(IOPathInfo(
                        path=path,
                        path_type="url",
                        is_variable=False,
                        line_number=node.lineno,
                        context="URL操作"
                    ))
    
    def _analyze_socket_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析socket操作"""
        file_io["api_endpoints"].append(IOPathInfo(
            path="socket://",
            path_type="network",
            is_variable=False,
            line_number=node.lineno,
            context="Socket网络连接"
        ))
    
    def _analyze_ftp_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析FTP操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                if path.startswith(('ftp://', 'sftp://')):
                    file_io["api_endpoints"].append(IOPathInfo(
                        path=path,
                        path_type="ftp",
                        is_variable=False,
                        line_number=node.lineno,
                        context="FTP文件传输"
                    ))
    
    def _analyze_env_var_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析环境变量操作"""
        if len(node.args) > 0:
            path_arg = node.args[0]
            if isinstance(path_arg, ast.Constant):
                path = path_arg.value
                file_io["input_paths"].append(IOPathInfo(
                    path=path,
                    path_type="environment",
                    is_variable=False,
                    line_number=node.lineno,
                    context="环境变量读取"
                ))
    
    def _validate_io_paths(self, result: Dict[str, Any]):
        """验证IO路径的存在性和可访问性"""
        # 验证输入路径
        for path_info in result["input_paths"]:
            if path_info.path_type in ["file", "directory", "json", "csv"]:
                path = Path(path_info.path)
                if not path.exists():
                    result["missing_inputs"].append({
                        "path": path_info.path,
                        "type": path_info.path_type,
                        "context": path_info.context
                    })
        
        # 验证输出路径的父目录
        for path_info in result["output_paths"]:
            if path_info.path_type in ["file", "directory", "json", "csv"]:
                path = Path(path_info.path)
                parent_dir = path.parent
                if not parent_dir.exists():
                    result["unreachable_outputs"].append({
                        "path": path_info.path,
                        "type": path_info.path_type,
                        "context": path_info.context
                    })
    
    def _analyze_variable_dependencies(self) -> Dict[str, Any]:
        """分析变量依赖关系"""
        # 简化实现
        return {}
    
    def _generate_io_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """生成IO建议"""
        recommendations = []
        
        if result["missing_inputs"]:
            recommendations.append(f"发现 {len(result['missing_inputs'])} 个缺失的输入文件/目录")
        
        if result["unreachable_outputs"]:
            recommendations.append(f"发现 {len(result['unreachable_outputs'])} 个无法访问的输出路径")
        
        if result["database_connections"]:
            recommendations.append(f"发现 {len(result['database_connections'])} 个数据库连接")
        
        if result["api_endpoints"]:
            recommendations.append(f"发现 {len(result['api_endpoints'])} 个API端点")
        
        return recommendations