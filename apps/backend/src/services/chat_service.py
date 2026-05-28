# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================
# 職責: 聊天與對話服務 (Chat Service)
# 管理 Angela 的對話邏輯、意圖識別與回應合成。
# =============================================================================

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime

from .angela_llm_service import get_llm_service
from core.engine.state_matrix import StateMatrix4D
from core.engine.state_matrix_adapter import StateMatrixAdapter
from ai.security.ego_guard import EgoGuard

logger = logging.getLogger(__name__)


class ChatService:
    """
    Angela 的聊天核心服務。
    負責意圖分析、上下文管理、以及調用 LLM 生成回應。
    """

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.state_matrix = StateMatrix4D()
        self.state_adapter = StateMatrixAdapter()
        self.ego_guard = EgoGuard()
        self._user_profiles: Dict[str, Dict[str, Any]] = {}
        self._conversation_history: List[Dict[str, str]] = []
        self._initialized = True
        self.pending_evolution_proposals: Dict[str, Any] = {} # [Phase 6]

    async def initialize(self):
        """非同步初始化服務"""
        logger.info("正在初始化 ChatService...")
        # 確保 LLM 服務已就緒
        await get_llm_service()
        logger.info("ChatService 初始化完成。")

    async def _handle_evolution_proposal(self, user_name: str, message: str) -> Optional[str]:
        """
        [Phase 6] 處理演化提案。
        如果用戶確認提案，執行物理寫入。
        """
        msg = message.lower()
        if user_name not in self.pending_evolution_proposals:
            return None
            
        proposal = self.pending_evolution_proposals[user_name]
        
        if any(kw in msg for kw in ["確認", "執行", "實施", "好的", "ok", "yes", "confirm", "approve"]):
            try:
                from src.core.system.evolution.config_mutator import ConfigMutator
                from src.core.system.bootstrap import get_bootstrap_manager
                from .angela_llm_service import get_llm_service
                
                mutator = ConfigMutator()
                success = mutator.apply_mutation(proposal["config_type"], proposal["proposed_updates"])
                
                if success:
                    # 1. 廣播演化
                    bootstrap = get_bootstrap_manager()
                    bootstrap.broadcast_evolution(proposal["config_type"], proposal["proposed_updates"])
                    
                    # 2. 熱加載相關服務
                    if proposal["config_type"] == "llm":
                        llm = await get_llm_service()
                        llm.reload_config()
                    
                    del self.pending_evolution_proposals[user_name]
                    return f"（演化成功）我已經完成自我升級，新的配置已生效！✨"
                else:
                    return f"（演化失敗）寫入配置時似乎遇到了點小麻煩..."
            except Exception as e:
                logger.error(f"Evolution execution error: {e}", exc_info=True)
                return f"（演化失敗）發生了意料之外的錯誤：{e}"
                
        elif any(kw in msg for kw in ["取消", "不", "拒絕", "cancel", "no", "reject"]):
            del self.pending_evolution_proposals[user_name]
            return "（提案已取消）好的，我會維持現狀。"
            
        return None

    def _get_neuro_blender(self):
        """獲取 NeuroBlender 實例（用於備份回應）"""
        try:
            from ai.response.composer import NeuroVocabulary, NeuroBlender
            from ai.memory.template_library import get_template_library
            vocab = NeuroVocabulary()
            library = get_template_library()
            vocab.decompose_from_templates(library)
            return NeuroBlender(vocab)
        except ImportError:
            return None

    async def generate_response(self, user_message: str, user_name: str = "User", origin: str = "Human") -> str:
        if not self._initialized: await self.initialize()

        # [Phase 6] 優先檢查是否有待處理的演化提案確認
        evolution_response = await self._handle_evolution_proposal(user_name, user_message)
        if evolution_response:
            return evolution_response

        sanitized_message, is_violation = self.ego_guard.sanitize_prompt(user_message)

        if is_violation:
            return "（我的核心安全守衛提醒我，這條消息可能包含不當內容，我們聊點別的吧？）"

        # 1. 提取與分析用戶意圖
        intent_analysis = await self._analyze_intent(sanitized_message)
        primary_intent = intent_analysis.get("primary_intent", "general")

        # 2. 獲取當前生理與情緒狀態
        bio_state = self.state_matrix.get_analysis()

        # 3. 處理特定意圖 (如：LLM 管理, 檔案操作等)
        if primary_intent == "llm_manage":
            return await self._handle_llm_manage_intent(sanitized_message, primary_intent)
        elif primary_intent == "file_op":
            return await self._handle_file_intent(sanitized_message, primary_intent)

        # 4. 調用 LLM 生成智慧回應
        response = await self._call_llm(sanitized_message, user_name, bio_state, intent_analysis)

        # [Phase 8 Activation] 啟動語言學習循環 (Linguistic Evolution)
        try:
            from ai.response.learning_loop import get_learning_loop
            loop = get_learning_loop()
            
            # 嘗試綁定詞彙庫，實現學習 -> 合成的閉環
            blender = self._get_neuro_blender()
            if blender and hasattr(blender, "vocabulary"):
                loop.bind_vocabulary(blender.vocabulary)
            
            loop.process_llm_response(response, intent_analysis)
        except Exception as e:
            logger.warning(f"Linguistic learning loop failed: {e}", exc_info=True)

        # 5. 更新對話歷史
        self._conversation_history.append({"role": "user", "content": user_message})
        self._conversation_history.append({"role": "assistant", "content": response})

        # 保持歷史長度
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]

        return response

    async def _analyze_intent(self, text: str) -> Dict[str, Any]:
        """基礎意圖分析 (待升級為更強的 NLU)"""
        text_lower = text.lower()
        intent = "general"

        if any(kw in text_lower for kw in ["切換模型", "使用模型", "llm", "後端", "backend"]):
            intent = "llm_manage"
        elif any(kw in text_lower for kw in ["讀取檔案", "寫入檔案", "file", "存檔"]):
            intent = "file_op"
        elif any(kw in text_lower for kw in ["教你", "學習", "learn", "teach"]):
            intent = "learning"

        return {"primary_intent": intent}

    async def _call_llm(self, message: str, user_name: str, bio_state: Dict[str, Any], intent_analysis: Dict[str, Any]) -> str:
        """核心 LLM 調用封裝"""
        llm = await get_llm_service()
        
        # 準備上下文
        context = {
            "user_name": user_name,
            "bio_state": bio_state,
            "intent": intent_analysis.get("primary_intent"),
            "history": self._conversation_history,
            "state_for_llm": self.state_matrix.export_for_llm()
        }

        try:
            # 嘗試使用 LLM
            response = await llm.generate_response(message, context)
            
            if response.error:
                # 失敗時嘗試使用 NeuroBlender 降級
                logger.warning(f"LLM Error, falling back to NeuroBlender: {response.error}", exc_info=True)
                return await self._try_neuro_fallback(message, bio_state)
                
            return response.text
        except Exception as e:
            logger.error(f"LLM Call failed: {e}", exc_info=True)
            return await self._try_neuro_fallback(message, bio_state)

    async def _try_neuro_fallback(self, text: str, bio_state: Dict[str, Any]) -> str:
        """NeuroBlender 降級回應實作"""
        blender = self._get_neuro_blender()
        if not blender:
            return "（我的大腦似乎有點累了，能休息一下再聊嗎？）"
            
        state_dict = self._build_neuro_blend_state(text, bio_state, None)
        intent_vec = {"casual": 0.5} # 簡化
        
        result = blender.synthesize(
            state_dict=state_dict,
            intent_vec=intent_vec,
            empathy_valence=bio_state.get("valence", 0.0),
            user_name="朋友"
        )
        return result.text

    def _build_neuro_blend_state(self, text: str, bio_state: Dict[str, Any], empathy_analysis: Any) -> Dict[str, Any]:
        """Build state_dict for NeuroBlender from GlobalStateStore (Decoupled Phase 2)"""
        from src.core.system.state_store import state_store
        
        # Get latest states from Store instead of direct matrix access
        alpha = state_store.get_state("alpha")
        beta = state_store.get_state("beta")
        gamma = state_store.get_state("gamma")
        delta = state_store.get_state("delta")
        epsilon = state_store.get_state("epsilon")
        theta = state_store.get_state("theta")
        zeta = state_store.get_state("zeta")

        empathy_valence = 0.0
        if empathy_analysis and hasattr(empathy_analysis, "predicted_emotional_state"):
            empathy_valence = getattr(empathy_analysis.predicted_emotional_state, "valence", 0.0)
            
        return {
            "alpha": {"energy": 1.0 - bio_state.get("stress_level", 0.0) * 0.5},
            "beta": {"curiosity": beta.get("curiosity", 0.5)},
            "gamma": {"valence": bio_state.get("valence", 0.0)},
            "delta": {"intimacy": delta.get("intimacy", 0.3)},
            "epsilon": {"precision": epsilon.get("precision", 0.5)},
            "zeta": {"temporal_coherence": zeta.get("temporal_coherence", 0.5)},
            "theta": {"novelty": theta.get("novelty", 0.3)},
            "eta": {"execution_count": self.eta_state.execution_count if hasattr(self, "eta_state") else 0.5},
        }

    async def _handle_llm_manage_intent(self, text: str, intent: str) -> str:
        self.state_adapter.anchor_learning.on_axis_update("epsilon", {"precision": 0.02}, is_stable=True)
        try:
            import re
            from services.angela_llm_service import get_llm_service
            from src.core.system.evolution.config_mutator import ConfigMutator
            
            llm = await get_llm_service()
            
            # 偵測是否有「切換/使用新模型」的指令
            model_match = re.search(r'(?:使用|切換到|換成|use|switch to)\s*([a-zA-Z0-9\-\._]+)', text, re.I)
            if model_match:
                new_model = model_match.group(1)
                mutator = ConfigMutator()
                # 假設我們要更新目前 active 的 provider
                active_type = getattr(llm, "active_backend_type", None)
                if active_type:
                    backend_id = active_type.value
                    proposal = mutator.propose_change("llm", {backend_id: {"model_name": new_model}})
                    
                    # 存入待處理提案
                    self.pending_evolution_proposals[user_name] = proposal
                    
                    return f"（演化提案）我識別到妳想讓我使用模型 `{new_model}`。這將修改我的系統配置，妳確認要執行這個自我演化嗎？（請回覆：確認/取消）"

            lines = ["可用後端："]
            for backend_type, backend in llm.backends.items():
                model = getattr(backend, "model", "unknown")
                avail = "✅" if getattr(backend, "is_available", False) else "❌"
                active = "👈" if backend == getattr(llm, "active_backend", None) else ""
                lines.append(f"  {avail} {backend_type.value} ({model}) {active}")
            return "（LLM 管理）目前運行狀態如下。妳可以告訴我「切換到某模型」來觸發演化。\n" + "\n".join(lines)
        except Exception as e:
            logger.warning(f"LLM manage intent failed: {e}", exc_info=True)
            return "（LLM 管理模組載入失敗）"

    async def _handle_file_intent(self, text: str, intent: str) -> str:
        return "（檔案操作功能正在對齊中，稍後為妳開啟...）"

    def _get_anchor_keywords(self) -> Dict[str, List[str]]:
        """從分層配置讀取維度關鍵詞 [Phase 7]"""
        try:
            from core.config_loader import get_formula_config
            matrix_conf = get_formula_config("matrix")
            dims = matrix_conf.get("dimensions", {})
            return {name: d.get("anchor_keywords", []) for name, d in dims.items()}
        except Exception:
            # 極簡回退
            return {"alpha": ["energy"], "beta": ["think"]}

    def _get_state_constants(self, key: str, default):
        """從分層配置讀取行為常量 [Phase 7]"""
        try:
            from core.config_loader import get_formula_config
            dyn_conf = get_formula_config("dynamic")
            return dyn_conf.get("state_constants", {}).get(key, default)
        except Exception:
            return default

# Module-level exports for backward compatibility (Phase 7 fix)
_chat_service_instance = None

async def get_angela_chat_service():
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
        await _chat_service_instance.initialize()
        from core.interfaces.service_registry import get_registry
        get_registry().register("chat_service", _chat_service_instance)
    return _chat_service_instance

async def generate_angela_response(user_message, user_name="User"):
    svc = await get_angela_chat_service()
    return await svc.generate_response(user_message, user_name)
