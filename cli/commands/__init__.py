#!/usr/bin/env python3
"""
Unified AI Project CLI 命令模块初始化文件
"""

from .dev import dev
from .test import test
from .git import git

__all__ = ['dev', 'test', 'git']