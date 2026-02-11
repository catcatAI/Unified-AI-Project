# =============================================================================
# ANGELA-MATRIX: L6[执行层] β [A] L3+
# =============================================================================
#
# 职责: 数据分析代理，处理数值和统计数据
# 维度: 涉及认知维度 (β) 的逻辑分析和数据处理
# 安全: 使用 Key A (后端控制) 进行数据隐私保护
# 成熟度: L3+ 等级可以进行复杂的数据分析
#
# 能力:
# - statistical_analysis: 统计分析
# - data_visualization: 数据可视化
# - pattern_recognition: 模式识别
# - trend_analysis: 趋势分析
#
# =============================================================================

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