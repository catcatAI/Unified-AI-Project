"""
Angela AI 7.5.0-dev - Internationalization Module
国际化模块

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

import logging

logger = logging.getLogger(__name__)

from .i18n_manager import (  # noqa: E402
    I18nConfig,
    I18nContext,
    I18nManager,
    Language,
    Locale,
    TranslationCache,
    TranslationEntry,
    add_translation,
    get_language,
    set_language,
    t,
)

__version__ = "7.5.0-dev"
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
]
