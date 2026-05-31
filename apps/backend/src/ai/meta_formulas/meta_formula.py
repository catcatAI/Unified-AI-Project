import logging

logger = logging.getLogger(__name__)


class MetaFormula:
    """Base class for all MetaFormulas."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, *args, **kwargs):
        """Executes the meta-formula. Should be overridden by subclasses."""
        logger.warning("[MetaFormula.execute] Not implemented — stub")
        return {"stub": True, "message": f"{self.name} meta-formula not implemented"}
