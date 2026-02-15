#!/usr/bin/env python3
"""
Angela AI - Version Management
版本管理模块

提供统一的版本号管理和版本信息查询。
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
logger = logging.getLogger(__name__)


class ReleasePhase(Enum):
    """发布阶段"""
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"  # Release Candidate
    STABLE = "stable"


@dataclass
class VersionInfo:
    """版本信息"""
    major: int = 6
    minor: int = 2
    patch: int = 0
    phase: ReleasePhase = ReleasePhase.STABLE
    phase_number: int = 0
    build_metadata: str = ""
    
    def __str__(self) -> str:
        """版本字符串"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        
        if self.phase != ReleasePhase.STABLE:
            version += f"-{self.phase.value}"
            if self.phase_number > 0:
                version += f".{self.phase_number}"
        
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        
        return version
    
    def __repr__(self) -> str:
        return f"VersionInfo({self})"
    
    def to_tuple(self) -> tuple:
        """转换为元组"""
        return (self.major, self.minor, self.patch)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "phase": self.phase.value,
            "phase_number": self.phase_number,
            "build_metadata": self.build_metadata,
            "full_version": str(self),
        }
    
    def increment_major(self) -> "VersionInfo":
        """增加主版本号"""
        return VersionInfo(
            major=self.major + 1,
            minor=0,
            patch=0,
            phase=self.phase,
            phase_number=0,
        )
    
    def increment_minor(self) -> "VersionInfo":
        """增加次版本号"""
        return VersionInfo(
            major=self.major,
            minor=self.minor + 1,
            patch=0,
            phase=self.phase,
            phase_number=0,
        )
    
    def increment_patch(self) -> "VersionInfo":
        """增加补丁版本号"""
        return VersionInfo(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
            phase=self.phase,
            phase_number=0,
        )
    
    def set_phase(self, phase: ReleasePhase, phase_number: int = 0) -> "VersionInfo":
        """设置发布阶段"""
        return VersionInfo(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            phase=phase,
            phase_number=phase_number,
        )


# 当前版本信息
CURRENT_VERSION = VersionInfo(
    major=6,
    minor=2,
    patch=0,
    phase=ReleasePhase.STABLE,
)

# 版本常量
__version__ = str(CURRENT_VERSION)
__version_info__ = CURRENT_VERSION.to_tuple()
__version_dict__ = CURRENT_VERSION.to_dict()


def get_version() -> str:
    """获取版本字符串"""
    return __version__


def get_version_info() -> VersionInfo:
    """获取版本信息对象"""
    return CURRENT_VERSION


def get_version_tuple() -> tuple:
    """获取版本元组"""
    return __version_info__


def get_version_dict() -> dict:
    """获取版本字典"""
    return __version_dict__


def read_version_file(version_file: Optional[Path] = None) -> str:
    """从 VERSION 文件读取版本号"""
    if version_file is None:
        version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
    
    if version_file.exists():
        with open(version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
            return version
    else:
        return __version__


def parse_version(version_str: str) -> VersionInfo:
    """解析版本字符串"""
    # 移除 build metadata
    version_str = version_str.split('+')[0]
    
    # 解析主版本、次版本、补丁版本
    main_part = version_str.split('-')[0]
    parts = main_part.split('.')
    
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    
    # 解析发布阶段
    phase = ReleasePhase.STABLE
    phase_number = 0
    
    if '-' in version_str:
        phase_part = version_str.split('-')[1]
        phase_parts = phase_part.split('.')
        
        try:
            phase = ReleasePhase(phase_parts[0])
        except ValueError:
            phase = ReleasePhase.STABLE
        
        if len(phase_parts) > 1:
            try:
                phase_number = int(phase_parts[1])
            except ValueError:
                phase_number = 0
    
    return VersionInfo(
        major=major,
        minor=minor,
        patch=patch,
        phase=phase,
        phase_number=phase_number,
    )


def compare_versions(v1: str, v2: str) -> int:
    """比较两个版本号
    
    Args:
        v1: 第一个版本字符串
        v2: 第二个版本字符串
        
    Returns:
        int: -1 如果 v1 < v2, 0 如果 v1 == v2, 1 如果 v1 > v2
    """
    version1 = parse_version(v1)
    version2 = parse_version(v2)
    
    if version1.major != version2.major:
        return -1 if version1.major < version2.major else 1
    
    if version1.minor != version2.minor:
        return -1 if version1.minor < version2.minor else 1
    
    if version1.patch != version2.patch:
        return -1 if version1.patch < version2.patch else 1
    
    # 比较发布阶段
    phase_order = {
        ReleasePhase.ALPHA: 0,
        ReleasePhase.BETA: 1,
        ReleasePhase.RC: 2,
        ReleasePhase.STABLE: 3,
    }
    
    if phase_order[version1.phase] != phase_order[version2.phase]:
        return -1 if phase_order[version1.phase] < phase_order[version2.phase] else 1
    
    if version1.phase_number != version2.phase_number:
        return -1 if version1.phase_number < version2.phase_number else 1
    
    return 0


def is_compatible(required_version: str, current_version: str = None) -> bool:
    """检查版本兼容性
    
    Args:
        required_version: 要求的最低版本
        current_version: 当前版本，默认为项目版本
        
    Returns:
        bool: 如果兼容则为 True
    """
    if current_version is None:
        current_version = __version__
    
    return compare_versions(current_version, required_version) >= 0


def get_changelog_url() -> str:
    """获取变更日志 URL"""
    return f"https://github.com/catcatAI/Unified-AI-Project/blob/main/CHANGELOG.md"


def get_release_notes_url(version: Optional[str] = None) -> str:
    """获取发布说明 URL"""
    version = version or __version__
    return f"https://github.com/catcatAI/Unified-AI-Project/releases/tag/v{version}"


# 模块导出
__all__ = [
    "get_version",
    "get_version_info",
    "get_version_tuple",
    "get_version_dict",
    "read_version_file",
    "parse_version",
    "compare_versions",
    "is_compatible",
    "get_changelog_url",
    "get_release_notes_url",
    "VersionInfo",
    "ReleasePhase",
    "CURRENT_VERSION",
    "__version__",
    "__version_info__",
    "__version_dict__",
]


if __name__ == "__main__":
    # 测试版本管理模块
    logger.info(f"Angela AI Version: {get_version()}")
    logger.info(f"Version Info: {get_version_info()}")
    logger.info(f"Version Tuple: {get_version_tuple()}")
    logger.info(f"Version Dict: {get_version_dict()}")
    logger.info(f"Changelog URL: {get_changelog_url()}")
    logger.info(f"Release Notes URL: {get_release_notes_url()}")
    
    # 测试版本比较
    logger.info(f"\nComparing 6.2.0 and 6.1.0: {compare_versions('6.2.0', '6.1.0')}")
    logger.info(f"Comparing 6.1.0 and 6.2.0: {compare_versions('6.1.0', '6.2.0')}")
    logger.info(f"Comparing 6.2.0 and 6.2.0: {compare_versions('6.2.0', '6.2.0')}")
    
    # 测试版本兼容性
    logger.info(f"\nCompatible with 6.1.0: {is_compatible('6.1.0')}")
    logger.info(f"Compatible with 6.3.0: {is_compatible('6.3.0')}")
    
    # 测试版本递增
    logger.info(f"\nNext major: {CURRENT_VERSION.increment_major()}")
    logger.info(f"Next minor: {CURRENT_VERSION.increment_minor()}")
    logger.info(f"Next patch: {CURRENT_VERSION.increment_patch()}")