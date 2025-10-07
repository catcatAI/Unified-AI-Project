"""
输入输出分析器 - 分析项目中的输入输出依赖关系
"""

import ast
import json
import re
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
                    if func_name in ['requests.get', 'requests.post', 'requests.put', 'requests.delete']:
                        self._analyze_requests_operation(node, file_path, file_io)
                    
                    # httpx操作
                    elif 'httpx' in func_name:
                        self._analyze_httpx_operation(node, file_path, file_io)
                    
                    # urllib操作
                    elif 'urllib' in func_name:
                        self._analyze_urllib_operation(node, file_path, file_io)
                    
                    # FastAPI/Flask操作
                    elif any(api_framework in func_name for api_framework in ['FastAPI', 'Flask', 'app.route']):

                        self._analyze_web_framework_operation(node, file_path, file_io)
    
    def _analyze_network_operations(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析网络操作"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name:
                    # Socket操作
                    if 'socket' in func_name.lower():
                        self._analyze_socket_operation(node, file_path, file_io)
                    
                    # FTP操作
                    elif 'ftp' in func_name.lower():
                        self._analyze_ftp_operation(node, file_path, file_io)
                    
                     # SSH操作

                    elif 'ssh' in func_name.lower():
                        self._analyze_ssh_operation(node, file_path, file_io)
    
    def _analyze_env_var_io(self, tree: ast.AST, file_path: Path, file_io: Dict[str, Any]):
        """分析环境变量相关的IO"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                
                if func_name and 'environ' in func_name:
                    # 分析环境变量访问
                    self._analyze_environ_access(node, file_path, file_io)
    
    def _analyze_open_call(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析open()调用"""
        if node.args:
            file_path_arg = node.args[0]
            file_path_str = self._extract_path_from_node(file_path_arg)
            
            if file_path_str:
                # 检查文件模式

                mode = 'r'  # 默认读取模式
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value


                
                io_path_info = IOPathInfo(
                    path=file_path_str,
                    path_type="file",
                    is_variable=isinstance(file_path_arg, ast.Name),
                    variable_name=file_path_arg.id if isinstance(file_path_arg, ast.Name) else None,
                    line_number=node.lineno,
                    context=f"open('{file_path_str}', '{mode}')"
                )
                
                if 'r' in mode or mode == 'rb':
                    file_io["input_paths"].append(io_path_info)
                elif 'w' in mode or 'a' in mode or mode == 'wb' or mode == 'ab':
                    file_io["output_paths"].append(io_path_info)
    
    def _analyze_json_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析JSON操作"""
        func_name = self._get_function_name(node.func)

        
        if func_name in ['json.load'] and node.args:
#             file_arg = node.args[0]
# 
            file_path_str = self._extract_path_from_node(file_arg)
            
            if file_path_str:
                io_path_info = IOPathInfo(
                    path=file_path_str,
                    path_type="file",
                    is_variable=isinstance(file_arg, ast.Name),
                    variable_name=file_arg.id if isinstance(file_arg, ast.Name) else None,
                    line_number=node.lineno,
                    context=f"json.load('{file_path_str}')"

                )
                #                 file_io["input_paths"].append(io_path_info)

#         
#         elif func_name in ['json.dump'] and len(node.args) >= 2:
#             file_arg = node.args[1]

            file_path_str = self._extract_path_from_node(file_arg)

            
            if file_path_str:
                io_path_info = IOPathInfo(
                    path=file_path_str,
                    path_type="file",
                    is_variable=isinstance(file_arg, ast.Name),
                    variable_name=file_arg.id if isinstance(file_arg, ast.Name) else None,
                    line_number=node.lineno,
                    context=f"json.dump(..., '{file_path_str}')"
                )
                file_io["output_paths"].append(io_path_info)
    
     #     def _analyze_database_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):

#         """分析数据库操作"""
# 
#         func_name = self._get_function_name(node.func)
        
        if 'create_engine' in func_name and node.args:
            # SQLAlchemy数据库连接
            connection_string = self._extract_connection_string(node.args[0])

            if connection_string:

                io_path_info = IOPathInfo(
                    path=connection_string,
                    path_type="database",
                    is_variable=isinstance(node.args[0], ast.Name),
                    variable_name=node.args[0].id if isinstance(node.args[0], ast.Name) else None,

 line_number=node.lineno,

#                     context=f"create_engine('{connection_string}')"
                )
#                 file_io["database_connections"].append(io_path_info)

    
    def _analyze_requests_operation(self, node: ast.Call, file_path: Path, file_io: Dict[str, Any]):
        """分析requests操作"""

        if node.args:
            url_arg = node.args[0]
            url = self._extract_url_from_node(url_arg)
            
            if url:
                io_path_info = IOPathInfo(
                    path=url,
                    path_type="url",
                    is_variable=isinstance(url_arg, ast.Name),
                    variable_name=url_arg.id if isinstance(url_arg, ast.Name) else None,

 line_number=node.lineno,

                    context=f"requests.{self._get_function_name(node.func).split('.')[-1]}('{url}')"
                )
                
                func_name = self._get_function_name(node.func)
                if func_name and 'get' in func_name:


                    file_io["input_paths"].append(io_path_info)
                else:
                    file_io["output_paths"].append(io_path_info)
                
                file_io["api_endpoints"].append(io_path_info)
    
    def _analyze_config_files(self, context: FixContext) -> Dict[str, List[IOPathInfo]]:
        """分析配置文件中的IO路径"""
        config_io = {
            "input_paths": [],
            "output_paths": []
        }
        
        # 常见的配置文件
        config_files = [
            "config.json",
            "settings.json",
            "config.yaml",

 "settings.yaml",

            ".env",
            "config.ini"


        ]
        
        for config_file in config_files:
            config_path = context.project_root / config_file
            if config_path.exists():
                file_io = self._analyze_config_file_io(config_path)
                config_io["input_paths"].extend(file_io["input_paths"])
                config_io["output_paths"].extend(file_io["output_paths"])
        
        return config_io
    
    def _analyze_config_file_io(self, config_path: Path) -> Dict[str, List[IOPathInfo]]:
        """分析配置文件的IO路径"""
        config_io = {
            "input_paths": [],
            "output_paths": []
        }
        
        try:
            if config_path.suffix == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                 # 查找可能的路径配置

                self._extract_paths_from_config(config_data, config_path, config_io)
#             
            elif config_path.suffix in ['.yaml', '.yml']:
#                 import yaml
                with open(config_path, 'r', encoding='utf-8') as f:

                    config_data = yaml.safe_load(f)
                
                self._extract_paths_from_config(config_data, config_path, config_io)
            
            elif config_path.name == '.env':
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()

                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)

                            if 'PATH' in key.upper() or 'FILE' in key.upper() or 'URL' in key.upper():
                                if self._looks_like_path(value):
                                    io_path_info = IOPathInfo(
                                        path=value,
                                        path_type=self._determine_path_type(value),
                                        is_variable=False,
                                        line_number=0,

                                        context=f"{key}={value}"
                                    )
                                    config_io["input_paths"].append(io_path_info)

        
        except Exception as e:
            print(f"分析配置文件IO失败 {config_path}: {e}")
        
        return config_io
    
    def _validate_io_paths(self, result: Dict[str, Any]):
        """验证IO路径的有效性"""
        # 检查缺失的输入
        for input_path in result["input_paths"]:
            if input_path.path_type == "file":
                full_path = Path(input_path.path)

                if not full_path.exists() and not full_path.is_absolute():
                    # 尝试相对路径
                    project_root = Path.cwd()
                    relative_path = project_root / input_path.path


                    if not relative_path.exists():
                        result["missing_inputs"].append({
                        "path": input_path.path,

 "type": input_path.path_type,

                            "line_number": input_path.line_number,
                            "context": input_path.context

                        })
        
        # 检查无法访问的输出
        for output_path in result["output_paths"]:
            if output_path.path_type == "file":
                full_path = Path(output_path.path)
                if not full_path.is_absolute():

                    full_path = Path.cwd() / output_path.path
                
                parent = full_path.parent
                if not parent.exists():

                    result["unreachable_outputs"].append({
                        "path": output_path.path,
                        "type": output_path.path_type,

                        "line_number": output_path.line_number,
                        "context": output_path.context


                    })
    
    def _analyze_variable_dependencies(self) -> Dict[str, Any]:
        """分析变量依赖关系"""
        dependencies = {


 "file_path_variables": {},

            "environment_variables": {},
            "configuration_variables": {},

            "computed_variables": {}

 }

        
         # 分析文件路径变量


        for var_name, paths in self.variable_assignments.items():
            if any('file' in str(path).lower() or 'path' in str(path).lower() for path in paths):

                dependencies["file_path_variables"][var_name] = list(paths)
        
        return dependencies
    
    def _generate_io_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """生成IO建议"""
        recommendations = []
        
        if result["missing_inputs"]:
            recommendations.append(f"发现 {len(result['missing_inputs'])} 个缺失的输入路径，建议检查文件是否存在")
        
        if result["unreachable_outputs"]:
            recommendations.append(f"发现 {len(result['unreachable_outputs'])} 个无法访问的输出路径，建议检查目录权限")
        
        if result["database_connections"]:
            recommendations.append("发现数据库连接，建议检查连接字符串的安全性")
        
        if result["api_endpoints"]:
            recommendations.append("发现API端点调用，建议检查错误处理和重试机制")
        
        return recommendations
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """检查是否应该分析文件"""
        excluded_patterns = ["__pycache__", ".git", "node_modules", "venv", ".venv"]
        return not any(pattern in str(file_path) for pattern in excluded_patterns)

    
    def _get_function_name(self, node: ast.AST) -> Optional[str]:
        """获取函数名称"""

        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        return None
    
    def _extract_path_from_node(self, node: ast.AST) -> Optional[str]:
#         """从AST节点提取路径"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Name):
            # 变量路径，需要跟踪赋值

            if node.id in self.variable_assignments:
                # 返回最新的赋值
#                 assignments = self.variable_assignments[node.id]
#                 if assignments:
                    return list(assignments)[-1]
                    return None

    
    def _extract_connection_string(self, node: ast.AST) -> Optional[str]:
        """提取数据库连接字符串"""

        return self._extract_path_from_node(node)
    
    def _extract_url_from_node(self, node: ast.AST) -> Optional[str]:
        """从节点提取URL"""

        return self._extract_path_from_node(node)
    
    def _extract_paths_from_config(self, config_data: Any, config_path: Path, config_io: Dict[str, List[IOPathInfo]]):
        """从配置数据提取路径"""
        def extract_from_value(value, key_path=""):

            if isinstance(value, dict):

                for key, val in value.items():
                    new_key_path = f"{key_path}.{key}" if key_path else key
                    extract_from_value(val, new_key_path)
            elif isinstance(value, list):
                for i, val in enumerate(value):

                    new_key_path = f"{key_path}[{i}]"
                    extract_from_value(val, new_key_path)
            elif isinstance(value, str) and self._looks_like_path(value):
                io_path_info = IOPathInfo(
                    path=value,
                    path_type=self._determine_path_type(value),
                    is_variable=False,
                    line_number=0,
                    context=f"{config_path.name}:{key_path}"
                )
                
                if 'input' in key_path.lower() or 'read' in key_path.lower():
                    config_io["input_paths"].append(io_path_info)
                else:
                    config_io["output_paths"].append(io_path_info)
        
        extract_from_value(config_data)
    
    def _looks_like_path(self, value: str) -> bool:
        """判断字符串是否像路径"""
        if not value or len(value) < 2:
            return False
        
        # 检查路径特征
        path_indicators = [
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
            if path.endswith('/') or '\\' in path:
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