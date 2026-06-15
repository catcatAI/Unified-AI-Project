import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from services.llm.router import AngelaLLMService
from ai.core.model_bus import ModelBus, ModelRouteResult, RouteDecision
from core.interfaces.protocols import LLMResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_refinement_pipeline():
    """測試當 ModelBus 回傳中等信心值時，是否正確觸發 LLM 潤色管線"""
    
    # 1. Setup Mock ModelBus
    mock_bus = MagicMock(spec=ModelBus)
    
    # 模擬 ED3N 回傳中等信心值 (0.6)
    mock_result = ModelRouteResult(
        model_id="ed3n",
        text="我是Angela，很高興認識你。",
        confidence=0.6,
        latency_ms=1.0,
        domain="reflex"
    )
    
    mock_decision = RouteDecision(
        query="你是誰",
        query_type="reflex",
        selected_model="ed3n",
        results={"ed3n": mock_result},
        total_latency_ms=1.5,
        confidence=0.6,
        reason="Matched personality preset"
    )
    
    mock_bus.route = AsyncMock(return_value=mock_decision)
    
    # 2. Setup AngelaLLMService
    service = AngelaLLMService()
    service.model_bus = mock_bus
    
    # Mock LLM Backend to check if it receives the draft
    mock_backend = AsyncMock()
    mock_backend.generate.return_value = LLMResponse(text="潤色後的回應", confidence=0.9)
    service.active_backend = mock_backend
    service.is_available = True
    
    # 3. Execute request
    logger.info("Starting refinement pipeline test...")
    context = {"intent": "reflex"}
    response = await service.generate_response("你是誰", context=context)
    
    # 4. Assertions
    logger.info(f"Final Response: {response.text}")
    
    # 檢查 context 是否被注入了 draft_response
    assert "draft_response" in context
    assert context["draft_response"] == "我是Angela，很高興認識你。"
    logger.info("✅ Context successfully injected with draft_response")
    
    # 檢查 LLM backend 是否被調用（因為信心值 0.6 低於直接返回閾值 0.8）
    assert mock_backend.generate.called
    logger.info("✅ LLM Backend was called for refinement")
    
    logger.info("Refinement pipeline test passed!")

if __name__ == "__main__":
    asyncio.run(test_refinement_pipeline())
