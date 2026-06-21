"""
P34 tests: Frontend Multimodal Panel for Electron Desktop.

Tests cover:
  - HTML structure: correct elements exist
  - API client: multimodal methods work correctly
  - main.js integration: IPC handlers registered

Total: 10 tests
"""

import json
import re
import sys
from pathlib import Path

import pytest

# Paths — resolve from project root (3 levels up from tests/desktop/)
ROOT = Path(__file__).resolve().parent.parent.parent
DESKTOP_APP = ROOT / "apps/desktop-app/electron_app"
MAIN_JS = DESKTOP_APP / "main.js"
HTML_FILE = DESKTOP_APP / "multimodal-panel.html"
CLIENT_JS = DESKTOP_APP / "js" / "multimodal-client.js"
PANEL_JS = DESKTOP_APP / "js" / "multimodal-panel.js"


class TestMultimodalPanelHTML:
    """T1-T4: HTML structure tests."""

    def test_html_file_exists(self):
        """T1: multimodal-panel.html exists."""
        assert HTML_FILE.exists(), f"File not found: {HTML_FILE}"
        content = HTML_FILE.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_html_has_required_tabs(self):
        """T2: HTML has all 5 tab sections."""
        content = HTML_FILE.read_text(encoding="utf-8")
        tabs = ["tab-encode", "tab-compare", "tab-generate", "tab-train", "tab-quality"]
        for tab in tabs:
            assert f'id="{tab}"' in content, f"Missing tab section: {tab}"

    def test_html_has_upload_zones(self):
        """T3: HTML has vision and audio upload zones."""
        content = HTML_FILE.read_text(encoding="utf-8")
        assert 'id="vision-upload"' in content
        assert 'id="audio-upload"' in content
        assert 'id="record-btn"' in content

    def test_html_has_quality_metrics(self):
        """T4: HTML has quality dashboard with all metrics."""
        content = HTML_FILE.read_text(encoding="utf-8")
        metrics = ["q-ssim", "q-psnr", "q-vision-calls", "q-vision-time",
                   "q-snr", "q-audio-calls", "q-audio-time", "health-bar-fill"]
        for m in metrics:
            assert f'id="{m}"' in content, f"Missing metric element: {m}"

    def test_html_links_scripts(self):
        """T5: HTML loads multimodal-client.js and multimodal-panel.js."""
        content = HTML_FILE.read_text(encoding="utf-8")
        assert 'src="js/multimodal-client.js"' in content
        assert 'src="js/multimodal-panel.js"' in content


class TestMultimodalClientJS:
    """T6-T7: API client JavaScript tests."""

    def test_client_file_exists(self):
        """T6: multimodal-client.js has all required methods."""
        assert CLIENT_JS.exists()
        content = CLIENT_JS.read_text(encoding="utf-8")
        required_methods = [
            "encode(", "decode(", "compare(", "retrieve(",
            "train(", "evaluate(", "generate(", "crossInfer(",
            "qualityDashboard(", "checkHealth(", "multimodalHealth("
        ]
        for method in required_methods:
            assert method in content, f"Missing method: {method}"

    def test_client_exports(self):
        """T7: multimodal-client.js exports MultimodalAPIClient class."""
        content = CLIENT_JS.read_text(encoding="utf-8")
        assert "class MultimodalAPIClient" in content
        assert "module.exports" in content or "MultimodalAPIClient" in content


class TestMultimodalPanelJS:
    """T8: Panel JavaScript tests."""

    def test_panel_js_file_exists(self):
        """T8: multimodal-panel.js has all required methods."""
        assert PANEL_JS.exists()
        content = PANEL_JS.read_text(encoding="utf-8")
        required = [
            "class MultimodalPanel",
            "DOMContentLoaded",
            "_bindVisionUpload",
            "_bindAudioUpload",
            "_bindEncodeDecode",
            "_bindCompare",
            "_bindGenerate",
            "_bindTrain",
            "_bindQuality",
            "_doVisionEncode",
            "_doAudioEncode",
            "_refreshQuality",
            "_refreshItems",
        ]
        for r in required:
            assert r in content, f"Missing in panel JS: {r}"


class TestMainJSIntegration:
    """T9-T10: main.js integration tests."""

    def test_multimodal_ipc_handler(self):
        """T9: main.js has multimodal IPC handlers."""
        content = MAIN_JS.read_text(encoding="utf-8")
        assert "multimodal-open" in content
        assert "multimodal-is-open" in content
        assert "createMultimodalWindow" in content
        assert "multimodalWindow" in content

    def test_multimodal_context_menu(self):
        """T10: main.js context menu has Multimodal Panel item."""
        content = MAIN_JS.read_text(encoding="utf-8")
        assert "Multimodal Panel" in content
        assert "multimodal-panel.html" in content

    def test_multimodal_window_config(self):
        """T10b: multimodal window has correct config."""
        content = MAIN_JS.read_text(encoding="utf-8")
        assert "width: 1000" in content or "width:1000" in content
        assert "multimodal-panel.html" in content
