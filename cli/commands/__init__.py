#!/usr/bin/env python3
"""
Unified AI Project CLI 命令模块初始化文件
"""

from .dev import dev
from .test import test
from .git import git
from .editor import editor
from .rovo import rovo
from .security import security
from .integrate import integrate

__all__ = ['dev', 'test', 'git', 'editor', 'rovo', 'security', 'integrate']