class SimultaneousTranslation:
    """
    A lightweight, mock simultaneous translation module.

    In production, this would interface with a real streaming translation engine
    (e.g., via WebSocket or gRPC), handle partial hypotheses, timestamps, and
    diarization. Here we provide a minimal, dependency-free placeholder that can
    be swapped out later.
    """

    def __init__(self, default_target_lang: str = "en", latency_ms: int = 100):
        self.default_target_lang = default_target_lang
        self.latency_ms = max(0, latency_ms)

    def translate(self, text: str, source_lang: str = "auto", target_lang: str | None = None) -> dict:
        """
        Synchronously "translates" text. In this mock, we simply echo the text.

        Returns a structured payload for forward compatibility.
        """
        if text is None:
            text = ""
        tgt = target_lang or self.default_target_lang
        return {
            "source_lang": source_lang,
            "target_lang": tgt,
            "original_text": text,
            "translated_text": text,  # mock: no actual translation
            "confidence": 0.9,
            "latency_ms": self.latency_ms,
        }

    def stream_translate(self, chunks: list[str] | tuple[str, ...], source_lang: str = "auto", target_lang: str | None = None):
        """
        Generator that yields partial translation results per chunk.
        This mock yields the chunk as "translated" text without modification.
        """
        import time
        tgt = target_lang or self.default_target_lang
        for idx, chunk in enumerate(chunks or []):
            time.sleep(self.latency_ms / 1000.0)
            yield {
                "index": idx,
                "source_lang": source_lang,
                "target_lang": tgt,
                "original_text": chunk or "",
                "translated_text": (chunk or ""),  # mock
                "is_final": idx == len(chunks) - 1,
                "confidence": 0.85 if idx < (len(chunks) - 1) else 0.9,
            }
