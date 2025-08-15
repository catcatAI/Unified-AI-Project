# Minimal settings configuration for chromadb shim
from typing import Any, Dict, Optional

class Settings:
    def __init__(self, anonymized_telemetry: bool = False, **kwargs):
        self.anonymized_telemetry = anonymized_telemetry
        self.data = kwargs