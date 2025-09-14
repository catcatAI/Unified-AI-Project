#!/usr/bin/env python3
"""
配置管理器核心模块 - 统一管理所有配置文件和设置
"""

import json
import yaml
import os
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum

class ConfigType(Enum):
    """配置类型枚举"""
    SYSTEM = "system"                # 系统配置
    HSP = "hsp"                      # HSP协议配置
    DATABASE = "database"            # 数据库配置
    API = "api"                      # API配置
    TEST = "test"                    # 测试配置
    DEPLOYMENT = "deployment"        # 部署配置
    DEVELOPMENT = "development"      # 开发配置
    FIX = "fix"                      # 修复配置
    ENVIRONMENT = "environment"      # 环境配置
    CUSTOM = "custom"                # 自定义配置

class ConfigFormat(Enum):
    """配置格式枚举"""
    JSON = "json"                    # JSON格式
    YAML = "yaml"                    # YAML格式
    INI = "ini"                      # INI格式
    TOML = "toml"                    # TOML格式
    ENV = "env"                      # 环境变量格式

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.frontend_root = project_root / "apps" / "frontend-dashboard"
        self.desktop_root = project_root / "apps" / "desktop-app"
        
        # 配置目录
        self.configs_dir = project_root / "configs"
        self.backend_configs_dir = self.backend_root / "configs"
        
        # 确保配置目录存在
        self.configs_dir.mkdir(exist_ok=True)
        self.backend_configs_dir.mkdir(exist_ok=True)
        
        # 配置文件路径映射
        self.config_paths = {
            ConfigType.SYSTEM: self.backend_configs_dir / "system_config.yaml",
            ConfigType.HSP: self.backend_configs_dir / "hsp_fallback_config.yaml",
            ConfigType.DATABASE: self.backend_configs_dir / "database_config.yaml",
            ConfigType.API: self.backend_configs_dir / "api_config.yaml",
            ConfigType.TEST: self.backend_configs_dir / "test_config.yaml",
            ConfigType.DEPLOYMENT: self.backend_configs_dir / "deployment_config.yaml",
            ConfigType.DEVELOPMENT: self.backend_configs_dir / "development_config.yaml",
            ConfigType.FIX: self.configs_dir / "fix_config.yaml",
            ConfigType.ENVIRONMENT: self.configs_dir / "environment_config.yaml",
            ConfigType.CUSTOM: self.configs_dir / "custom_config.yaml"
        }
        
        # 默认配置
        self.default_configs = {
            ConfigType.SYSTEM: {
                "operational_configs": {
                    "api_server": {
                        "host": "localhost",
                        "port": 8000
                    },
                    "database": {
                        "type": "firebase",
                        "timeout": 30
                    },
                    "mqtt": {
                        "broker_address": "localhost",
                        "broker_port": 1883
                    }
                },
                "development_configs": {
                    "debug_mode": True,
                    "log_level": "DEBUG"
                }
            },
            ConfigType.HSP: {
                "hsp_primary": {
                    "mqtt": {
                        "broker_address": "localhost",
                        "broker_port": 1883,
                        "keepalive": 60,
                        "clean_session": True
                    }
                },
                "hsp_fallback": {
                    "mqtt": {
                        "broker_address": "localhost",
                        "broker_port": 1883,
                        "keepalive": 60,
                        "clean_session": True
                    }
                }
            },
            ConfigType.TEST: {
                "test_settings": {
                    "timeout": 300,
                    "verbose": False,
                    "coverage": True
                },
                "test_paths": {
                    "unit_tests": "tests/",
                    "integration_tests": "tests/integration/",
                    "e2e_tests": "tests/e2e/"
                }
            },
            ConfigType.FIX: {
                "fix_settings": {
                    "auto_fix": True,
                    "backup_files": True,
                    "verbose": False
                },
                "fix_types": {
                    "import_fixes": True,
                    "dependency_fixes": True,
                    "syntax_fixes": True,
                    "cleanup_fixes": True
                }
            },
            ConfigType.ENVIRONMENT: {
                "environment_checks": {
                    "python": True,
                    "node": True,
                    "database": True,
                    "api_server": True,
                    "mqtt_broker": True
                },
                "retention_policies": {
                    "logs": 7,
                    "cache": 1,
                    "reports": 30,
                    "backups": 90
                }
            }
        }
        
        # 配置缓存
        self.config_cache: Dict[str, Any] = {}
        
        # 配置验证规则
        self.validation_rules = {
            ConfigType.SYSTEM: {
                "required_keys": ["operational_configs"],
                "key_types": {
                    "operational_configs.api_server.host": str,
                    "operational_configs.api_server.port": int,
                    "operational_configs.database.type": str,
                    "operational_configs.database.timeout": int
                }
            },
            ConfigType.HSP: {
                "required_keys": ["hsp_primary", "hsp_fallback"],
                "key_types": {
                    "hsp_primary.mqtt.broker_address": str,
                    "hsp_primary.mqtt.broker_port": int,
                    "hsp_fallback.mqtt.broker_address": str,
                    "hsp_fallback.mqtt.broker_port": int
                }
            },
            ConfigType.TEST: {
                "required_keys": ["test_settings"],
                "key_types": {
                    "test_settings.timeout": int,
                    "test_settings.verbose": bool,
                    "test_settings.coverage": bool
                }
            }
        }
    
    def get_config_path(self, config_type: ConfigType) -> Path:
        """获取配置文件路径"""
        return self.config_paths.get(config_type, self.configs_dir / f"{config_type.value}.yaml")
    
    def load_config(self, config_type: ConfigType, use_cache: bool = True) -> Dict[str, Any]:
        """加载配置"""
        cache_key = f"{config_type.value}_{time.time() // 60}"  # 每分钟更新缓存
        
        if use_cache and cache_key in self.config_cache:
            return self.config_cache[cache_key]
        
        config_path = self.get_config_path(config_type)
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.suffix.lower() in ['.yaml', '.yml']:
                        config = yaml.safe_load(f)
                    elif config_path.suffix.lower() == '.json':
                        config = json.load(f)
                    else:
                        raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
                
                # 验证配置
                if not self.validate_config(config_type, config):
                    print(f"⚠ 配置 {config_type.value} 验证失败，使用默认配置")
                    config = self.default_configs.get(config_type, {})
                
                # 合并默认配置
                config = self.merge_configs(self.default_configs.get(config_type, {}), config)
                
            else:
                # 配置文件不存在，使用默认配置
                config = self.default_configs.get(config_type, {})
                print(f"⚠ 配置文件 {config_path} 不存在，使用默认配置")
            
            # 缓存配置
            if use_cache:
                self.config_cache[cache_key] = config
            
            return config
            
        except Exception as e:
            print(f"✗ 加载配置 {config_type.value} 失败: {e}")
            return self.default_configs.get(config_type, {})
    
    def save_config(self, config_type: ConfigType, config: Dict[str, Any], 
                   create_backup: bool = True) -> bool:
        """保存配置"""
        config_path = self.get_config_path(config_type)
        
        try:
            # 创建备份
            if create_backup and config_path.exists():
                backup_path = config_path.with_suffix(f"{config_path.suffix}.backup")
                backup_path.write_text(config_path.read_text(encoding='utf-8'), encoding='utf-8')
            
            # 验证配置
            if not self.validate_config(config_type, config):
                print(f"✗ 配置 {config_type.value} 验证失败，无法保存")
                return False
            
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif config_path.suffix.lower() == '.json':
                    json.dump(config, f, ensure_ascii=False, indent=2)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
            
            # 清除缓存
            self.clear_cache(config_type)
            
            print(f"✓ 配置 {config_type.value} 已保存到 {config_path}")
            return True
            
        except Exception as e:
            print(f"✗ 保存配置 {config_type.value} 失败: {e}")
            return False
    
    def validate_config(self, config_type: ConfigType, config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            rules = self.validation_rules.get(config_type, {})
            
            # 检查必需的键
            if "required_keys" in rules:
                for key in rules["required_keys"]:
                    if not self._get_nested_value(config, key):
                        print(f"✗ 缺少必需的配置键: {key}")
                        return False
            
            # 检查键类型
            if "key_types" in rules:
                for key_path, expected_type in rules["key_types"].items():
                    value = self._get_nested_value(config, key_path)
                    if value is not None and not isinstance(value, expected_type):
                        print(f"✗ 配置键 {key_path} 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"✗ 验证配置时出错: {e}")
            return False
    
    def merge_configs(self, default_config: Dict, user_config: Dict) -> Dict:
        """合并配置"""
        result = default_config.copy()
        
        for key, value in user_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config_value(self, config_type: ConfigType, key_path: str, 
                        default: Any = None) -> Any:
        """获取配置值"""
        config = self.load_config(config_type)
        return self._get_nested_value(config, key_path, default)
    
    def set_config_value(self, config_type: ConfigType, key_path: str, 
                        value: Any, save: bool = True) -> bool:
        """设置配置值"""
        config = self.load_config(config_type)
        
        if not self._set_nested_value(config, key_path, value):
            return False
        
        if save:
            return self.save_config(config_type, config)
        
        return True
    
    def _get_nested_value(self, config: Dict, key_path: str, default: Any = None) -> Any:
        """获取嵌套配置值"""
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _set_nested_value(self, config: Dict, key_path: str, value: Any) -> bool:
        """设置嵌套配置值"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return True
    
    def list_configs(self) -> List[ConfigType]:
        """列出所有配置类型"""
        return list(ConfigType)
    
    def config_exists(self, config_type: ConfigType) -> bool:
        """检查配置是否存在"""
        config_path = self.get_config_path(config_type)
        return config_path.exists()
    
    def create_default_config(self, config_type: ConfigType) -> bool:
        """创建默认配置"""
        if config_type in self.default_configs:
            return self.save_config(config_type, self.default_configs[config_type], create_backup=False)
        else:
            print(f"✗ 配置类型 {config_type.value} 没有默认配置")
            return False
    
    def backup_config(self, config_type: ConfigType, backup_path: Optional[Path] = None) -> bool:
        """备份配置"""
        config_path = self.get_config_path(config_type)
        
        if not config_path.exists():
            print(f"✗ 配置文件 {config_path} 不存在")
            return False
        
        if backup_path is None:
            timestamp = int(time.time())
            backup_path = config_path.with_suffix(f"{config_path.suffix}.backup_{timestamp}")
        
        try:
            backup_path.write_text(config_path.read_text(encoding='utf-8'), encoding='utf-8')
            print(f"✓ 配置 {config_type.value} 已备份到 {backup_path}")
            return True
        except Exception as e:
            print(f"✗ 备份配置 {config_type.value} 失败: {e}")
            return False
    
    def restore_config(self, config_type: ConfigType, backup_path: Path) -> bool:
        """恢复配置"""
        config_path = self.get_config_path(config_type)
        
        if not backup_path.exists():
            print(f"✗ 备份文件 {backup_path} 不存在")
            return False
        
        try:
            # 验证备份配置
            with open(backup_path, 'r', encoding='utf-8') as f:
                if backup_path.suffix.lower() in ['.yaml', '.yml']:
                    backup_config = yaml.safe_load(f)
                elif backup_path.suffix.lower() == '.json':
                    backup_config = json.load(f)
                else:
                    raise ValueError(f"不支持的备份文件格式: {backup_path.suffix}")
            
            if not self.validate_config(config_type, backup_config):
                print(f"✗ 备份配置验证失败")
                return False
            
            # 恢复配置
            config_path.write_text(backup_path.read_text(encoding='utf-8'), encoding='utf-8')
            
            # 清除缓存
            self.clear_cache(config_type)
            
            print(f"✓ 配置 {config_type.value} 已从 {backup_path} 恢复")
            return True
            
        except Exception as e:
            print(f"✗ 恢复配置 {config_type.value} 失败: {e}")
            return False
    
    def clear_cache(self, config_type: Optional[ConfigType] = None):
        """清除配置缓存"""
        if config_type:
            # 清除特定配置类型的缓存
            keys_to_remove = [key for key in self.config_cache.keys() if key.startswith(config_type.value)]
            for key in keys_to_remove:
                del self.config_cache[key]
        else:
            # 清除所有缓存
            self.config_cache.clear()
        
        print("✓ 配置缓存已清除")
    
    def reload_config(self, config_type: ConfigType) -> Dict[str, Any]:
        """重新加载配置"""
        self.clear_cache(config_type)
        return self.load_config(config_type, use_cache=False)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configs": {},
            "cache_size": len(self.config_cache)
        }
        
        for config_type in ConfigType:
            config_path = self.get_config_path(config_type)
            summary["configs"][config_type.value] = {
                "exists": config_path.exists(),
                "path": str(config_path),
                "size": config_path.stat().st_size if config_path.exists() else 0,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", 
                                       time.localtime(config_path.stat().st_mtime)) if config_path.exists() else None
            }
        
        return summary
    
    def export_config(self, config_type: ConfigType, output_path: Path, 
                     output_format: ConfigFormat = ConfigFormat.YAML) -> bool:
        """导出配置"""
        config = self.load_config(config_type)
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_format == ConfigFormat.YAML:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif output_format == ConfigFormat.JSON:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                else:
                    raise ValueError(f"不支持的导出格式: {output_format.value}")
            
            print(f"✓ 配置 {config_type.value} 已导出到 {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ 导出配置 {config_type.value} 失败: {e}")
            return False
    
    def import_config(self, config_type: ConfigType, input_path: Path) -> bool:
        """导入配置"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                if input_path.suffix.lower() in ['.yaml', '.yml']:
                    imported_config = yaml.safe_load(f)
                elif input_path.suffix.lower() == '.json':
                    imported_config = json.load(f)
                else:
                    raise ValueError(f"不支持的导入文件格式: {input_path.suffix}")
            
            # 验证导入的配置
            if not self.validate_config(config_type, imported_config):
                print(f"✗ 导入的配置验证失败")
                return False
            
            # 保存配置
            return self.save_config(config_type, imported_config)
            
        except Exception as e:
            print(f"✗ 导入配置 {config_type.value} 失败: {e}")
            return False