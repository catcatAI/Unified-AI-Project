#!/usr/bin/env python3
"""
环境检查器核心模块 - 检查和验证开发环境
"""

import os
import sys
import json
import subprocess
import time
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union, Any
from enum import Enum

class EnvironmentComponent(Enum):
    """环境组件枚举"""
    PYTHON = "python"              # Python环境
    VENV = "venv"                  # 虚拟环境
    NODE = "node"                  # Node.js环境
    PNPM = "pnpm"                  # pnpm包管理器
    DEPENDENCIES = "dependencies"  # 依赖包
    DATABASE = "database"          # 数据库
    API_SERVER = "api_server"      # API服务器
    MQTT_BROKER = "mqtt_broker"    # MQTT代理
    FIREBASE = "firebase"          # Firebase
    CONFIG_FILES = "config_files"  # 配置文件
    ALL = "all"                    # 所有组件

class EnvironmentStatus(Enum):
    """环境状态枚举"""
    HEALTHY = "healthy"            # 健康
    WARNING = "warning"            # 警告
    ERROR = "error"               # 错误
    MISSING = "missing"            # 缺失

class EnvironmentCheckResult:
    """环境检查结果类"""
    def __init__(self, component: EnvironmentComponent):
        self.component = component.value
        self.status = EnvironmentStatus.HEALTHY.value
        self.details = ""
        self.version = ""
        self.path = ""
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.errors = []
        self.warnings = []
        self.suggestions = []

class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.frontend_root = project_root / "apps" / "frontend-dashboard"
        self.desktop_root = project_root / "apps" / "desktop-app"
        
        # 检查结果
        self.check_results: Dict[str, EnvironmentCheckResult] = {}
        
        # 环境配置
        self.env_config = {
            "python_min_version": (3, 8),
            "node_min_version": (16, 0),
            "required_env_vars": [
                "FIREBASE_CREDENTIALS_PATH"
            ],
            "required_config_files": [
                "apps/backend/configs/system_config.yaml",
                "apps/backend/configs/hsp_fallback_config.yaml"
            ],
            "required_directories": [
                "apps/backend/src",
                "apps/frontend-dashboard",
                "apps/desktop-app",
                "data",
                "tests"
            ]
        }
    
    def check_python_environment(self) -> EnvironmentCheckResult:
        """检查Python环境"""
        result = EnvironmentCheckResult(EnvironmentComponent.PYTHON)
        
        try:
            # 检查Python版本
            version = sys.version_info
            result.version = f"{version.major}.{version.minor}.{version.micro}"
            result.path = sys.executable
            
            # 检查最低版本要求
            min_version = self.env_config["python_min_version"]
            if version >= min_version:
                result.status = EnvironmentStatus.HEALTHY.value
                result.details = f"Python版本 {result.version} 满足要求"
            else:
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"Python版本 {result.version} 不满足最低要求 {min_version[0]}.{min_version[1]}"
                result.suggestions.append(f"请升级Python到{min_version[0]}.{min_version[1]}或更高版本")
            
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查Python环境时出错: {str(e)}")
            result.details = "无法检查Python环境"
        
        return result
    
    def check_virtual_environment(self) -> EnvironmentCheckResult:
        """检查虚拟环境"""
        result = EnvironmentCheckResult(EnvironmentComponent.VENV)
        
        try:
            # 检查虚拟环境目录
            venv_paths = [
                self.project_root / "venv",
                self.project_root / ".venv",
                self.project_root / "env"
            ]
            
            venv_found = False
            for venv_path in venv_paths:
                if venv_path.exists():
                    venv_found = True
                    result.path = str(venv_path)
                    
                    # 检查虚拟环境是否激活
                    if sys.prefix == str(venv_path):
                        result.status = EnvironmentStatus.HEALTHY.value
                        result.details = f"虚拟环境已激活: {venv_path}"
                    else:
                        result.status = EnvironmentStatus.WARNING.value
                        result.details = f"虚拟环境存在但未激活: {venv_path}"
                        result.suggestions.append("请激活虚拟环境后再运行")
                    break
            
            if not venv_found:
                result.status = EnvironmentStatus.WARNING.value
                result.details = "未找到虚拟环境"
                result.suggestions.append("建议创建虚拟环境以隔离依赖")
            
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查虚拟环境时出错: {str(e)}")
            result.details = "无法检查虚拟环境"
        
        return result
    
    def check_node_environment(self) -> EnvironmentCheckResult:
        """检查Node.js环境"""
        result = EnvironmentCheckResult(EnvironmentComponent.NODE)
        
        try:
            # 检查Node.js是否安装
            result_node = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result_node.returncode == 0:
                result.version = result_node.stdout.strip().replace('v', '')
                result.status = EnvironmentStatus.HEALTHY.value
                result.details = f"Node.js版本 {result.version} 已安装"
                
                # 检查版本是否满足要求
                try:
                    version_parts = [int(x) for x in result.version.split('.')]
                    min_version = self.env_config["node_min_version"]
                    if tuple(version_parts[:2]) < min_version:
                        result.status = EnvironmentStatus.WARNING.value
                        result.details += f"，但建议升级到{min_version[0]}.{min_version[1]}或更高版本"
                        result.suggestions.append(f"建议升级Node.js到{min_version[0]}.{min_version[1]}或更高版本")
                except:
                    pass
            else:
                result.status = EnvironmentStatus.ERROR.value
                result.details = "Node.js未安装或无法访问"
                result.suggestions.append("请安装Node.js")
            
        except subprocess.TimeoutExpired:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append("检查Node.js版本超时")
            result.details = "无法检查Node.js版本"
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查Node.js环境时出错: {str(e)}")
            result.details = "无法检查Node.js环境"
        
        return result
    
    def check_pnpm(self) -> EnvironmentCheckResult:
        """检查pnpm包管理器"""
        result = EnvironmentCheckResult(EnvironmentComponent.PNPM)
        
        try:
            # 检查pnpm是否安装
            result_pnpm = subprocess.run(
                ["pnpm", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result_pnpm.returncode == 0:
                result.version = result_pnpm.stdout.strip()
                result.status = EnvironmentStatus.HEALTHY.value
                result.details = f"pnpm版本 {result.version} 已安装"
            else:
                result.status = EnvironmentStatus.WARNING.value
                result.details = "pnpm未安装或无法访问"
                result.suggestions.append("建议安装pnpm: npm install -g pnpm")
            
        except subprocess.TimeoutExpired:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append("检查pnpm版本超时")
            result.details = "无法检查pnpm版本"
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查pnpm时出错: {str(e)}")
            result.details = "无法检查pnpm"
        
        return result
    
    def check_dependencies(self) -> EnvironmentCheckResult:
        """检查依赖包"""
        result = EnvironmentCheckResult(EnvironmentComponent.DEPENDENCIES)
        
        try:
            # 检查Python依赖
            requirements_files = [
                self.project_root / "requirements.txt",
                self.backend_root / "requirements.txt",
                self.backend_root / "requirements-dev.txt"
            ]
            
            python_deps_ok = True
            for req_file in requirements_files:
                if req_file.exists():
                    # 检查依赖是否安装
                    try:
                        with open(req_file, 'r', encoding='utf-8') as f:
                            requirements = f.read()
                        
                        # 这里可以添加更详细的依赖检查逻辑
                        result.details += f"找到依赖文件: {req_file}\n"
                    except Exception as e:
                        python_deps_ok = False
                        result.errors.append(f"读取依赖文件 {req_file} 失败: {str(e)}")
            
            # 检查Node.js依赖
            package_json_files = [
                self.project_root / "package.json",
                self.frontend_root / "package.json",
                self.desktop_root / "package.json"
            ]
            
            node_deps_ok = True
            for pkg_file in package_json_files:
                if pkg_file.exists():
                    # 检查node_modules是否存在
                    node_modules_dir = pkg_file.parent / "node_modules"
                    if node_modules_dir.exists():
                        result.details += f"找到node_modules: {node_modules_dir}\n"
                    else:
                        node_deps_ok = False
                        result.warnings.append(f"未找到node_modules: {node_modules_dir}")
                        result.suggestions.append(f"请在 {pkg_file.parent} 目录运行 pnpm install")
            
            if python_deps_ok and node_deps_ok:
                result.status = EnvironmentStatus.HEALTHY.value
                result.details = "依赖包检查通过"
            else:
                result.status = EnvironmentStatus.WARNING.value
                if not python_deps_ok:
                    result.details += "Python依赖检查存在问题\n"
                if not node_deps_ok:
                    result.details += "Node.js依赖检查存在问题"
            
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查依赖包时出错: {str(e)}")
            result.details = "无法检查依赖包"
        
        return result
    
    def check_database(self) -> EnvironmentCheckResult:
        """检查数据库连接"""
        result = EnvironmentCheckResult(EnvironmentComponent.DATABASE)
        
        try:
            # 检查Firebase配置
            firebase_creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if not firebase_creds_path:
                result.status = EnvironmentStatus.WARNING.value
                result.details = "FIREBASE_CREDENTIALS_PATH环境变量未设置"
                result.suggestions.append("请设置FIREBASE_CREDENTIALS_PATH环境变量")
                return result
            
            creds_file = Path(firebase_creds_path)
            if not creds_file.exists():
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"Firebase凭据文件不存在: {firebase_creds_path}"
                result.suggestions.append("请确保Firebase凭据文件存在")
                return result
            
            # 尝试连接Firebase
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                if not firebase_admin._apps:
                    cred = credentials.Certificate(firebase_creds_path)
                    firebase_admin.initialize_app(cred)
                
                db = firestore.client()
                # 简单的连接测试
                doc_ref = db.collection('health_check').document('ping')
                doc_ref.set({'timestamp': firestore.SERVER_TIMESTAMP})
                doc = doc_ref.get()
                
                if doc.exists:
                    result.status = EnvironmentStatus.HEALTHY.value
                    result.details = "Firebase数据库连接正常"
                else:
                    result.status = EnvironmentStatus.ERROR.value
                    result.details = "Firebase数据库连接测试失败"
                    
            except ImportError:
                result.status = EnvironmentStatus.WARNING.value
                result.details = "Firebase Admin SDK未安装"
                result.suggestions.append("请安装firebase-admin包")
            except Exception as e:
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"Firebase数据库连接失败: {str(e)}"
                result.errors.append(f"数据库连接错误: {str(e)}")
            
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查数据库时出错: {str(e)}")
            result.details = "无法检查数据库"
        
        return result
    
    def check_api_server(self) -> EnvironmentCheckResult:
        """检查API服务器"""
        result = EnvironmentCheckResult(EnvironmentComponent.API_SERVER)
        
        try:
            # 读取系统配置
            config_path = self.backend_root / "configs" / "system_config.yaml"
            if not config_path.exists():
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"系统配置文件不存在: {config_path}"
                return result
            
            # 读取配置
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            api_host = config['operational_configs']['api_server']['host']
            api_port = config['operational_configs']['api_server']['port']
            api_endpoint = f"http://{api_host}:{api_port}/api/health"
            
            # 测试API连接
            import requests
            response = requests.get(api_endpoint, timeout=5)
            
            if response.status_code == 200:
                result.status = EnvironmentStatus.HEALTHY.value
                result.details = f"API服务器运行正常: {api_endpoint}"
            else:
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"API服务器响应异常: HTTP {response.status_code}"
                result.suggestions.append("请检查API服务器日志")
                
        except FileNotFoundError:
            result.status = EnvironmentStatus.ERROR.value
            result.details = f"系统配置文件不存在: {config_path}"
        except ImportError:
            result.status = EnvironmentStatus.WARNING.value
            result.details = "缺少必要的依赖包（requests, yaml）"
            result.suggestions.append("请安装requests和pyyaml包")
        except requests.RequestException as e:
            result.status = EnvironmentStatus.ERROR.value
            result.details = f"无法连接到API服务器: {str(e)}"
            result.suggestions.append("请确保API服务器正在运行")
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查API服务器时出错: {str(e)}")
            result.details = "无法检查API服务器"
        
        return result
    
    def check_mqtt_broker(self) -> EnvironmentCheckResult:
        """检查MQTT代理"""
        result = EnvironmentCheckResult(EnvironmentComponent.MQTT_BROKER)
        
        try:
            # 读取HSP配置
            hsp_config_path = self.backend_root / "configs" / "hsp_fallback_config.yaml"
            if not hsp_config_path.exists():
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"HSP配置文件不存在: {hsp_config_path}"
                return result
            
            # 读取配置
            import yaml
            with open(hsp_config_path, 'r', encoding='utf-8') as f:
                hsp_config = yaml.safe_load(f)
            
            broker_address = hsp_config['hsp_primary']['mqtt']['broker_address']
            broker_port = hsp_config['hsp_primary']['mqtt']['broker_port']
            
            # 测试MQTT连接
            import paho.mqtt.client as mqtt
            
            mqtt_client = mqtt.Client()
            mqtt_client.connect(broker_address, broker_port, 60)
            mqtt_client.disconnect()
            
            result.status = EnvironmentStatus.HEALTHY.value
            result.details = f"MQTT代理连接正常: {broker_address}:{broker_port}"
            
        except FileNotFoundError:
            result.status = EnvironmentStatus.ERROR.value
            result.details = f"HSP配置文件不存在: {hsp_config_path}"
        except ImportError:
            result.status = EnvironmentStatus.WARNING.value
            result.details = "缺少paho-mqtt包"
            result.suggestions.append("请安装paho-mqtt包")
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.details = f"无法连接到MQTT代理: {str(e)}"
            result.errors.append(f"MQTT连接错误: {str(e)}")
            result.suggestions.append("请确保MQTT代理正在运行")
        
        return result
    
    def check_config_files(self) -> EnvironmentCheckResult:
        """检查配置文件"""
        result = EnvironmentCheckResult(EnvironmentComponent.CONFIG_FILES)
        
        try:
            missing_files = []
            existing_files = []
            
            for config_file in self.env_config["required_config_files"]:
                file_path = self.project_root / config_file
                if file_path.exists():
                    existing_files.append(config_file)
                else:
                    missing_files.append(config_file)
            
            if missing_files:
                result.status = EnvironmentStatus.ERROR.value
                result.details = f"缺少配置文件: {', '.join(missing_files)}"
                result.suggestions.append("请确保所有配置文件都存在")
            else:
                result.status = EnvironmentStatus.HEALTHY.value
                result.details = f"所有配置文件都存在: {', '.join(existing_files)}"
            
        except Exception as e:
            result.status = EnvironmentStatus.ERROR.value
            result.errors.append(f"检查配置文件时出错: {str(e)}")
            result.details = "无法检查配置文件"
        
        return result
    
    def check_environment(self, component: EnvironmentComponent = EnvironmentComponent.ALL) -> Dict[str, EnvironmentCheckResult]:
        """检查环境"""
        print(f"\n=== 开始环境检查 ({component.value}) ===")
        
        if component == EnvironmentComponent.ALL:
            # 检查所有组件
            components = [
                EnvironmentComponent.PYTHON,
                EnvironmentComponent.VENV,
                EnvironmentComponent.NODE,
                EnvironmentComponent.PNPM,
                EnvironmentComponent.DEPENDENCIES,
                EnvironmentComponent.DATABASE,
                EnvironmentComponent.API_SERVER,
                EnvironmentComponent.MQTT_BROKER,
                EnvironmentComponent.CONFIG_FILES
            ]
        else:
            components = [component]
        
        for comp in components:
            print(f"检查 {comp.value}...")
            
            if comp == EnvironmentComponent.PYTHON:
                result = self.check_python_environment()
            elif comp == EnvironmentComponent.VENV:
                result = self.check_virtual_environment()
            elif comp == EnvironmentComponent.NODE:
                result = self.check_node_environment()
            elif comp == EnvironmentComponent.PNPM:
                result = self.check_pnpm()
            elif comp == EnvironmentComponent.DEPENDENCIES:
                result = self.check_dependencies()
            elif comp == EnvironmentComponent.DATABASE:
                result = self.check_database()
            elif comp == EnvironmentComponent.API_SERVER:
                result = self.check_api_server()
            elif comp == EnvironmentComponent.MQTT_BROKER:
                result = self.check_mqtt_broker()
            elif comp == EnvironmentComponent.CONFIG_FILES:
                result = self.check_config_files()
            else:
                continue
            
            self.check_results[comp.value] = result
            
            # 打印检查结果
            status_icon = "✓" if result.status == EnvironmentStatus.HEALTHY.value else "⚠" if result.status == EnvironmentStatus.WARNING.value else "✗"
            print(f"{status_icon} {comp.value}: {result.details}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"  警告: {warning}")
            
            if result.suggestions:
                for suggestion in result.suggestions:
                    print(f"  建议: {suggestion}")
        
        return self.check_results
    
    def get_environment_summary(self) -> Dict:
        """获取环境摘要"""
        if not self.check_results:
            return {"message": "没有环境检查结果"}
        
        healthy_count = sum(1 for r in self.check_results.values() if r.status == EnvironmentStatus.HEALTHY.value)
        warning_count = sum(1 for r in self.check_results.values() if r.status == EnvironmentStatus.WARNING.value)
        error_count = sum(1 for r in self.check_results.values() if r.status == EnvironmentStatus.ERROR.value)
        total_count = len(self.check_results)
        
        return {
            "total_components": total_count,
            "healthy_components": healthy_count,
            "warning_components": warning_count,
            "error_components": error_count,
            "health_percentage": f"{(healthy_count / total_count * 100):.1f}%" if total_count > 0 else "0%",
            "overall_status": "healthy" if error_count == 0 and warning_count == 0 else "warning" if error_count == 0 else "error"
        }
    
    def save_environment_report(self, report_path: Optional[Path] = None):
        """保存环境检查报告"""
        if report_path is None:
            report_path = self.project_root / f"environment_check_report_{int(time.time())}.json"
        
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": self.get_environment_summary(),
            "results": {}
        }
        
        for component, result in self.check_results.items():
            report_data["results"][component] = {
                "status": result.status,
                "details": result.details,
                "version": result.version,
                "path": result.path,
                "timestamp": result.timestamp,
                "errors": result.errors,
                "warnings": result.warnings,
                "suggestions": result.suggestions
            }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"✓ 环境检查报告已保存到 {report_path}")
        except Exception as e:
            print(f"✗ 保存环境检查报告时出错: {e}")
    
    def clear_results(self):
        """清除检查结果"""
        self.check_results.clear()
        print("✓ 环境检查结果已清除")