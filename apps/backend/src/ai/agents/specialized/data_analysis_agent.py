import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
try:
    import numpy as np
except ImportError:
    np = None
try:
    import pandas as pd
except ImportError:
    pd = None

from ..base.base_agent import BaseAgent
from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for data analysis tasks.
    """

    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_statistical_analysis_v1.0",
                "name": "statistical_analysis",
                "description": "Performs statistical analysis on numerical data.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "array", "required": True, "description": "Data for analysis"}
                ],
                "returns": {"type": "object", "description": "Analysis results."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities, agent_name="DataAnalysisAgent")

        # Register handlers
        self.register_task_handler(f"{agent_id}_statistical_analysis_v1.0", self._handle_stat_analysis)

    async def _handle_stat_analysis(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        data = payload.get("parameters", {}).get("data", [])
        if not data: return {"error": "No data"}
        
        if np:
            arr = np.array(data)
            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "count": len(arr)
            }
        return {"error": "Numpy not available", "count": len(data)}