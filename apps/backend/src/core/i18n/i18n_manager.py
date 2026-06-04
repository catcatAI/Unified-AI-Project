"""
Angela AI v6.0 - Internationalization (i18n) System
多语言支持系统

Provides internationalization and localization support for Angela AI.
为Angela AI提供国际化和本地化支持。

Features:
- Multi-language text translations
- Locale-aware formatting
- Fallback language support
- Language detection

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"


class Locale(Enum):
    US = "en-US"
    CN = "zh-CN"
    JP = "ja-JP"
    KR = "ko-KR"
    FR = "fr-FR"
    DE = "de-DE"
    ES = "es-ES"
    PT = "pt-BR"
    RU = "ru-RU"
    AR = "ar-SA"


@dataclass
class TranslationEntry:
    key: str
    translations: Dict[str, str] = field(default_factory=dict)
    context: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class I18nConfig:
    default_language: Language = Language.ENGLISH
    default_locale: Locale = Locale.US
    fallback_language: Language = Language.ENGLISH
    enable_cache: bool = True
    cache_size: int = 1000


@dataclass
class I18nContext:
    language: Language
    locale: Locale
    translations: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TranslationCache:
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, str] = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        if len(self._cache) >= self._max_size:
            self._cache.clear()
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()


class I18nManager:
    def __init__(self, config: Optional[I18nConfig] = None):
        self.config = config or I18nConfig()
        self._translations: Dict[str, TranslationEntry] = {}
        self._current_language = self.config.default_language
        self._current_locale = self.config.default_locale
        self._cache = TranslationCache(self.config.cache_size) if self.config.enable_cache else None
        logger.debug(f"I18nManager initialized with {self._current_language.value}")

    def set_language(self, language: Language) -> None:
        self._current_language = language
        logger.debug(f"Language set to {language.value}")

    def get_language(self) -> Language:
        return self._current_language

    def add_translation(self, key: str, translation: str, language: Language) -> None:
        if key not in self._translations:
            self._translations[key] = TranslationEntry(key=key)
        self._translations[key].translations[language.value] = translation
        if self._cache:
            self._cache.set(f"{key}:{language.value}", translation)

    def translate(self, key: str, language: Optional[Language] = None) -> str:
        lang = language or self._current_language
        cache_key = f"{key}:{lang.value}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return cached
        entry = self._translations.get(key)
        if entry and lang.value in entry.translations:
            result = entry.translations[lang.value]
            if self._cache:
                self._cache.set(cache_key, result)
            return result
        if lang != self.config.fallback_language:
            return self.translate(key, self.config.fallback_language)
        return key

    def get_context(self) -> I18nContext:
        return I18nContext(
            language=self._current_language,
            locale=self._current_locale,
        )


_default_manager = I18nManager()


def t(key: str, **kwargs) -> str:
    result = _default_manager.translate(key)
    if kwargs:
        result = result.format(**kwargs)
    return result


def set_language(language: Language) -> None:
    _default_manager.set_language(language)


def get_language() -> Language:
    return _default_manager.get_language()


def add_translation(key: str, translation: str, language: Language) -> None:
    _default_manager.add_translation(key, translation, language)
