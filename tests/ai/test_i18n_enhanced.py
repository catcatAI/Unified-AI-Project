"""Test Phase 7 P0: I18nManager enhancement."""
import json
import os
import tempfile

import pytest

from apps.backend.src.core.i18n.i18n_manager import I18nConfig, I18nManager, Language


class TestI18nManagerEnhanced:
    def test_load_from_json(self):
        """load_from_json loads translations from a JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "common": {"hello": "Hello", "world": "World"},
                    "errors": {"not_found": "Not found"},
                },
                f,
            )
            tmp = f.name

        try:
            mgr = I18nManager()
            count = mgr.load_from_json(tmp, Language.ENGLISH)
            assert count == 3
            assert mgr.translate("common.hello") == "Hello"
            assert mgr.translate("errors.not_found") == "Not found"
        finally:
            os.unlink(tmp)

    def test_load_from_json_missing_file(self):
        mgr = I18nManager()
        count = mgr.load_from_json("/nonexistent/file.json", Language.ENGLISH)
        assert count == 0

    def test_load_from_locale_dir(self):
        """load_from_locale_dir loads all locale files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_path = os.path.join(tmpdir, "en-US.json")
            zh_path = os.path.join(tmpdir, "zh-CN.json")
            with open(en_path, "w", encoding="utf-8") as f:
                json.dump({"greeting": {"hello": "Hello"}}, f)
            with open(zh_path, "w", encoding="utf-8") as f:
                json.dump({"greeting": {"hello": "你好"}}, f)

            mgr = I18nManager()
            count = mgr.load_from_locale_dir(tmpdir)
            assert count == 2
            # Default language is Chinese (§X #56); assert per-language loads.
            assert mgr.translate("greeting.hello", Language.ENGLISH) == "Hello"
            assert mgr.translate("greeting.hello", Language.CHINESE) == "你好"

    def test_load_from_locale_dir_missing(self):
        mgr = I18nManager()
        count = mgr.load_from_locale_dir("/nonexistent/dir")
        assert count == 0

    def test_encode_decode_roundtrip(self):
        """encode then decode returns original text."""
        mgr = I18nManager()
        mgr.add_translation("greeting.hello", "Hello", Language.ENGLISH)
        mgr.add_translation("greeting.hello", "你好", Language.CHINESE)

        keys = mgr.encode("Hello")
        assert "greeting.hello" in keys
        result = mgr.decode(keys, Language.ENGLISH)
        assert result == "Hello"

    def test_encode_chinese(self):
        mgr = I18nManager()
        mgr.add_translation("greeting.hello", "Hello", Language.ENGLISH)
        mgr.add_translation("greeting.hello", "你好", Language.CHINESE)

        keys = mgr.encode("你好")
        assert "greeting.hello" in keys

    def test_decode_preferred_language(self):
        mgr = I18nManager()
        mgr.add_translation("key", "Hello", Language.ENGLISH)
        mgr.add_translation("key", "你好", Language.CHINESE)

        result = mgr.decode(["key"], Language.CHINESE)
        assert result == "你好"

    def test_load_real_locale_files(self):
        """Load the actual locale files shipped with the project."""
        locale_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "apps", "backend", "src", "core", "i18n", "locales"
        )
        if not os.path.isdir(locale_dir):
            pytest.skip("Locale directory not found")

        mgr = I18nManager()
        count = mgr.load_from_locale_dir(locale_dir)
        assert count > 0
        assert mgr.translate("common.app_name") == "Angela AI"
