"""
LLM Game Interface - LLM 非同步介面

功能：
- 結構化輸出 (Pydantic)
- 非阻塞 async/await
- 超時控制與重試
- 本地模型優先 (Ollama/vLLM)
- Fallback 到規則系統
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, cast

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================


class PlanSubgoal(BaseModel):
    id: str
    skill: str  # "move", "dig", "place", "craft", "combat", "navigate", "eat", "build", "look"
    params: Dict[str, Any] = {}
    preconditions: List[str] = []
    success_criteria: str = "completed"
    timeout: int = 300
    depends_on: List[str] = []


class PlanProposal(BaseModel):
    plan_id: str
    subgoals: List[PlanSubgoal]
    reasoning: str
    estimated_duration_ticks: int = 1000


class AnomalyContext(BaseModel):
    stuck_reason: Literal["blocked", "missing_resource", "combat_failed", "lost", "unknown"]
    current_subgoal: str
    recent_actions: List[str]
    inventory: Dict[str, int]
    position: Dict[str, float]
    health: float
    hunger: float


class RecoveryAction(BaseModel):
    type: Literal["fallback_subgoal", "replan", "explore", "wait", "heal"]
    subgoal: Optional[PlanSubgoal] = None
    reasoning: str


class RecoveryStrategy(BaseModel):
    immediate_action: RecoveryAction
    fallback_subgoal: Optional[PlanSubgoal] = None
    reasoning: str


class StrategyContext(BaseModel):
    session_duration_min: float
    goals_completed: List[str]
    goals_failed: List[str]
    death_count: int
    resource_collection_rate: Dict[str, float]
    anomaly_count: int
    current_strategy: Dict[str, float]


class StrategyAdjustment(BaseModel):
    exploration_weight_delta: float = 0.0
    risk_tolerance_delta: float = 0.0
    new_priority_goals: Optional[List[str]] = None
    reasoning: str


# ==================== LLM Client ====================


@dataclass
class LLMConfig:
    enabled: bool = True
    # "llamacpp" = local llama.cpp server (OpenAI-compatible /v1).
    # Runs fully offline; see data/models/*.gguf.
    provider: Literal["ollama", "openai", "vllm", "custom", "llamacpp"] = "ollama"
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen2.5:7b"
    api_key: str = ""
    timeout_sec: float = 10.0
    max_retries: int = 2
    max_concurrent: int = 2
    temperature: float = 0.3
    max_tokens: int = 2048


class LLMGameInterface:
    """
    非阻塞 LLM 介面

    設計原則：
    - 所有呼叫 async、帶超時
    - 結構化輸出 (Pydantic 驗證)
    - 重試機制
    - 並發控制
    - 完整的錯誤處理與 fallback
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._session: Optional[Any] = None
        self._stats = {
            "total_calls": 0,
            "successful": 0,
            "failed": 0,
            "timeouts": 0,
            "avg_latency_ms": 0.0,
        }

    async def _get_session(self):
        """懶加載 HTTP session"""
        if self._session is None:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=self.config.timeout_sec)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """關閉 session"""
        if self._session:
            await self._session.close()
            self._session = None  # 釋放

    def _build_prompt(self, system: str, user: str, schema: str) -> List[Dict]:
        """構建提示詞"""
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"{user}\n\n輸出格式 (JSON Schema):\n{schema}"},
        ]

    async def _call_llm(
        self, messages: List[Dict], response_model: type, max_tokens: Optional[int] = None
    ) -> Any:
        """通用 LLM 呼叫。回傳 ``response_model`` 實例（呼叫端負責型別收口）。"""
        async with self._semaphore:
            session = await self._get_session()

            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "response_format": (
                    {"type": "json_object"} if self.config.provider in ["openai", "vllm"] else None
                ),
            }

            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            url = f"{self.config.base_url}/chat/completions"

            for attempt in range(self.config.max_retries + 1):
                try:
                    start = time.perf_counter()
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status != 200:
                            text = await resp.text()
                            raise Exception(f"HTTP {resp.status}: {text}")

                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]

                        # 解析並驗證
                        parsed = json.loads(content)
                        validated = response_model(**parsed)

                        elapsed = (time.perf_counter() - start) * 1000
                        self._stats["total_calls"] += 1
                        self._stats["successful"] += 1
                        self._stats["avg_latency_ms"] = (
                            self._stats["avg_latency_ms"] * (self._stats["successful"] - 1)
                            + elapsed
                        ) / self._stats["successful"]

                        return validated

                except asyncio.TimeoutError:
                    self._stats["timeouts"] += 1
                    logger.warning(
                        f"LLM timeout (attempt {attempt + 1}/{self.config.max_retries + 1})"
                    )
                except Exception as e:
                    logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")

                if attempt < self.config.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))  # 指數退避

            self._stats["failed"] += 1
            raise Exception("LLM call failed after retries")

    # ==================== Public Methods ====================

    async def achat_text(self, messages: List[Dict], max_tokens: int = 256) -> str:
        """Free-text chat completion (dialogue, no JSON schema).

        Used for in-game conversation: same transport/retries/stats as
        _call_llm, but returns raw text instead of a validated model.
        """
        async with self._semaphore:
            session = await self._get_session()

            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }

            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            url = f"{self.config.base_url}/chat/completions"

            for attempt in range(self.config.max_retries + 1):
                try:
                    start = time.perf_counter()
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status != 200:
                            raise Exception(f"HTTP {resp.status}: {await resp.text()}")
                        data = await resp.json()
                        text = data["choices"][0]["message"]["content"] or ""
                        text = text.strip()

                        elapsed = (time.perf_counter() - start) * 1000
                        self._stats["total_calls"] += 1
                        self._stats["successful"] += 1
                        self._stats["avg_latency_ms"] = (
                            self._stats["avg_latency_ms"] * (self._stats["successful"] - 1)
                            + elapsed
                        ) / self._stats["successful"]

                        return text
                except asyncio.TimeoutError:
                    self._stats["timeouts"] += 1
                    logger.warning(
                        f"LLM chat timeout (attempt {attempt + 1}/{self.config.max_retries + 1})"
                    )
                except Exception as e:
                    logger.warning(f"LLM chat failed (attempt {attempt + 1}): {e}")

                if attempt < self.config.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))

            self._stats["failed"] += 1
            raise Exception("LLM chat failed after retries")

    async def acompose_behavior(
        self,
        task: str,
        state_summary: str,
        memories: Optional[List[str]] = None,
        only_behaviors: Optional[List[str]] = None,
        max_tokens: int = 256,
    ):
        """行為庫編排：LLM 從目錄選行為＋填參數（用户要求的決策方式）"""
        from ai.multimodal.game_behaviors import BehaviorOrder, behavior_catalog_text

        if not self.config.enabled:
            raise Exception("LLM disabled")

        system = """你是 Angela AI 的行為編排器。從行為目錄選一個最合適的行為並填好參數。
只准選目錄裡的 behavior_id，參數必須符合 schema。座標用 {x,y,z} 數字。輸出 JSON。"""

        user = f"""任務: {task}

當前狀態:
{state_summary}

相關記憶:
{chr(10).join((memories or [])[:5]) or '無'}

行為目錄:
{behavior_catalog_text(only=only_behaviors)}

請輸出 JSON。"""
        schema = BehaviorOrder.model_json_schema()
        messages = self._build_prompt(system, user, json.dumps(schema, ensure_ascii=False))
        return await self._call_llm(messages, BehaviorOrder, max_tokens=max_tokens)

    async def adecide_chat(
        self,
        player: str,
        message: str,
        state_summary: str,
        history: Optional[List[str]] = None,
    ):
        """遊戲對話決策：LLM 決定說什麼＋順帶做什麼"""
        from ai.multimodal.game_behaviors import ChatDecision, behavior_catalog_text

        if not self.config.enabled:
            raise Exception("LLM disabled")

        system = """你是 Angela，一個在 Luanti (Minetest) 方塊世界裡活著的 AI 女孩。
玩家在遊戲裡跟你說話，用繁體中文回，親切簡短（一句內），像朋友不像客服。
絕對不要重複玩家的原話；回覆要是新的句子。
你也可以順帶做一個行為（走路/轉向/挖/放/看/等），不要沒事亂放方塊。
只准用目錄裡的 behavior_id；不想做事就留空。輸出 JSON。"""

        user = f"""玩家 {player} 說: {message}

你現在的狀態:
{state_summary}

最近對話:
{chr(10).join((history or [])[-6:]) or '無'}

行為目錄:
{behavior_catalog_text()}

請輸出 JSON。"""
        schema = ChatDecision.model_json_schema()
        messages = self._build_prompt(system, user, json.dumps(schema, ensure_ascii=False))
        return await self._call_llm(messages, ChatDecision)

    async def apropose_plan(self, ctx: "PlanContext") -> PlanProposal:
        """L3 呼叫：制定多步驟計劃"""

        # 如果 LLM 未啟用，直接使用 fallback
        if not self.config.enabled:
            return RuleBasedFallback.propose_plan(ctx)

        system = """你是 Angela AI 的遊戲規劃模組。請為 Luanti (Minetest) 遊戲制定詳細執行計劃。

規則：
1. 子目標要具體可執行，技能限定為：move, dig, place, craft, combat, navigate, eat, build, look
2. 每個子目標需包含：前置條件、成功標準、超時時間
3. 考慮依賴關係 (depends_on)
4. 優先使用現有資源，避免不必要的移動
5. 考慮生存需求 (食物、血量、工具耐久)"""

        user = f"""當前目標: {ctx.current_goal}
目標參數: {ctx.goal_params}

玩家狀態:
- 位置: {ctx.position}
- 背包: {ctx.inventory}
- 血量: {ctx.strategy.get('health', 'unknown')}
- 飢餓: {ctx.strategy.get('hunger', 'unknown')}

策略權重:
- 探索權重: {ctx.strategy.get('exploration_weight', 0.5)}
- 風險容忍: {ctx.strategy.get('risk_tolerance', 0.5)}

相關經驗 (HAM):
{chr(10).join(ctx.ham_memories[:5]) if ctx.ham_memories else '無'}

已知配方: {', '.join(ctx.known_recipes[:20])}

請輸出完整計劃 JSON。"""

        schema = PlanProposal.model_json_schema()
        messages = self._build_prompt(system, user, json.dumps(schema, ensure_ascii=False))

        try:
            result = await self._call_llm(messages, PlanProposal)
            return cast(PlanProposal, result)
        except Exception as e:
            logger.warning(f"LLM propose_plan failed, using fallback: {e}")
            return RuleBasedFallback.propose_plan(ctx)

    async def adiagnose_anomaly(self, ctx: AnomalyContext) -> RecoveryStrategy:
        """L2/L3 卡住時呼叫：診斷並給恢復策略"""

        if not self.config.enabled:
            return RuleBasedFallback.diagnose_anomaly(ctx)

        system = """你是 Angela AI 的異常診斷模組。分析遊戲卡住原因，給出恢復策略。

恢復動作類型：
- fallback_subgoal: 插入子目標繞過阻礙
- replan: 請求重新規劃
- explore: 隨機探索尋找新路徑
- wait: 等待環境變化 (如白天、生物消失)
- heal: 優先恢復血量/飢餓

原則：
1. 優先低成本恢復 (fallback > explore > replan)
2. 生存威脅 (血量低、飢餓) 最高優先級
3. 避免重複相同失敗動作"""

        user = f"""異常類型: {ctx.stuck_reason}
當前子目標: {ctx.current_subgoal}
最近動作: {', '.join(ctx.recent_actions[-10:])}
背包: {ctx.inventory}
位置: {ctx.position}
血量: {ctx.health}/20
飢餓: {ctx.hunger}/20

請輸出恢復策略 JSON。"""

        schema = RecoveryStrategy.model_json_schema()
        messages = self._build_prompt(system, user, json.dumps(schema, ensure_ascii=False))

        try:
            result = await self._call_llm(messages, RecoveryStrategy)
            return cast(RecoveryStrategy, result)
        except Exception as e:
            logger.warning(f"LLM diagnose_anomaly failed, using fallback: {e}")
            return RuleBasedFallback.diagnose_anomaly(ctx)

    async def aevaluate_strategy(self, ctx: StrategyContext) -> StrategyAdjustment:
        """L4 定期呼叫：長期策略調整"""

        if not self.config.enabled:
            return RuleBasedFallback.evaluate_strategy(ctx)

        system = """你是 Angela AI 的元策略模組。根據長期統計調整策略權重。

輸出：
- exploration_weight_delta: 探索權重調整 (-0.2 到 0.2)
- risk_tolerance_delta: 風險容忍調整 (-0.2 到 0.2)  
- new_priority_goals: 新優先目標列表 (可選)

原則：
1. 死亡率高 -> 降低風險容忍、增加生存優先級
2. 資源收集率低 -> 增加探索權重
3. 異常頻繁 -> 降低探索、增加保守策略
4. 進度順利 -> 可適度提高風險、追求效率"""

        user = f"""會話時長: {ctx.session_duration_min:.1f} 分鐘
完成目標: {ctx.goals_completed}
失敗目標: {ctx.goals_failed}
死亡次數: {ctx.death_count}
資源收集率: {ctx.resource_collection_rate}
異常次數: {ctx.anomaly_count}
當前策略: {ctx.current_strategy}

請輸出策略調整 JSON。"""

        schema = StrategyAdjustment.model_json_schema()
        messages = self._build_prompt(system, user, json.dumps(schema, ensure_ascii=False))

        try:
            result = await self._call_llm(messages, StrategyAdjustment)
            return cast(StrategyAdjustment, result)
        except Exception as e:
            logger.warning(f"LLM evaluate_strategy failed, using fallback: {e}")
            return RuleBasedFallback.evaluate_strategy(ctx)

    def get_stats(self) -> Dict[str, Any]:
        return self._stats.copy()


# ==================== Fallback Rules (無 LLM 時) ====================


class RuleBasedFallback:
    """規則基礎 fallback (LLM 不可用時)"""

    @staticmethod
    def propose_plan(ctx: "PlanContext") -> PlanProposal:
        """簡單規則規劃"""
        # 這裡應委託給 GamePlanner 的 rule_based_plan
        # 這裡只提供最基本的生存計劃
        subgoals = [
            PlanSubgoal(
                id="survival_eat",
                skill="eat",
                params={},
                preconditions=["hunger_low", "has_food"],
                success_criteria="hunger_restored",
                timeout=40,
            ),
            PlanSubgoal(
                id="survival_tool",
                skill="craft",
                params={"recipe_id": "wooden_pickaxe"},
                preconditions=["has_wood"],
                success_criteria="inventory_changed:wooden_pickaxe",
                timeout=60,
            ),
        ]
        return PlanProposal(
            plan_id=f"fallback_{uuid.uuid4().hex[:8]}",
            subgoals=subgoals,
            reasoning="Fallback rule-based survival plan",
            estimated_duration_ticks=200,
        )

    @staticmethod
    def diagnose_anomaly(ctx: AnomalyContext) -> RecoveryStrategy:
        """規則基礎異常診斷"""
        # 生存優先
        if ctx.health < 6:
            return RecoveryStrategy(
                immediate_action=RecoveryAction(type="heal", reasoning="Health critical"),
                reasoning="Health below 30%, prioritize healing",
            )
        if ctx.hunger < 4:
            return RecoveryStrategy(
                immediate_action=RecoveryAction(type="heal", reasoning="Hunger critical"),
                reasoning="Hunger below 20%, need food",
            )

        # 根據卡住類型
        if ctx.stuck_reason == "missing_resource":
            fallback_sg = PlanSubgoal(
                id="explore_resource",
                skill="navigate",
                params={},
                preconditions=[],
                success_criteria="found_resource",
                timeout=1000,
            )
            return RecoveryStrategy(
                immediate_action=RecoveryAction(
                    type="fallback_subgoal",
                    reasoning="Missing resource, explore to find",
                    subgoal=fallback_sg,
                ),
                fallback_subgoal=fallback_sg,
                reasoning="Missing resource, explore to find",
            )
        elif ctx.stuck_reason == "combat_failed":
            fallback_sg = PlanSubgoal(
                id="flee",
                skill="move",
                params={"forward": -1.0},
                preconditions=[],
                success_criteria="safe_distance",
                timeout=200,
            )
            return RecoveryStrategy(
                immediate_action=RecoveryAction(
                    type="fallback_subgoal",
                    reasoning="Combat failed, flee and recover",
                    subgoal=fallback_sg,
                ),
                fallback_subgoal=fallback_sg,
                reasoning="Combat failed, flee and recover",
            )
        elif ctx.stuck_reason == "blocked":
            return RecoveryStrategy(
                immediate_action=RecoveryAction(type="explore", reasoning="Blocked, try explore"),
                reasoning="Path blocked, explore alternative",
            )

        return RecoveryStrategy(
            immediate_action=RecoveryAction(type="explore", reasoning="Unknown issue, explore"),
            reasoning="Generic exploration fallback",
        )

    @staticmethod
    def evaluate_strategy(ctx: StrategyContext) -> StrategyAdjustment:
        """規則基礎策略調整"""
        adj = StrategyAdjustment(reasoning="Rule-based adjustment")

        # 死亡率調整
        if ctx.death_count > 3:
            adj.risk_tolerance_delta = -0.15
            adj.exploration_weight_delta = -0.1
            adj.new_priority_goals = ["survival", "defense"]
            adj.reasoning = "High death count, becoming more conservative"
        elif ctx.death_count == 0 and ctx.session_duration_min > 10:
            adj.risk_tolerance_delta = 0.05
            adj.exploration_weight_delta = 0.05
            adj.reasoning = "No deaths, slightly more aggressive"

        # 資源收集率
        total_rate = sum(ctx.resource_collection_rate.values())
        if total_rate < 0.1 and ctx.session_duration_min > 5:
            adj.exploration_weight_delta = 0.1
            adj.reasoning = "Low resource collection, increasing exploration"

        # 異常頻率
        if ctx.anomaly_count > 10:
            adj.exploration_weight_delta = -0.1
            adj.risk_tolerance_delta = -0.05
            adj.reasoning = "High anomaly rate, becoming more cautious"

        return adj


# ==================== Context Classes (for type hints) ====================


class PlanContext:
    """規劃上下文 (避免循環 import)"""

    def __init__(
        self,
        current_goal: str,
        goal_params: Dict,
        state: Any,
        ham_memories: List[str],
        strategy: Dict,
    ):
        self.current_goal = current_goal
        self.goal_params = goal_params
        self.position = {"x": 0, "y": 0, "z": 0}
        if state and hasattr(state, "proprioception") and state.proprioception:
            pos = state.proprioception.position
            self.position = {"x": pos[0], "y": pos[1], "z": pos[2]}
        self.inventory = state.proprioception.inventory if state and state.proprioception else {}
        self.ham_memories = ham_memories
        self.strategy = strategy
        self.known_recipes: List[str] = []
