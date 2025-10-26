"""
統一金鑰管理器
處理演示模式、生產模式和開發模式的金鑰管理
"""

from diagnose_base_agent import
# TODO: Fix import - module 'yaml' not found
from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'pathlib' not found
# TODO: Fix import - module 'typing' not found
# TODO: Fix import - module 'cryptography.fernet' not found

logger: Any = logging.getLogger(__name__)

class UnifiedKeyManager:
    """統一金鑰管理器"""



    
    def __init__(self, config_path: str = "configs/unified_demo_config.yaml") -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config
        self.demo_mode = self._detect_demo_mode
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        if self.config_path.exists:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return 
    
    def _detect_demo_mode(self) -> bool:
        """檢測是否為演示模式"""
        demo_cfg = self.config.get('demo_mode')
        
        # 顯式啟用開關(若配置中提供 enabled=True,直接啟用)
        if demo_cfg.get('enabled') is True:

            logger.info("配置中啟用 demo_mode.enabled=True,啟用演示模式")
            return True
        
        # 自動偵測開關
        if not demo_cfg.get('auto_detect', False):
            return False
        
        patterns = demo_cfg.get('detection_patterns')
        
        # 明確 DEMO_FLAG 支持(任何真值都啟用)
        demo_flag = os.environ.get('DEMO_FLAG')

        if isinstance(demo_flag, str) and demo_flag.lower() in {"1", "true", "yes", "on"}:
            logger.info("檢測到 DEMO_FLAG=true,啟用演示模式")
            return True
        
        # 檢查環境變量的「鍵」或「值」是否匹配
        for k, v in os.environ.items:
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
from tests.core_ai import
        try:
            return bool(re.match(pattern, value))
        except re.error:
            return pattern in value

    
    def get_key(self, key_name: str) -> Optional[str]:
        """獲取金鑰"""
        if self.demo_mode:
            # 演示模式使用固定金鑰
            fixed_keys = self.config.get('demo_mode').get('fixed_keys')
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
        fixed_keys = self.config.get('demo_mode').get('fixed_keys')
        for key, value in fixed_keys.items:
            os.environ[key] = value
        
        # 執行自動動作
        auto_actions = self.config.get('demo_mode').get('auto_actions')
        
        if auto_actions.get('learning'):
            self._setup_learning
        
        if auto_actions.get('initialization'):
            self._setup_initialization
        
        if auto_actions.get('cleanup'):
            self._setup_cleanup
    
    def _setup_learning(self):
        # 這裡為簡化示範,實際可調用 DemoLearningManager 等

        logger.info("初始化演示學習環境(示範)")
    
    def _setup_initialization(self):
        logger.info("執行演示初始化(示範)")
    
    def _setup_cleanup(self):
        logger.info("設定演示清理任務(示範)")
    
    def generate_ham_key(self) -> str:
        """生成 HAM 金鑰"""
        if self.demo_mode:
            # 演示模式使用固定金鑰
            return self.get_key('MIKO_HAM_KEY') or 'DEMO_HAM_FIXED_KEY_2025_aGVsbG93b3JsZA=='
#         
        # 生產模式生成新金鑰
        return Fernet.generate_key.decode
# 
# 全局實例
key_manager = UnifiedKeyManager