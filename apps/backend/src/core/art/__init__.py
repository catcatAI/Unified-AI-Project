# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L1]
# =============================================================================
"""
Art module: real voice generation (TTS) and real browser control.

Provides:
  - AngelaRealVoice: Microsoft Edge TTS integration for speech synthesis
  - AngelaRealBrowser: Playwright-based web browser for content extraction
"""

from core.art.real_edge_tts import AngelaRealVoice
from core.art.real_playwright_browser import AngelaRealBrowser

__all__ = [
    "AngelaRealVoice",
    "AngelaRealBrowser",
]
