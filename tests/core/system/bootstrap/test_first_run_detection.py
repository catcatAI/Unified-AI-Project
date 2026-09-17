"""First-run detection tests: usable-backend classification and warnings.

Covers the RELEASE_CRITERIA gap: main server previously started with no
detection/warning when no API key / no Ollama was configured.
"""

import sys
from pathlib import Path
from unittest.mock import patch

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.system.bootstrap.first_run_detection import (  # noqa: E402
    detect_first_run,
    log_first_run_warnings,
)


def _with_config(monkeypatch, mode, backends):
    fake = {"deployment": {"mode": mode}, "backends": backends}
    monkeypatch.setattr("core.system.bootstrap.first_run_detection.get_config", lambda path: fake)


class TestAlwaysAvailableLocal:
    def test_unified_backend_counts_usable(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local",
            {"unified-1g": {"type": "local", "provider": "unified", "enabled": True}},
        )
        result = detect_first_run()
        assert result["usable_backends"] == ["unified-1g"]
        assert result["ok"] is True
        assert result["warnings"] == []


class TestLocalHttp:
    def test_ollama_reachable(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local",
            {
                "ollama-llama3": {
                    "type": "local",
                    "provider": "ollama",
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                }
            },
        )
        with patch(
            "core.system.bootstrap.first_run_detection._probe_local_http",
            return_value=True,
        ):
            result = detect_first_run()
        assert result["usable_backends"] == ["ollama-llama3"]
        assert result["unreachable_local"] == []

    def test_ollama_unreachable_warns(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local",
            {
                "ollama-llama3": {
                    "type": "local",
                    "provider": "ollama",
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                }
            },
        )
        with patch(
            "core.system.bootstrap.first_run_detection._probe_local_http",
            return_value=False,
        ):
            result = detect_first_run()
        assert result["ok"] is False
        assert result["unreachable_local"] == ["ollama-llama3"]
        assert any("ollama-llama3" in w for w in result["warnings"])
        assert any("ollama serve" in w for w in result["warnings"])

    def test_disabled_backend_ignored(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local",
            {
                "llamacpp-local": {
                    "type": "local",
                    "provider": "llama_cpp",
                    "enabled": False,
                    "base_url": "http://localhost:8080",
                }
            },
        )
        result = detect_first_run()
        assert result["usable_backends"] == []
        assert result["unreachable_local"] == []


class TestCloud:
    def test_cloud_gated_by_local_mode(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local",
            {"openai-gpt4": {"type": "cloud", "provider": "openai", "enabled": True}},
        )
        result = detect_first_run()
        assert result["ok"] is False
        assert any("gates it" in b for b in result["blocked_cloud"])

    def test_cloud_missing_key_blocked(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local+llm",
            {"openai-gpt4": {"type": "cloud", "provider": "openai", "enabled": True}},
        )
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = detect_first_run()
        assert result["ok"] is False
        assert any("OPENAI_API_KEY" in b for b in result["blocked_cloud"])

    def test_cloud_with_key_usable(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local+llm",
            {"openai-gpt4": {"type": "cloud", "provider": "openai", "enabled": True}},
        )
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        result = detect_first_run()
        assert result["ok"] is True
        assert result["usable_backends"] == ["openai-gpt4"]

    def test_gemini_uses_gemini_api_key(self, monkeypatch):
        _with_config(
            monkeypatch,
            "llm",
            {"google-gemini": {"type": "cloud", "provider": "google", "enabled": True}},
        )
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "ignore-me")
        result = detect_first_run()
        assert result["ok"] is False
        assert any("GEMINI_API_KEY" in b for b in result["blocked_cloud"])


class TestMixed:
    def test_unified_available_means_ok_despite_others_down(self, monkeypatch):
        _with_config(
            monkeypatch,
            "local",
            {
                "unified-1g": {"type": "local", "provider": "unified", "enabled": True},
                "ollama-llama3": {
                    "type": "local",
                    "provider": "ollama",
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                },
                "openai-gpt4": {"type": "cloud", "provider": "openai", "enabled": True},
            },
        )
        with patch(
            "core.system.bootstrap.first_run_detection._probe_local_http",
            return_value=False,
        ):
            result = detect_first_run()
        assert result["ok"] is True
        assert result["usable_backends"] == ["unified-1g"]
        assert result["warnings"] == []

    def test_all_unusable_gives_fix_hints(self, monkeypatch):
        _with_config(monkeypatch, "local", {})
        result = detect_first_run()
        assert result["ok"] is False
        assert any("ollama.ai" in w for w in result["warnings"])


class TestLogging:
    def test_log_ok_is_info_not_warning(self, monkeypatch, caplog):
        summary = {
            "ok": True,
            "usable_backends": ["unified-1g"],
            "deployment_mode": "local",
            "warnings": [],
        }
        log_first_run_warnings(summary)
        assert not any("No usable" in r.message for r in caplog.records)

    def test_log_failure_emits_warnings(self, caplog):
        summary = {
            "ok": False,
            "usable_backends": [],
            "deployment_mode": "local",
            "warnings": ["⚠️  fix me"],
        }
        log_first_run_warnings(summary)
        assert any("fix me" in r.message for r in caplog.records)
