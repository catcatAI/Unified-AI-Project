# Minimal settings configuration for chromadb shim:
lass ChromaDBConfig:
    def __init__(self, anonymized_telemetry: bool = False, **kwargs) -> None:
        self.anonymized_telemetry = anonymized_telemetry:
elf.data = kwargs