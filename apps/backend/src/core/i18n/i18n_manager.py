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
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import json
import re
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言 / Supported Languages"""

    ZH_CN = "zh-CN"
    ZH_TW = "zh-TW"
    EN_US = "en-US"
    EN_GB = "en-GB"
    JA_JP = "ja-JP"
    KO_KR = "ko-KR"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"
    ES_ES = "es-ES"
    PT_BR = "pt-BR"


class Locale(Enum):
    """区域设置 / Locale configurations"""

    CHINA = ("zh-CN", "Asia/Shanghai", "CNY")
    TAIWAN = ("zh-TW", "Asia/Taipei", "TWD")
    UNITED_STATES = ("en-US", "America/New_York", "USD")
    UNITED_KINGDOM = ("en-GB", "Europe/London", "GBP")
    JAPAN = ("ja-JP", "Asia/Tokyo", "JPY")
    KOREA = ("ko-KR", "Asia/Seoul", "KRW")
    FRANCE = ("fr-FR", "Europe/Paris", "EUR")
    GERMANY = ("de-DE", "Europe/Berlin", "EUR")
    SPAIN = ("es-ES", "Europe/Madrid", "EUR")
    BRAZIL = ("pt-BR", "America/Sao_Paulo", "BRL")


@dataclass
class TranslationEntry:
    """翻译条目 / Translation entry"""

    key: str
    translations: Dict[str, str]
    context: str = ""
    plural_form: Optional[str] = None

    def translate(self, lang: str, count: int = 1) -> str:
        """翻译文本 / Translate text"""
        if lang in self.translations:
            text = self.translations[lang]
            if self.plural_form and count != 1:
                if f"{lang}_plural" in self.translations:
                    return self.translations[f"{lang}_plural"]
            return text
        return self.translations.get("en-US", self.key)


@dataclass
class I18nConfig:
    """i18n配置 / i18n configuration"""

    default_language: str = "zh-CN"
    fallback_language: str = "en-US"
    supported_languages: List[str] = field(
        default_factory=lambda: ["zh-CN", "zh-TW", "en-US", "en-GB", "ja-JP", "ko-KR"]
    )
    enable_autodetect: bool = True
    cache_translations: bool = True


class TranslationCache:
    """翻译缓存 / Translation cache"""

    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Dict[str, str]] = {}
        self._max_size = max_size

    def get(self, lang: str, key: str) -> Optional[str]:
        """获取缓存翻译 / Get cached translation"""
        if lang in self._cache:
            return self._cache[lang].get(key)
        return None

    def set(self, lang: str, key: str, value: str):
        """设置缓存翻译 / Set cached translation"""
        if lang not in self._cache:
            self._cache[lang] = {}

        if len(self._cache[lang]) < self._max_size:
            self._cache[lang][key] = value

    def clear(self, lang: str = None):
        """清除缓存 / Clear cache"""
        if lang:
            self._cache.pop(lang, None)
        else:
            self._cache.clear()


class I18nManager:
    """
    i18n管理器 / i18n Manager

    Manages translations and locale settings.
    管理翻译和区域设置。

    Attributes:
        config: i18n配置 / i18n config
        translations: 翻译字典 / Translation dictionary
        cache: 翻译缓存 / Translation cache
    """

    def __init__(self, config: I18nConfig = None):
        self.config = config or I18nConfig()
        self.translations: Dict[str, Dict[str, TranslationEntry]] = {}
        self.cache = TranslationCache()
        self._current_language = self.config.default_language

        self._load_default_translations()

    def _load_default_translations(self):
        """加载默认翻译 / Load default translations"""
        self._register_translations(
            "greeting",
            {
                "zh-CN": "你好！我是Angela，很高兴见到你！",
                "zh-TW": "你好！我是Angela，很高興見到你！",
                "en-US": "Hello! I'm Angela, nice to meet you!",
                "ja-JP": "こんにちは！私はAngelaです。 만나게 되어 기쁩니다!",
                "ko-KR": "안녕하세요! 저는 Angela입니다. 처음 뵙겠습니다!",
            },
        )

        self._register_translations(
            "farewell",
            {
                "zh-CN": "再见！期待下次见面！",
                "zh-TW": "再見！期待下次見面！",
                "en-US": "Goodbye! Looking forward to seeing you again!",
                "ja-JP": "さようなら！またお会いできるのを楽しみにしています！",
                "ko-KR": "안녕히 가세요! 다음에 또 만나요!",
            },
        )

        self._register_translations(
            "thinking",
            {
                "zh-CN": "让我想想...",
                "zh-TW": "讓我想想...",
                "en-US": "Let me think...",
                "ja-JP": "考えさせてください...",
                "ko-KR": "잠시만요, 생각해보겠습니다...",
            },
        )

        self._register_translations(
            "help_request",
            {
                "zh-CN": "我能帮你做什么吗？",
                "zh-TW": "我能幫你做什麼嗎？",
                "en-US": "How can I help you?",
                "ja-JP": "何かお手伝いできることはありますか？",
                "ko-KR": "뭐 도와드릴까요?",
            },
        )

        self._register_translations(
            "error_occurred",
            {
                "zh-CN": "出错了，请稍后再试。",
                "zh-TW": "出錯了，請稍後再試。",
                "en-US": "An error occurred. Please try again later.",
                "ja-JP": "エラーが発生しました。 後ほど再試行してください。",
                "ko-KR": "오류가 발생했습니다. 나중에 다시 시도해 주세요.",
            },
        )

    def _register_translations(self, category: str, translations: Dict[str, str]):
        """注册翻译 / Register translations"""
        if category not in self.translations:
            self.translations[category] = {}

        for lang, text in translations.items():
            key = f"{category}_{hash(text) % 10000}"
            entry = TranslationEntry(key=key, translations={lang: text})
            self.translations[category][key] = entry

    def set_language(self, language: str):
        """设置当前语言 / Set current language"""
        if language in self.config.supported_languages:
            self._current_language = language
        else:
            self._current_language = self.config.default_language

    def get_language(self) -> str:
        """获取当前语言 / Get current language"""
        return self._current_language

    def t(self, key: str, language: str = None, **kwargs) -> str:
        """
        翻译文本 / Translate text

        Args:
            key: 翻译键名 / Translation key
            language: 目标语言 / Target language
            **kwargs: 格式化参数 / Formatting parameters

        Returns:
            翻译后的文本 / Translated text
        """
        lang = language or self._current_language

        if lang not in self.config.supported_languages:
            lang = self.config.fallback_language

        cached = self.cache.get(lang, key)
        if cached:
            return self._format_text(cached, **kwargs)

        text = self._lookup_translation(key, lang)
        if text:
            self.cache.set(lang, key, text)
            return self._format_text(text, **kwargs)

        return self._format_text(key, **kwargs)

    def _lookup_translation(self, key: str, lang: str) -> str:
        """查找翻译 / Lookup translation"""
        for category in self.translations.values():
            if key in category:
                return category[key].translate(lang)

        if "_" in key:
            parts = key.split("_", 1)
            fallback_key = parts[1] if len(parts) > 1 else parts[0]
            for cat in self.translations.values():
                for k, entry in cat.items():
                    if fallback_key in k.lower():
                        return entry.translate(lang)

        return None

    def _format_text(self, text: str, **kwargs) -> str:
        """格式化文本 / Format text"""
        try:
            return text.format(**kwargs) if kwargs else text
        except KeyError:
            return text

    def add_translation(self, key: str, language: str, translation: str, category: str = "general"):
        """添加翻译 / Add translation"""
        if category not in self.translations:
            self.translations[category] = {}

        if key not in self.translations[category]:
            self.translations[category][key] = TranslationEntry(key=key, translations={})

        self.translations[category][key].translations[language] = translation
        self.cache.clear(language)

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """获取支持的语言列表 / Get supported languages list"""
        return [
            {"code": lang, "name": Language(lang).name.replace("_", " ")}
            for lang in self.config.supported_languages
            if lang in [l.value for l in Language]
        ]

    def detect_language(self, text: str) -> str:
        """检测语言 / Detect language"""
        if not self.config.enable_autodetect:
            return self._current_language

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        japanese_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", text))
        korean_chars = len(re.findall(r"[\uac00-\ud7af]", text))

        total = chinese_chars + japanese_chars + korean_chars
        if total == 0:
            return "en-US"

        if chinese_chars / total > 0.5:
            return "zh-CN"
        elif japanese_chars / total > 0.5:
            return "ja-JP"
        elif korean_chars / total > 0.5:
            return "ko-KR"
        else:
            return "en-US"

    def export_translations(self, language: str) -> Dict[str, str]:
        """导出翻译 / Export translations"""
        result = {}
        for category in self.translations.values():
            for key, entry in category.items():
                if language in entry.translations:
                    result[key] = entry.translations[language]
        return result

    def import_translations(
        self, translations: Dict[str, str], language: str, overwrite: bool = False
    ):
        """导入翻译 / Import translations"""
        for key, text in translations.items():
            if overwrite or not self._lookup_translation(key, language):
                self.add_translation(key, language, text)

    def get_locale_info(self, locale: str) -> Dict[str, Any]:
        """获取区域信息 / Get locale info"""
        for l in Locale:
            if l.value[0] == locale:
                return {"language": l.value[0], "timezone": l.value[1], "currency": l.value[2]}
        return {"language": locale, "timezone": "UTC", "currency": "USD"}


class I18nContext:
    """i18n上下文 / i18n context"""

    def __init__(self, manager: I18nManager = None):
        self.manager = manager or I18nManager()
        self._language_stack: List[str] = []

    def use_language(self, language: str) -> Callable:
        """使用语言上下文 / Use language context"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                old_lang = self.manager.get_language()
                self.manager.set_language(language)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.manager.set_language(old_lang)

            return wrapper

        return decorator

    def translate(self, key: str, **kwargs) -> str:
        """翻译 / Translate"""
        return self.manager.t(key, **kwargs)


# 便捷函数
_i18n_manager: Optional[I18nManager] = None


def _get_manager() -> I18nManager:
    """获取i18n管理器 / Get i18n manager"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def t(key: str, language: str = None, **kwargs) -> str:
    """便捷翻译函数 / Convenience translation function"""
    return _get_manager().t(key, language, **kwargs)


def set_language(language: str):
    """设置语言 / Set language"""
    _get_manager().set_language(language)


def get_language() -> str:
    """获取语言 / Get language"""
    return _get_manager().get_language()


def add_translation(key: str, language: str, translation: str):
    """添加翻译 / Add translation"""
    _get_manager().add_translation(key, language, translation)


def create_i18n_manager(config: I18nConfig = None) -> I18nManager:
    """创建i18n管理器 / Create i18n manager"""
    return I18nManager(config)


def demo():
    """演示 / Demo"""
    logger.info("🌐 i18n 多语言支持系统演示")
    logger.info("=" * 50)

    manager = I18nManager()

    logger.info("\n📋 支持的语言:")
    for lang in manager.get_supported_languages():
        logger.info(f"  {lang['code']}: {lang['name']}")

    logger.info("\n🔤 翻译测试:")
    for lang in ["zh-CN", "zh-TW", "en-US", "ja-JP", "ko-KR"]:
        manager.set_language(lang)
        logger.info(f"\n[{lang}]")
        logger.info(f"  问候: {manager.t('greeting')}")
        logger.info(f"  再见: {manager.t('farewell')}")
        logger.info(f"  思考: {manager.t('thinking')}")
        logger.info(f"  帮助: {manager.t('help_request')}")

    logger.info("\n🌍 语言检测:")
    test_texts = [
        ("你好", "zh-CN"),
        ("Hello", "en-US"),
        ("こんにちは", "ja-JP"),
        ("안녕하세요", "ko-KR"),
    ]
    for text, expected in test_texts:
        detected = manager.detect_language(text)
        status = "✅" if detected == expected else "❌"
        logger.info(f"  {status} '{text}' -> {detected} (期望: {expected})")

    logger.info("\n💾 区域信息:")
    info = manager.get_locale_info("zh-CN")
    logger.info(f"  中文(中国): {info}")

    logger.info("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
