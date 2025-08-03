"""
統一金鑰管理器
處理演示模式、生產模式和開發模式的金鑰管理
"""

import os
import yaml
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class UnifiedKeyManager:
    """統一金鑰管理器"""
    
    def __init__(self, config_path: str = "configs/unified_demo_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.demo_mode = self._detect_demo_mode()
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _detect_demo_mode(self) -> bool:
        """檢測是否為演示模式"""
        if not self.config.get('demo_mode', {}).get('auto_detect', False):
            return False
            
        patterns = self.config.get('demo_mode', {}).get('detection_patterns', [])
        
        # 檢查環境變量
        for key, value in os.environ.items():
            if any(self._match_pattern(value, pattern) for pattern in patterns):
                logger.info(f"檢測到演示金鑰: {key}")
                return True
        
        return False
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """匹配模式"""
        import re
        try:
            return bool(re.match(pattern, value))
        except re.error:
            return pattern in value
    
    def get_key(self, key_name: str) -> Optional[str]:
        """獲取金鑰"""
        if self.demo_mode:
            # 演示模式使用固定金鑰
            fixed_keys = self.config.get('demo_mode', {}).get('fixed_keys', {})
            if key_name in fixed_keys:
                logger.info(f"使用演示金鑰: {key_name}")
                return fixed_keys[key_name]
        
        # 從環境變量獲取
        return os.environ.get(key_name)
    
    def setup_demo_environment(self):
        """設置演示環境"""
        if not self.demo_mode:
            return
            
        logger.info("設置演示環境...")
        
        # 設置固定金鑰
        fixed_keys = self.config.get('demo_mode', {}).get('fixed_keys', {})
        for key, value in fixed_keys.items():
            os.environ[key] = value
        
        # 執行自動動作
        auto_actions = self.config.get('demo_mode', {}).get('auto_actions', {})
        
        if auto_actions.get('learning'):
            self._setup_learning()
        
        if auto_actions.get('initialization'):
            self._setup_initialization()
        
        if auto_actions.get('cleanup'):
            self._setup_cleanup()
    
    def _setup_learning(self):
        """設置學習模式"""
        logger.info("啟用自動學習模式")
        learning_config = self.config.get('learning_config', {})
        
        # 創建學習數據目錄
        storage_path = Path(learning_config.get('storage_path', 'data/demo_learning'))
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # 設置學習環境變量
        os.environ['DEMO_LEARNING_ENABLED'] = 'true'
        os.environ['DEMO_LEARNING_PATH'] = str(storage_path)
    
    def _setup_initialization(self):
        """設置初始化"""
        logger.info("執行演示初始化")
        os.environ['DEMO_INIT_ENABLED'] = 'true'
    
    def _setup_cleanup(self):
        """設置清理"""
        logger.info("配置自動清理")
        os.environ['DEMO_CLEANUP_ENABLED'] = 'true'
    
    def generate_ham_key(self) -> str:
        """生成 HAM 金鑰"""
        if self.demo_mode:
            # 演示模式使用固定金鑰
            return self.get_key('MIKO_HAM_KEY') or 'DEMO_HAM_FIXED_KEY_2025_aGVsbG93b3JsZA=='
        
        # 生產模式生成新金鑰
        return Fernet.generate_key().decode()

# 全局實例
key_manager = UnifiedKeyManager()
