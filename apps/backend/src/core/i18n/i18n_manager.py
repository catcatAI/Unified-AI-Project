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

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

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

    def load_from_json(self, filepath: str, language: Language) -> int:
        """Load translations from a locale JSON file."""
        import json
        import os

        if not os.path.exists(filepath):
            logger.warning(f"Locale file not found: {filepath}")
            return 0

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0

        def flatten(obj, prefix=""):
            nonlocal count
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    flatten(v, full_key)
                else:
                    self.add_translation(full_key, str(v), language)
                    count += 1

        # Skip metadata keys
        skip = {"language", "language_code", "direction", "date_format", "time_format"}
        for key, value in data.items():
            if key not in skip:
                flatten(value, key)

        logger.info(f"Loaded {count} translations from {filepath} for {language.value}")
        return count

    def load_from_locale_dir(self, locale_dir: str) -> int:
        """Load all locale JSON files from a directory."""
        import os

        if not os.path.isdir(locale_dir):
            logger.warning(f"Locale directory not found: {locale_dir}")
            return 0

        lang_map = {
            "en-US": Language.ENGLISH,
            "zh-CN": Language.CHINESE,
            "ja-JP": Language.JAPANESE,
            "ko-KR": Language.KOREAN,
            "fr-FR": Language.FRENCH,
            "de-DE": Language.GERMAN,
            "es-ES": Language.SPANISH,
            "pt-BR": Language.PORTUGUESE,
            "ru-RU": Language.RUSSIAN,
            "ar-SA": Language.ARABIC,
        }

        total = 0
        for fname in os.listdir(locale_dir):
            if not fname.endswith(".json"):
                continue
            code = fname.replace(".json", "")
            if code in lang_map:
                filepath = os.path.join(locale_dir, fname)
                count = self.load_from_json(filepath, lang_map[code])
                total += count

        logger.info(f"Loaded {total} total translations from {locale_dir}")
        return total

    def encode(self, text: str) -> List[str]:
        """Find translation keys matching input text (any language)."""
        text_lower = text.lower().strip()
        matched = []
        for key, entry in self._translations.items():
            for lang_text in entry.translations.values():
                if lang_text.lower().strip() == text_lower:
                    matched.append(key)
                    break
        return matched

    def decode(self, keys: List[str], language: Optional[Language] = None) -> str:
        """Reconstruct localized string from keys, preferring current language."""
        lang = language or self._current_language
        parts = []
        for key in keys:
            entry = self._translations.get(key)
            if entry:
                text = entry.translations.get(lang.value) or entry.translations.get(
                    self.config.fallback_language.value, key
                )
                parts.append(text)
        return " ".join(parts)


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
