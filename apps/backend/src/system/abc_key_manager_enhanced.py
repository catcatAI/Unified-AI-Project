"""
Angela AI v6.2.0 - Enhanced A/B/C Key Manager
增强的 A/B/C 密钥管理系统

功能：
1. 密钥轮换机制 - 定期或手动轮换密钥
2. 密钥验证 - 验证密钥格式和有效性
3. 密钥过期管理 - 支持密钥过期时间
4. 密钥历史记录 - 保留历史密钥用于验证旧数据
5. 密钥强度检查 - 确保密钥符合安全标准

密钥用途：
- KeyA: 后端控制 - 管理系统核心权限与安全托盘监控器
- KeyB: 移动通信 - 专用於手機端加密通訊
- KeyC: 桌面同步 - 处理跨设备数据同步与本地 AES-256 加密
"""

import os
import json
import time
import hashlib
import secrets
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# 密钥配置
KEY_CONFIG = {
    'rotation_interval_days': 30,  # 密钥轮换间隔（天）
    'key_history_limit': 5,  # 保留的历史密钥数量
    'min_key_age_hours': 1,  # 密钥最小存活时间（防止过于频繁轮换）
    'key_strength_bits': 256,  # 密钥强度（位）
    'enable_auto_rotation': True  # 是否启用自动轮换
}

# 密钥用途描述
KEY_PURPOSES = {
    'KeyA': {
        'name': 'Backend Control Key',
        'description': '管理系统核心权限与安全托盘监控器',
        'rotation_priority': 'high',
        'critical': True
    },
    'KeyB': {
        'name': 'Mobile Communication Key',
        'description': '专用於手機端加密通訊',
        'rotation_priority': 'medium',
        'critical': True
    },
    'KeyC': {
        'name': 'Desktop Sync Key',
        'description': '处理跨设备数据同步与本地 AES-256 加密',
        'rotation_priority': 'medium',
        'critical': True
    }
}


class EnhancedABCKeyManager:
    """增强的 A/B/C 密钥管理器"""
    
    def __init__(self, key_dir: Optional[Path] = None):
        self.key_dir = key_dir or Path(__file__).parent.parent.parent / "data" / "security"
        self.key_dir.mkdir(parents=True, exist_ok=True)
        
        # 密钥文件
        self.key_file = self.key_dir / "abc_keys.json"
        self.key_history_file = self.key_dir / "abc_keys_history.json"
        self.key_rotation_log_file = self.key_dir / "abc_key_rotation.log"
        
        # 加载或生成密钥
        self.keys = self._load_or_generate_keys()
        self.key_history = self._load_key_history()
        
        # 初始化轮换检查
        self._check_rotation_needed()
    
    def _load_or_generate_keys(self) -> Dict[str, str]:
        """加载现有密钥或生成新密钥"""
        if self.key_file.exists():
            try:
                with open(self.key_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                
                # 验证密钥格式
                if self._validate_keys(data):
                    logger.info(f"✅ 已加载现有 A/B/C 密钥: {self.key_file}")
                    return data
                else:
                    logger.warning("⚠️ 现有密钥验证失败，将生成新密钥")
            except Exception as e:
                logger.error(f"读取密钥文件失败: {e}")
        
        # 生成新密钥
        return self._generate_new_keys(force=True)
    
    def _generate_new_keys(self, force: bool = False) -> Dict[str, str]:
        """
        生成新的 A/B/C 密钥
        
        Args:
            force: 是否强制生成（忽略最小存活时间）
        
        Returns:
            新生成的密钥字典
        """
        # 检查密钥最小存活时间
        if not force and 'created_at' in self.keys:
            key_age_hours = (time.time() - self.keys['created_at']) / 3600
            if key_age_hours < KEY_CONFIG['min_key_age_hours']:
                logger.warning(f"密钥存活时间不足 ({key_age_hours:.1f}h < {KEY_CONFIG['min_key_age_hours']}h)，拒绝轮换")
                return self.keys
        
        # 保存旧密钥到历史记录
        old_keys = {k: v for k, v in self.keys.items() if k.startswith('Key')}
        if old_keys:
            self._save_key_to_history(old_keys)
        
        # 生成新密钥
        new_keys = {
            "KeyA": Fernet.generate_key().decode(),
            "KeyB": Fernet.generate_key().decode(),
            "KeyC": Fernet.generate_key().decode(),
            "created_at": time.time(),
            "rotated_at": time.time(),
            "version": self._get_next_version()
        }
        
        # 保存新密钥
        with open(self.key_file, "w", encoding='utf-8') as f:
            json.dump(new_keys, f, indent=4)
        
        # 记录轮换日志
        self._log_rotation(new_keys, old_keys)
        
        logger.info(f"✅ 已生成新的 A/B/C 密钥体系: {self.key_file}")
        logger.info(f"   密钥版本: {new_keys['version']}")
        logger.info(f"   KeyA: {self._mask_key(new_keys['KeyA'])}")
        logger.info(f"   KeyB: {self._mask_key(new_keys['KeyB'])}")
        logger.info(f"   KeyC: {self._mask_key(new_keys['KeyC'])}")
        
        return new_keys
    
    def _validate_keys(self, keys: Dict[str, str]) -> bool:
        """
        验证密钥格式和有效性
        
        Args:
            keys: 密钥字典
        
        Returns:
            是否有效
        """
        # 检查必需的密钥
        required_keys = ['KeyA', 'KeyB', 'KeyC']
        for key_name in required_keys:
            if key_name not in keys:
                logger.error(f"缺少必需的密钥: {key_name}")
                return False
            
            key_value = keys[key_name]
            if not key_value or len(key_value) < 32:
                logger.error(f"密钥 {key_name} 长度不足")
                return False
            
            # 尝试验证密钥格式（Fernet 密钥必须是 44 个字符的 base64）
            try:
                # Fernet 密钥格式：urlsafe_base64(32 bytes) = 44 chars
                if len(key_value) != 44:
                    logger.error(f"密钥 {key_name} 格式不正确 (期望 44 字符)")
                    return False
                
                # 尝试使用密钥（如果有效则格式正确）
                Fernet(key_value.encode())
            except Exception as e:
                logger.error(f"密钥 {key_name} 无效: {e}")
                return False
        
        # 检查创建时间
        if 'created_at' not in keys:
            logger.warning("密钥缺少创建时间戳")
        
        return True
    
    def _load_key_history(self) -> List[Dict[str, str]]:
        """加载密钥历史记录"""
        if self.key_history_file.exists():
            try:
                with open(self.key_history_file, "r", encoding='utf-8') as f:
                    history = json.load(f)
                
                # 按时间倒序排序（最新的在前）
                history.sort(key=lambda x: x.get('rotated_at', 0), reverse=True)
                
                # 限制历史记录数量
                return history[:KEY_CONFIG['key_history_limit']]
            except Exception as e:
                logger.error(f"读取密钥历史失败: {e}")
        
        return []
    
    def _save_key_to_history(self, old_keys: Dict[str, str]) -> None:
        """保存旧密钥到历史记录"""
        entry = {
            'keys': {k: self._mask_key(v) for k, v in old_keys.items() if k.startswith('Key')},
            'original_keys': {k: v for k, v in old_keys.items() if k.startswith('Key')},
            'rotated_at': time.time(),
            'rotated_date': datetime.now().isoformat()
        }
        
        self.key_history.append(entry)
        
        # 限制历史记录数量
        if len(self.key_history) > KEY_CONFIG['key_history_limit']:
            self.key_history = self.key_history[-KEY_CONFIG['key_history_limit']:]
        
        # 保存到文件
        with open(self.key_history_file, "w", encoding='utf-8') as f:
            json.dump(self.key_history, f, indent=4, ensure_ascii=False)
    
    def _get_next_version(self) -> int:
        """获取下一个密钥版本号"""
        if 'version' in self.keys:
            return self.keys['version'] + 1
        return 1
    
    def _mask_key(self, key: str, visible_chars: int = 8) -> str:
        """
        掩码密钥（只显示前几个字符）
        
        Args:
            key: 密钥字符串
            visible_chars: 显示的字符数
        
        Returns:
            掩码后的密钥
        """
        if not key:
            return "***"
        if len(key) <= visible_chars:
            return "***"
        return key[:visible_chars] + "..." + key[-4:]
    
    def _log_rotation(self, new_keys: Dict[str, str], old_keys: Dict[str, str]) -> None:
        """记录密钥轮换日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'version': new_keys['version'],
            'rotated_keys': list(old_keys.keys()),
            'rotation_type': 'manual'
        }
        
        with open(self.key_rotation_log_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _check_rotation_needed(self) -> bool:
        """
        检查是否需要轮换密钥
        
        Returns:
            是否需要轮换
        """
        if not KEY_CONFIG['enable_auto_rotation']:
            return False
        
        if 'created_at' not in self.keys:
            return False
        
        # 检查密钥年龄
        key_age_days = (time.time() - self.keys['created_at']) / 86400
        
        if key_age_days >= KEY_CONFIG['rotation_interval_days']:
            logger.info(f"密钥已使用 {key_age_days:.1f} 天，建议轮换")
            return True
        
        return False
    
    def get_key(self, name: str, validate: bool = True) -> str:
        """
        获取密钥
        
        Args:
            name: 密钥名称 (KeyA, KeyB, KeyC)
            validate: 是否验证密钥
        
        Returns:
            密钥字符串，如果不存在返回空字符串
        """
        key_value = self.keys.get(name, "")
        
        if validate and key_value:
            try:
                # 验证密钥格式
                Fernet(key_value.encode())
            except Exception as e:
                logger.error(f"密钥 {name} 验证失败: {e}")
                return ""
        
        return key_value
    
    def rotate_keys(self, force: bool = False) -> Dict[str, str]:
        """
        轮换所有密钥
        
        Args:
            force: 是否强制轮换（忽略最小存活时间）
        
        Returns:
            新生成的密钥字典
        """
        logger.info("🔄 开始轮换 A/B/C 密钥...")
        
        new_keys = self._generate_new_keys(force=force)
        
        # 更新当前密钥
        self.keys = new_keys
        
        logger.info("✅ 密钥轮换完成")
        
        return new_keys
    
    def rotate_single_key(self, key_name: str, force: bool = False) -> str:
        """
        轮换单个密钥
        
        Args:
            key_name: 密钥名称 (KeyA, KeyB, KeyC)
            force: 是否强制轮换
        
        Returns:
            新的密钥值
        """
        if key_name not in ['KeyA', 'KeyB', 'KeyC']:
            raise ValueError(f"无效的密钥名称: {key_name}")
        
        logger.info(f"🔄 开始轮换密钥: {key_name}")
        
        # 保存旧密钥
        old_key = self.keys.get(key_name, "")
        
        # 生成新密钥
        new_key = Fernet.generate_key().decode()
        
        # 更新密钥字典
        self.keys[key_name] = new_key
        self.keys['rotated_at'] = time.time()
        
        # 保存到文件
        with open(self.key_file, "w", encoding='utf-8') as f:
            json.dump(self.keys, f, indent=4)
        
        logger.info(f"✅ 密钥 {key_name} 轮换完成")
        logger.info(f"   旧值: {self._mask_key(old_key)}")
        logger.info(f"   新值: {self._mask_key(new_key)}")
        
        return new_key
    
    def verify_key(self, name: str, key_value: str) -> bool:
        """
        验证密钥是否有效
        
        Args:
            name: 密钥名称
            key_value: 要验证的密钥值
        
        Returns:
            是否有效
        """
        # 检查当前密钥
        if self.keys.get(name) == key_value:
            return True
        
        # 检查历史密钥
        for entry in self.key_history:
            if 'original_keys' in entry and entry['original_keys'].get(name) == key_value:
                logger.warning(f"密钥 {name} 匹配历史记录 (版本 {entry.get('version', 'unknown')})")
                return True
        
        return False
    
    def get_key_info(self, name: str) -> Dict[str, any]:
        """
        获取密钥信息
        
        Args:
            name: 密钥名称
        
        Returns:
            密钥信息字典
        """
        if name not in ['KeyA', 'KeyB', 'KeyC']:
            raise ValueError(f"无效的密钥名称: {name}")
        
        info = {
            'name': name,
            'masked': self._mask_key(self.keys.get(name, "")),
            'purpose': KEY_PURPOSES.get(name, {}),
            'created_at': self.keys.get('created_at'),
            'rotated_at': self.keys.get('rotated_at'),
            'version': self.keys.get('version', 0)
        }
        
        # 计算密钥年龄
        if info['created_at']:
            age_seconds = time.time() - info['created_at']
            info['age_days'] = age_seconds / 86400
            info['age_hours'] = age_seconds / 3600
        
        # 检查是否需要轮换
        info['needs_rotation'] = self._check_rotation_needed()
        
        return info
    
    def get_all_keys_info(self) -> Dict[str, Dict[str, any]]:
        """获取所有密钥的信息"""
        return {
            'KeyA': self.get_key_info('KeyA'),
            'KeyB': self.get_key_info('KeyB'),
            'KeyC': self.get_key_info('KeyC')
        }
    
    def export_keys(self, include_full_keys: bool = False) -> Dict[str, any]:
        """
        导出密钥信息
        
        Args:
            include_full_keys: 是否包含完整密钥（谨慎使用）
        
        Returns:
            密钥信息字典
        """
        export_data = {
            'version': self.keys.get('version', 0),
            'created_at': self.keys.get('created_at'),
            'rotated_at': self.keys.get('rotated_at'),
            'exported_at': datetime.now().isoformat(),
            'keys': {}
        }
        
        for key_name in ['KeyA', 'KeyB', 'KeyC']:
            if include_full_keys:
                export_data['keys'][key_name] = self.keys.get(key_name)
            else:
                export_data['keys'][key_name] = {
                    'masked': self._mask_key(self.keys.get(key_name, "")),
                    'purpose': KEY_PURPOSES.get(key_name, {})
                }
        
        return export_data
    
    def check_key_strength(self, name: str) -> Dict[str, any]:
        """
        检查密钥强度
        
        Args:
            name: 密钥名称
        
        Returns:
            强度检查结果
        """
        key_value = self.keys.get(name, "")
        
        if not key_value:
            return {'valid': False, 'error': '密钥不存在'}
        
        result = {
            'valid': True,
            'name': name,
            'length': len(key_value),
            'format_correct': len(key_value) == 44,
            'strength_bits': KEY_CONFIG['key_strength_bits']
        }
        
        # Fernet 密钥是 256 位（32 字节）
        result['strength_level'] = 'high' if result['format_correct'] else 'invalid'
        
        return result


# 向后兼容的 ABCKeyManager 类
class ABCKeyManager(EnhancedABCKeyManager):
    """向后兼容的 ABCKeyManager 类"""
    
    def __init__(self, key_dir: Optional[Path] = None):
        super().__init__(key_dir)
        logger.info("使用增强的 ABCKeyManager（向后兼容模式）")