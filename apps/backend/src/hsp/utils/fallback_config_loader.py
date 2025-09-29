"""
HSP Fallback協議配置加載器
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

logger: Any = logging.getLogger(__name__)

class FallbackConfigLoader:
    """Fallback協議配置加載器"""
    
    DEFAULT_CONFIG = {
        "hsp_fallback": {
            "enabled": True,
            "protocols": {
                "http": {
                    "priority": 3,
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": 8765,
                    "timeout": 30
                },
                "file": {
                    "priority": 2,
                    "enabled": True,
                    "base_path": "data/fallback_comm",
                    "poll_interval": 0.5,
                    "max_file_size": 10485760
                },
                "memory": {
                    "priority": 1,
                    "enabled": True,
                    "queue_size": 1000
                }
            },
            "message": {
                "default_max_retries": 3,
                "default_ttl": 300,
                "health_check_interval": 30
            },
            "logging": {
                "level": "INFO",
                "log_fallback_usage": True,
                "log_protocol_switches": True
            }
        },
        "hsp_primary": {
            "mqtt": {
                "broker_address": "127.0.0.1",
                "broker_port": 1883,
                "keepalive": 60,
                "qos_default": 1
            },
            "connection": {
                "timeout": 10,
                "reconnect_interval": 5,
                "max_reconnect_attempts": 3
            },
            "health_check": {
                "interval": 60,
                "timeout": 5
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化配置加載器
        
        Args:
            config_path: 配置文件路徑，如果為None則使用默認路徑
        """
        self.config_path = config_path or self._find_config_file
        self._config: Optional[Dict[str, Any]] = None
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        possible_paths = [
            "configs/hsp_fallback_config.yaml",
            "Unified-AI-Project/configs/hsp_fallback_config.yaml",
            "../configs/hsp_fallback_config.yaml",
            "hsp_fallback_config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("未找到配置文件，將使用默認配置")
        return None
    
    def load_config(self) -> Dict[str, Any]:
        """加載配置"""
        if self._config is not None:
            return self._config
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                
                # 合併配置（文件配置覆蓋默認配置）
                self._config = self._merge_configs(self.DEFAULT_CONFIG, file_config)
                logger.info(f"已加載配置文件: {self.config_path}")
                
            except Exception as e:
                logger.error(f"加載配置文件失敗: {e}")
                self._config = self.DEFAULT_CONFIG.copy
        else:
            logger.info("使用默認配置")
            self._config = self.DEFAULT_CONFIG.copy
        
        return self._config
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """遞歸合併配置"""
        result = default.copy
        
        for key, value in override.items:
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """獲取fallback協議配置"""
        config = self.load_config
        return config.get("hsp_fallback", )
    
    def get_hsp_config(self) -> Dict[str, Any]:
        """獲取HSP主協議配置"""
        config = self.load_config
        return config.get("hsp_primary", )
    
    def is_fallback_enabled(self) -> bool:
        """檢查是否啟用fallback協議"""
        fallback_config = self.get_fallback_config
        return fallback_config.get("enabled", True)
    
    def get_protocol_config(self, protocol_name: str) -> Dict[str, Any]:
        """獲取特定協議的配置"""
        fallback_config = self.get_fallback_config
        protocols = fallback_config.get("protocols", )
        return protocols.get(protocol_name, )
    
    def get_message_config(self) -> Dict[str, Any]:
        """獲取消息配置"""
        fallback_config = self.get_fallback_config
        return fallback_config.get("message", )
    
    def get_logging_config(self) -> Dict[str, Any]:
        """獲取日誌配置"""
        fallback_config = self.get_fallback_config
        return fallback_config.get("logging", )
    
    def save_config(self, config: Dict[str, Any], path: Optional[str] = None):
        """保存配置到文件"""
        save_path = path or self.config_path or "hsp_fallback_config.yaml"
        
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
            raise
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """驗證配置的有效性"""
        config = config or self.load_config
        
        try:
            # 檢查必要的配置項
            fallback_config = config.get("hsp_fallback", )
            
            # 檢查協議配置
            protocols = fallback_config.get("protocols", )
            for protocol_name, protocol_config in protocols.items:
                if not isinstance(protocol_config.get("priority"), int):
                    logger.error(f"協議 {protocol_name} 的優先級必須是整數")
                    return False
                
                if not isinstance(protocol_config.get("enabled"), bool):
                    logger.error(f"協議 {protocol_name} 的enabled必須是布爾值")
                    return False
            
            # 檢查消息配置
            message_config = fallback_config.get("message", )
            if message_config.get("default_max_retries") is not None:
                if not isinstance(message_config["default_max_retries"], int) or message_config["default_max_retries"] < 0:
                    logger.error("default_max_retries必須是非負整數")
                    return False
            
            if message_config.get("default_ttl") is not None:
                if not isinstance(message_config["default_ttl"], (int, float)) or message_config["default_ttl"] <= 0:
                    logger.error("default_ttl必須是正數")
                    return False
            
            logger.info("配置驗證通過")
            return True
            
        except Exception as e:
            logger.error(f"配置驗證失敗: {e}")
            return False

# 全局配置加載器實例
_config_loader: Optional[FallbackConfigLoader] = None

def get_config_loader(config_path: Optional[str] = None) -> FallbackConfigLoader:
    """獲取全局配置加載器實例"""
    global _config_loader
    if _config_loader is None or config_path is not None:
        _config_loader = FallbackConfigLoader(config_path)
    return _config_loader

def load_fallback_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """快速加載fallback配置"""
    loader = get_config_loader(config_path)
    return loader.get_fallback_config

def load_hsp_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """快速加載HSP配置"""
    loader = get_config_loader(config_path)
    return loader.get_hsp_config