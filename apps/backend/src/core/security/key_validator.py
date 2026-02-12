# =============================================================================
# ANGELA-MATRIX: 密鑰驗證模塊
# =============================================================================
#
# 職責: 驗證系統密鑰的安全性和有效性
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級
#
# 安全特性:
# - 檢測默認或硬編碼的密鑰
# - 驗證密鑰長度要求
# - 防止弱密鑰使用
# - 提供密鑰生成建議
#
# =============================================================================

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KeyValidationResult:
    """密鑰驗證結果"""
    key_name: str
    is_valid: bool
    issues: List[str]
    severity: str  # 'critical', 'high', 'medium', 'low'


class KeyValidator:
    """密鑰驗證器"""

    # 已知的弱密鑰和佔位符模式
    WEAK_PATTERNS = [
        r'your_key_[abc]_minimum_32_chars',  # 舊的佔位符
        r'PLACEHOLDER_REPLACE_WITH_SECURE_KEY_[ABC]',  # 新的佔位符
        r'YOUR_API_KEY',  # API 密鑰佔位符
        r'changeme',  # 常見的測試密鑰
        r'test123',  # 測試密鑰
        r'password',  # 弱密鑰
        r'secret',  # 弱密鑰
        r'admin',  # 弱密鑰
        r'key123',  # 弱密鑰
    ]

    # 密鑰最小長度要求
    MIN_KEY_LENGTHS = {
        'ANGELA_KEY_A': 32,
        'ANGELA_KEY_B': 32,
        'ANGELA_KEY_C': 32,
        'OPENAI_API_KEY': 20,
        'GOOGLE_API_KEY': 20,
        'ANTHROPIC_API_KEY': 20,
    }

    def __init__(self):
        self.results: List[KeyValidationResult] = []

    def validate_key(self, key_name: str, key_value: str) -> KeyValidationResult:
        """
        驗證單個密鑰

        Args:
            key_name: 密鑰名稱
            key_value: 密鑰值

        Returns:
            KeyValidationResult: 驗證結果
        """
        issues = []
        severity = 'low'

        # 檢查密鑰是否為空
        if not key_value or key_value.strip() == '':
            issues.append(f"密鑰 {key_name} 為空或未設置")
            severity = 'critical'
            return KeyValidationResult(key_name, False, issues, severity)

        # 檢查密鑰長度
        min_length = self.MIN_KEY_LENGTHS.get(key_name, 32)
        if len(key_value) < min_length:
            issues.append(f"密鑰 {key_name} 長度不足 (當前: {len(key_value)}, 最小要求: {min_length})")
            severity = 'high' if severity != 'critical' else severity

        # 檢查是否為弱密鑰或佔位符
        for pattern in self.WEAK_PATTERNS:
            if re.search(pattern, key_value, re.IGNORECASE):
                issues.append(f"密鑰 {key_name} 使用了弱模式或佔位符: {pattern}")
                severity = 'critical'
                break

        # 檢查密鑰複雜度（僅檢查非 API 密鑰）
        if key_name.startswith('ANGELA_KEY_'):
            if not self._check_key_complexity(key_value):
                issues.append(f"密鑰 {key_name} 缺乏足夠的複雜度")
                severity = 'medium' if severity not in ['critical', 'high'] else severity

        # 判斷是否有效
        is_valid = len(issues) == 0

        return KeyValidationResult(key_name, is_valid, issues, severity)

    def _check_key_complexity(self, key_value: str) -> bool:
        """
        檢查密鑰複雜度

        Args:
            key_value: 密鑰值

        Returns:
            bool: 是否通過複雜度檢查
        """
        # 檢查是否包含字母和數字
        has_alpha = any(c.isalpha() for c in key_value)
        has_digit = any(c.isdigit() for c in key_value)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in key_value)

        # 至少需要字母和數字，或者包含特殊字符
        return (has_alpha and has_digit) or has_special

    def validate_all_keys(self, env_dict: Optional[Dict[str, str]] = None) -> List[KeyValidationResult]:
        """
        驗證所有關鍵密鑰

        Args:
            env_dict: 環境變量字典，如果為 None 則從 os.environ 讀取

        Returns:
            List[KeyValidationResult]: 所有密鑰的驗證結果
        """
        if env_dict is None:
            env_dict = os.environ

        self.results = []

        # 驗證 Angela 核心密鑰
        for key_name in ['ANGELA_KEY_A', 'ANGELA_KEY_B', 'ANGELA_KEY_C']:
            key_value = env_dict.get(key_name, '')
            result = self.validate_key(key_name, key_value)
            self.results.append(result)

        # 驗證 API 密鑰
        api_keys = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'ANTHROPIC_API_KEY']
        for key_name in api_keys:
            key_value = env_dict.get(key_name, '')
            # API 密鑰可能為空（如果不使用該服務），所以只檢查非空值的情況
            if key_value:
                result = self.validate_key(key_name, key_value)
                self.results.append(result)

        return self.results

    def get_critical_issues(self) -> List[KeyValidationResult]:
        """獲取所有嚴重問題"""
        return [r for r in self.results if r.severity == 'critical']

    def get_high_issues(self) -> List[KeyValidationResult]:
        """獲取所有高優先級問題"""
        return [r for r in self.results if r.severity == 'high']

    def get_validation_summary(self) -> Dict[str, any]:
        """
        獲取驗證摘要

        Returns:
            Dict: 驗證摘要
        """
        total = len(self.results)
        valid = sum(1 for r in self.results if r.is_valid)
        critical = len(self.get_critical_issues())
        high = len(self.get_high_issues())

        return {
            'total_keys': total,
            'valid_keys': valid,
            'invalid_keys': total - valid,
            'critical_issues': critical,
            'high_issues': high,
            'all_valid': critical == 0 and high == 0,
        }

    def print_report(self) -> None:
        """打印驗證報告"""
        print("\n" + "="*80)
        print("ANGELA 密鑰安全驗證報告")
        print("="*80 + "\n")

        summary = self.get_validation_summary()
        print(f"總計密鑰數: {summary['total_keys']}")
        print(f"有效密鑰數: {summary['valid_keys']}")
        print(f"無效密鑰數: {summary['invalid_keys']}")
        print(f"嚴重問題: {summary['critical_issues']}")
        print(f"高優先級問題: {summary['high_issues']}")
        print(f"整體狀態: {'✓ 通過' if summary['all_valid'] else '✗ 失敗'}")
        print()

        # 打印詳細結果
        for result in self.results:
            status_icon = "✓" if result.is_valid else "✗"
            severity_indicator = {
                'critical': '🔴 CRITICAL',
                'high': '🟠 HIGH',
                'medium': '🟡 MEDIUM',
                'low': '🟢 LOW'
            }.get(result.severity, '')

            print(f"{status_icon} {result.key_name}: {severity_indicator if not result.is_valid else 'OK'}")

            if not result.is_valid:
                for issue in result.issues:
                    print(f"  - {issue}")
            print()

        print("="*80)

        if not summary['all_valid']:
            print("\n⚠️  安全警告: 發現密鑰安全問題！")
            print("請採取以下措施:")
            print("1. 使用強隨機生成器創建新的密鑰")
            print("2. 確保密鑰長度符合要求")
            print("3. 不要使用佔位符或默認值")
            print("4. 運行: python -m src.core.security.key_generator 生成新密鑰")
            print()


# 全局實例
_key_validator: Optional[KeyValidator] = None


def get_key_validator() -> KeyValidator:
    """獲取全局密鑰驗證器實例"""
    global _key_validator
    if _key_validator is None:
        _key_validator = KeyValidator()
    return _key_validator


def validate_system_keys() -> Tuple[bool, List[KeyValidationResult]]:
    """
    驗證系統密鑰（便捷函數）

    Returns:
        Tuple[bool, List[KeyValidationResult]]: (是否通過, 驗證結果列表)
    """
    validator = get_key_validator()
    results = validator.validate_all_keys()
    summary = validator.get_validation_summary()
    return summary['all_valid'], results


if __name__ == "__main__":
    # 測試密鑰驗證器
    logging.basicConfig(level=logging.INFO)

    validator = get_key_validator()
    results = validator.validate_all_keys()
    validator.print_report()

    # 檢查是否通過
    summary = validator.get_validation_summary()
    if not summary['all_valid']:
        exit(1)
    else:
        print("\n✓ 所有密鑰驗證通過！")
        exit(0)
