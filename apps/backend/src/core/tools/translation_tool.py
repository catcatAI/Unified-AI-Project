"""
翻译工具 - 基于字典的翻译
"""

import json
import os
import re
from datetime import datetime
from typing import Optional
import logging
logger = logging.getLogger(__name__)

# 定义路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DICTIONARY_PATH = os.path.join(PROJECT_ROOT, "src/tools/translation_model/data/translation_dictionary.json")

_translation_dictionary = None


def _load_dictionary():
    """加载翻译字典"""
    global _translation_dictionary

    if _translation_dictionary is None:
        logger.info("加载翻译字典...")

        try:
            with open(DICTIONARY_PATH, 'r', encoding='utf-8') as f:
                _translation_dictionary = json.load(f)
                logger.info("翻译字典加载成功")
        except FileNotFoundError:
            logger.info(f"错误: 翻译字典未找到 {DICTIONARY_PATH}")
            _translation_dictionary = {"zh_to_en": {}, "en_to_zh": {}}
        except json.JSONDecodeError:
            logger.info(f"错误: 无法解码JSON {DICTIONARY_PATH}")
            _translation_dictionary = {"zh_to_en": {}, "en_to_zh": {}}
        except Exception as e:
            logger.info(f"加载字典时出错: {e}")
            _translation_dictionary = {"zh_to_en": {}, "en_to_zh": {}}

    return _translation_dictionary


def _detect_language(text: str) -> Optional[str]:
    """
    基本语言检测
    返回 'zh' 表示中文，'en' 表示英文
    """
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    if re.search(r'[A-Za-z]', text):
        return 'en'
    return None


def translate(text: str, target_language: str, source_language: Optional[str] = None, **kwargs) -> str:
    """
    使用字典方法翻译文本

    Args:
        text: 要翻译的文本
        target_language: 目标语言名称或代码
        source_language: 源语言名称或代码（可选）

    Returns:
        翻译后的文本
    """
    dictionary = _load_dictionary()

    text_to_translate = kwargs.get('text_to_translate', text)

    if source_language is None:
        source_language = _detect_language(text_to_translate)
        if source_language is None:
            return f"无法确定源语言 '{text_to_translate}'"

    # 标准化为小写
    norm_source_language = source_language.lower()
    norm_target_language = target_language.lower()

    # 映射常见语言名称到代码
    lang_code_map = {
        "english": "en", "chinese": "zh", "spanish": "es",
        "french": "fr", "german": "de", "japanese": "ja", "korean": "ko"
    }

    source_lang_code = lang_code_map.get(norm_source_language, norm_source_language)
    target_lang_code = lang_code_map.get(norm_target_language, norm_target_language)

    if source_lang_code == target_lang_code:
        return text

    translation_map_key = f"{source_lang_code}_to_{target_lang_code}"

    if translation_map_key in dictionary:
        translation = dictionary[translation_map_key].get(text_to_translate)

        if translation:
            return translation
        else:
            # 尝试不区分大小写匹配
            if source_lang_code == 'en':
                for k, v in dictionary[translation_map_key].items():
                    if k.lower() == text_to_translate.lower():
                        return v

            return f"没有 '{text_to_translate}' 从 {source_lang_code} 到 {target_lang_code} 的翻译"
    else:
        return f"不支持从 {source_lang_code} 到 {target_lang_code} 的翻译"


def request_model_upgrade(details: str):
    """请求模型升级（概念性钩子）"""
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] MODEL_UPGRADE_REQUEST: {details}")


if __name__ == '__main__':
    logger.info("--- Translation Tool Example Usage ---")

    # 确保字典已加载
    _load_dictionary()

    if not _translation_dictionary or not _translation_dictionary.get("zh_to_en"):
        logger.info("字典似乎为空或未正确加载")

    tests = [
        ("你好", "en", "Hello"),
        ("Hello", "zh", "你好"),
    ]

    for input_text, target_lang, expected in tests:
        result = translate(input_text, target_lang)
        logger.info(f"{input_text} -> {target_lang}: {result}")