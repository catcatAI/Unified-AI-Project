# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A/B/C] L2+
# =============================================================================
#
# 职责: 统一金钥管理器，处理演示模式、生产模式和开发模式的金钥管理
# 维度: 涉及所有维度，管理 A/B/C 三层安全密钥
# 安全: 处理 Key A (后端控制)、Key B (移动通信)、Key C (桌面同步)
# 成熟度: L2+ 等级理解密钥管理的重要性
#
# =============================================================================

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

logger = logging.getLogger(__name__)

class UnifiedKeyManager:
    """統一金鑰管理器"""
    
    def __init__(self, config_path: str = "configs/unified_demo_config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.demo_mode = self._detect_demo_mode()
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if yaml:
                    return yaml.safe_load(f)
        return {}
        
    def _detect_demo_mode(self) -> bool:
        """檢測是否為演示模式"""
        demo_cfg = self.config.get('demo_mode', {})
        
        # 顯式啟用開關(若配置中提供 enabled = True, 直接啟用)
        if demo_cfg.get('enabled') is True:
            logger.info("配置中啟用 demo_mode.enabled = True, 啟用演示模式")
            return True
        
        # 自動偵測開關
        if not demo_cfg.get('auto_detect', False):
            return False
        
        patterns = demo_cfg.get('detection_patterns', [])
        
        # 明確 DEMO_FLAG 支持(任何真值都啟用)
        demo_flag = os.environ.get('DEMO_FLAG')

        if isinstance(demo_flag, str) and demo_flag.lower() in {"1", "true", "yes", "on"}:
            logger.info("檢測到 DEMO_FLAG = true, 啟用演示模式")
            return True
        
        # 檢查環境變量的「鍵」或「值」是否匹配
        for k, v in os.environ.items():
            # 鍵匹配(滿足如 ^DEMO_ 的場景)
            if any(self._match_pattern(k, ptn) for ptn in patterns):
                logger.info(f"檢測到演示環境變量鍵: {k}")
                return True
            # 值匹配(原有行為)
            if any(self._match_pattern(v, ptn) for ptn in patterns):
                logger.info(f"檢測到演示金鑰: {k}")
                return True
        
        return False
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """匹配模式"""
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
        """設置學習環境"""
        logger.info("初始化演示學習環境(示範)")
    
    def _setup_initialization(self):
        """設置初始化"""
        logger.info("執行演示初始化(示範)")
    
    def _setup_cleanup(self):
        """設置清理任務"""
        logger.info("設定演示清理任務(示範)")
    
    def generate_ham_key(self) -> str:
        """生成 HAM 金鑰"""
        if self.demo_mode:
            # 演示模式使用固定金鑰
            return self.get_key('MIKO_HAM_KEY') or 'DEMO_HAM_FIXED_KEY_2025_aGVsbG93b3JsZA=='
        
        # 生產模式生成新金鑰
        if Fernet:
            return Fernet.generate_key().decode()
        return 'DEFAULT_KEY'
    
    def get_key_a(self) -> str:
        """獲取 Key A (後端控制)"""
        return self.get_key('ANGELA_KEY_A') or 'DEMO_KEY_A_2025'
    
    def get_key_b(self) -> str:
        """獲取 Key B (移動通信)"""
        return self.get_key('ANGELA_KEY_B') or 'DEMO_KEY_B_2025'
    
    def get_key_c(self) -> str:
        """獲取 Key C (桌面同步)"""
        return self.get_key('ANGELA_KEY_C') or 'DEMO_KEY_C_2025'

# 全局實例
key_manager = UnifiedKeyManager()