"""
统一自动修复系统 (Unified Auto-Fix System)
项目完美的自动修复集成框架

 功能范围：



- 语法错误修复
- 导入路径修复  
- 依赖关系修复
- Git问题修复
- 环境配置修复
- 代码风格修复
- 安全漏洞修复

调用方式：
- AI/AGI代理调用
- 独立命令行使用
- 项目集成调用
- 实时监控修复
"""
# 
# __version__ = "2.0.0"
__author__ = "Unified AI Project"

from .core.unified_fix_engine import UnifiedFixEngine
from .core.fix_types import FixType, FixStatus, FixScope
from .core.fix_result import FixResult, FixReport
from .interfaces.ai_interface import AIFixInterface
from .interfaces.cli_interface import CLIFixInterface
from .interfaces.api_interface import APIFixInterface
# 
# 
__all__ = [
    "UnifiedFixEngine",
    "FixType", 
    "FixStatus",
    "FixScope",
    "FixResult",
    "FixReport", 
    "AIFixInterface",
    "CLIFixInterface",
    "APIFixInterface"


]