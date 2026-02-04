"""
Angela AI v6.0 - Internationalization Module
国际化模块

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from .i18n_manager import (
    I18nManager,
    I18nConfig,
    I18nContext,
    TranslationEntry,
    TranslationCache,
    Language,
    Locale,
    t,
    set_language,
    get_language,
    add_translation,
    create_i18n_manager,
)

__version__ = "6.0.0"
__author__ = "Angela AI Development Team"

__all__ = [
    "I18nManager",
    "I18nConfig",
    "I18nContext",
    "TranslationEntry",
    "TranslationCache",
    "Language",
    "Locale",
    "t",
    "set_language",
    "get_language",
    "add_translation",
    "create_i18n_manager",
]
