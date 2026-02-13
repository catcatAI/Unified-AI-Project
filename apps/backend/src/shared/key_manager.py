"""
Angela AI v6.0 - Key Manager (Legacy Support & Refined)
統一金鑰管理器

提供對 A/B/C 密鑰體系的訪問，並保留對舊有配置的相容性。

修复版本：改进密钥管理
- 持久化密钥存储
- 密钥轮换机制
- 密钥验证
- 环境变量设置
"""

import os
import logging
import secrets
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import yaml

logger = logging.getLogger(__name__)

class UnifiedKeyManager:
    """統一金鑰管理器 (明確區分通訊密鑰與模型金鑰)

    修复版本：改进的密钥管理
    - 持久化密钥存储
    - 密钥轮换机制
    - 密钥验证
    """

    def __init__(self, config_path: str = "configs/unified_demo_config.yaml", keys_file: str = "data/secure_keys.json") -> None:
        self.config_path = Path(config_path)
        self.keys_file = Path(keys_file)
        self.config = self._load_config()

        # 1. 系統通訊密鑰 (Angela Secret Keys: A/B/C)
        # 用於內部組件、行動端、桌面端的加密與控制
        try:
            from ..system.security_monitor import ABCKeyManager
            self.abc_km = ABCKeyManager()
        except ImportError:
            self.abc_km = None
            logger.warning("ABCKeyManager 不可用，使用本地密钥管理")

        # ========== 修复：持久化密钥管理 ==========
        self.keys_data: Dict[str, Any] = self._load_keys()

        # 密钥轮换设置
        self.key_rotation_days = 30  # 每 30 天轮换一次密钥

    def _load_config(self) -> Dict[str, Any]:
        """載入舊有 YAML 配置 (通常包含模型 API Keys)"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"載入配置失敗: {e}")
        return {}

    def _load_keys(self) -> Dict[str, Any]:
        """加载持久化的密钥数据"""
        # 确保数据目录存在
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)

        if self.keys_file.exists():
            try:
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载密钥文件失败: {e}，将创建新密钥")

        # 如果文件不存在，创建默认密钥
        return self._generate_default_keys()

    def _generate_default_keys(self) -> Dict[str, Any]:
        """生成默认密钥"""
        keys_data = {
            "keys": {
                "KeyA": secrets.token_hex(32),
                "KeyB": secrets.token_hex(32),
                "KeyC": secrets.token_hex(32)
            },
            "key_hashes": {},
            "created_at": datetime.now().isoformat(),
            "last_rotation": datetime.now().isoformat(),
            "version": "1.0"
        }

        # 计算密钥哈希
        for key_name, key_value in keys_data["keys"].items():
            keys_data["key_hashes"][key_name] = self._hash_key(key_value)

        # 保存密钥
        self._save_keys(keys_data)

        logger.info("已生成并保存默认密钥")
        return keys_data

    def _hash_key(self, key: str) -> str:
        """计算密钥哈希（用于验证）"""
        return hashlib.sha256(key.encode()).hexdigest()

    def _save_keys(self, keys_data: Dict[str, Any]):
        """保存密钥数据"""
        try:
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(keys_data, f, indent=2)
            # 设置文件权限（仅所有者可读写）
            os.chmod(self.keys_file, 0o600)
        except Exception as e:
            logger.error(f"保存密钥失败: {e}")

    def _should_rotate_keys(self) -> bool:
        """检查是否需要轮换密钥"""
        last_rotation = datetime.fromisoformat(self.keys_data.get("last_rotation", datetime.now().isoformat()))
        next_rotation = last_rotation + timedelta(days=self.key_rotation_days)
        return datetime.now() >= next_rotation

    def _rotate_keys(self):
        """轮换密钥"""
        logger.info("开始轮换密钥...")

        # 生成新密钥
        for key_name in ["KeyA", "KeyB", "KeyC"]:
            old_key = self.keys_data["keys"].get(key_name)
            new_key = secrets.token_hex(32)

            # 验证新密钥
            if old_key and self._hash_key(old_key) == self.keys_data["key_hashes"].get(key_name):
                logger.info(f"验证旧密钥 {key_name} 成功，生成新密钥")
            else:
                logger.warning(f"验证旧密钥 {key_name} 失败，直接生成新密钥")

            # 更新密钥
            self.keys_data["keys"][key_name] = new_key
            self.keys_data["key_hashes"][key_name] = self._hash_key(new_key)

        # 更新轮换时间
        self.keys_data["last_rotation"] = datetime.now().isoformat()

        # 保存新密钥
        self._save_keys(self.keys_data)

        logger.info("密钥轮换完成")

    def get_security_key(self, key_name: str) -> Optional[str]:
        """獲取 Angela 系統通訊密鑰 (KeyA, KeyB, KeyC)"""
        # 检查是否需要轮换密钥
        if self._should_rotate_keys():
            self._rotate_keys()

        # 优先从 ABCKeyManager 获取
        if self.abc_km and key_name in ["KeyA", "KeyB", "KeyC"]:
            key = self.abc_km.get_key(key_name)
            if key:
                return key

        # 从本地密钥存储获取
        if key_name in self.keys_data.get("keys", {}):
            return self.keys_data["keys"][key_name]

        return None

    def verify_key(self, key_name: str, key_value: str) -> bool:
        """验证密钥是否正确"""
        if key_name not in self.keys_data.get("keys", {}):
            return False

        stored_hash = self.keys_data["key_hashes"].get(key_name)
        provided_hash = self._hash_key(key_value)

        return stored_hash == provided_hash

    def get_api_key(self, service_name: str) -> Optional[str]:
        """獲取外部模型服務金鑰 (如 OpenAI, Anthropic API Keys)"""
        # 優先從環境變量獲取，然後從配置文件獲取
        env_key = os.environ.get(f"{service_name.upper()}_API_KEY")
        if env_key:
            return env_key
        return self.config.get("api_keys", {}).get(service_name)

    def get_key(self, key_name: str) -> Optional[str]:
        """通用檢索 (向下相容)"""
        # 優先檢查是否為 A/B/C 密鑰
        sec_key = self.get_security_key(key_name)
        if sec_key:
            return sec_key

        # 否則作為 API 金鑰或環境變量處理
        return os.environ.get(key_name) or self.config.get(key_name)

    def setup_environment(self):
        """設置運行環境金鑰"""
        # 检查是否需要轮换密钥
        if self._should_rotate_keys():
            self._rotate_keys()

        # 设置 A/B/C 密钥到环境变量
        if self.abc_km:
            for k in ["KeyA", "KeyB", "KeyC"]:
                val = self.abc_km.get_key(k)
                if val:
                    os.environ[k] = val
        else:
            # 从本地密钥存储设置
            for k in ["KeyA", "KeyB", "KeyC"]:
                val = self.keys_data["keys"].get(k)
                if val:
                    os.environ[k] = val

        logger.info("✅ 安全金鑰環境已設置完成")

    def get_key_info(self) -> Dict[str, Any]:
        """获取密钥信息（不包含实际密钥）"""
        return {
            "version": self.keys_data.get("version", "unknown"),
            "created_at": self.keys_data.get("created_at", "unknown"),
            "last_rotation": self.keys_data.get("last_rotation", "unknown"),
            "next_rotation": (datetime.fromisoformat(self.keys_data.get("last_rotation", datetime.now().isoformat())) +
                             timedelta(days=self.key_rotation_days)).isoformat(),
            "rotation_interval_days": self.key_rotation_days,
            "keys_available": list(self.keys_data.get("keys", {}).keys())
        }
