# =============================================================================
# ANGELA-MATRIX: [L2] [βγδ] [A] [L3+]
# =============================================================================
#
# 职责: 統一知識管線 — 在 LLM 呼叫前查詢所有本地數據源
# 维度: 認知(β) 情感(γ) 精神(δ)
# 安全: 使用 Key A (后端控制)
# 成熟度: L3+ 等級
#
# 數據源（使用現有模組，不重複實現）:
#   1. MathVerifier — 數學計算 (services/math_verifier.py)
#   2. KnowledgeBase — 顏色/動物/單位/化學 (ai/knowledge_base.py)
#   3. WeatherService — 天氣查詢 (services/weather_service.py)
#   4. DictionaryLayer — 字典翻譯 (ai/ed3n/dictionary_layer.py, 242k 詞條)
#   5. KGImporter — 知識圖譜 (ai/garden/kg_import.py, IS_A 關係)
#   6. GroundedKnowledgeStore — 已驗證事實 (ai/memory/grounded_knowledge.py)
#   7. PlanningEngine — 步驟規劃 (ai/reasoning/planning_engine.py)
#   8. RelationalChain — 多跳推理 (ai/reasoning/relational_chain.py)
#   9. CausalReasoningEngine — 因果推論 (ai/reasoning/causal_reasoning_engine.py)
#   10. HAM Memory — 過去對話記憶
#
# =============================================================================

import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class KnowledgePipeline:
    """統一知識查詢管線 — 在 LLM 之前提供本地答案。

    使用現有組件，不重複實現:
        - KGImporter: 生成/載入知識圖譜（IS_A 關係）
        - GroundedKnowledgeStore: 存儲已驗證事實
        - PlanningEngine: 生成步驟序列
        - RelationalChain: 多跳推理
        - CausalReasoningEngine: 因果推論
    """

    def __init__(
        self,
        math_verifier=None,
        knowledge_base=None,
        weather_service=None,
        dictionary_layer=None,
        symbolic_reasoner=None,
        web_search_tool=None,
        ham_memory=None,
        kg_importer=None,
        grounded_knowledge=None,
        planning_engine=None,
    ):
        self._math = math_verifier
        self._kb = knowledge_base
        self._weather = weather_service
        self._dict = dictionary_layer
        self._symbolic = symbolic_reasoner
        self._web = web_search_tool
        self._ham = ham_memory
        self._kg = kg_importer
        self._grounded = grounded_knowledge
        self._planner = planning_engine

    async def query(self, text: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """依序查詢所有數據源，返回第一個有效答案。

        Returns:
            {"answer": str, "source": str, "confidence": float} or None
        """
        if not text or not isinstance(text, str):
            return None

        text = text.strip()
        if len(text) > 4000:
            text = text[:4000]

        steps = [
            ("math", self._try_math),
            ("weather", self._try_weather),
            ("knowledge", self._try_knowledge),
            ("grounded", self._try_grounded_knowledge),
            ("dictionary_lookup", self._try_dictionary_lookup),
            ("symbolic", self._try_symbolic),
            ("memory", self._try_memory),
        ]

        for source_name, handler in steps:
            try:
                result = await handler(text, context or {})
                if result and result.get("answer"):
                    result["source"] = source_name
                    logger.debug("[KnowledgePipeline] Hit from %s: %s", source_name, result["answer"][:50])
                    return result
            except Exception as e:
                logger.debug("[KnowledgePipeline] %s failed: %s", source_name, e)
                continue

        return None

    async def _try_math(self, text: str, ctx: Dict) -> Optional[Dict]:
        if not self._math:
            return None
        try:
            if hasattr(self._math, "is_math_message") and self._math.is_math_message(text):
                verification = self._math.verify(text)
                if verification and getattr(verification, "is_correct", False):
                    answer = getattr(verification, "final_answer", None) or getattr(verification, "response_text", None)
                    if answer:
                        return {"answer": str(answer), "confidence": 0.99}
        except Exception as e:
            logger.debug("_try_math: %s", e)
        return None

    async def _try_weather(self, text: str, ctx: Dict) -> Optional[Dict]:
        if not self._weather:
            return None
        try:
            is_weather, location = self._detect_weather_query(text)
            if not is_weather:
                return None
            weather = await self._weather.get_weather(location if location else "Taipei")
            if weather and not weather.get("error"):
                desc = weather.get("description", "")
                temp = weather.get("temp_c", "?")
                humidity = weather.get("humidity", "?")
                wind = weather.get("wind_kph", "?")
                loc = weather.get("location", location or "台北")
                if loc == "Taipei":
                    loc = "台北"
                answer = f"{loc}目前天氣：{desc}，溫度 {temp}°C，濕度 {humidity}%，風速 {wind} km/h"
                return {"answer": answer, "confidence": 0.95}
        except Exception as e:
            logger.debug("_try_weather: %s", e)
        return None

    async def _try_knowledge(self, text: str, ctx: Dict) -> Optional[Dict]:
        try:
            from ai.knowledge_base import route_knowledge
            answer = route_knowledge(text)
            if answer:
                return {"answer": answer, "confidence": 0.95}
        except Exception as e:
            logger.debug("_try_knowledge: %s", e)
        return None

    async def _try_grounded_knowledge(self, text: str, ctx: Dict) -> Optional[Dict]:
        """Query GroundedKnowledgeStore for verified facts."""
        if not self._grounded:
            return None
        try:
            related = self._grounded.find_related(text, limit=3)
            if related:
                verified = [c for c in related if c.status.value == "verified"]
                if verified:
                    answers = []
                    for claim in verified[:3]:
                        answers.append(claim.text)
                    return {"answer": "\n".join(answers), "confidence": 0.90, "source": "grounded_knowledge"}
        except Exception as e:
            logger.debug("_try_grounded_knowledge: %s", e)
        return None

    async def _try_dictionary_lookup(self, text: str, ctx: Dict) -> Optional[Dict]:
        """Query the ED3N DictionaryLayer (242k+ entries) for translations/definitions."""
        try:
            from ai.ed3n.ed3n_engine import ED3NEngine
            engine = ED3NEngine.get_shared(load_trained=False)
            if not engine or not hasattr(engine, "dictionary"):
                return None
            stats = engine.dictionary.get_stats()
            if stats.get("entry_count", 0) < 100:
                return None
            is_dict_query, query = self._detect_dictionary_query(text)
            if not is_dict_query or not query:
                return None
            results = engine.dictionary.encode_soft(query)
            if results:
                top_keys = sorted(results.keys(), key=lambda k: results[k], reverse=True)[:5]
                entries = engine.dictionary.lookup(top_keys)
                parts = []
                for key, entry in entries.items():
                    if not entry:
                        continue
                    surfaces = getattr(entry, 'surface_forms', {})
                    if isinstance(surfaces, dict) and surfaces:
                        zh = surfaces.get('zh', '')
                        en = surfaces.get('en', '')
                        if zh and en:
                            parts.append(f"{zh} = {en}")
                        elif zh:
                            parts.append(zh)
                        elif en:
                            parts.append(en)
                    elif entry.contexts:
                        parts.append(f"{key}: {entry.contexts[0]}")
                if parts:
                    return {"answer": "\n".join(parts[:3]), "confidence": 0.90, "source": "dictionary"}
        except Exception as e:
            logger.debug("_try_dictionary_lookup: %s", e)
        return None

    async def _try_dictionary(self, text: str, ctx: Dict) -> Optional[Dict]:
        if not self._dict:
            return None
        try:
            is_dict, query = self._detect_dictionary_query(text)
            if not is_dict:
                return None
            results = self._dict.lookup(query, limit=3)
            if results:
                parts = []
                for r in results[:3]:
                    if isinstance(r, dict):
                        word = r.get("word", r.get("key", ""))
                        meaning = r.get("meaning", r.get("value", r.get("definition", "")))
                        if word and meaning:
                            parts.append(f"{word}: {meaning}")
                if parts:
                    return {"answer": "\n".join(parts), "confidence": 0.90}
        except Exception as e:
            logger.debug("_try_dictionary: %s", e)
        return None

    async def _try_symbolic(self, text: str, ctx: Dict) -> Optional[Dict]:
        if not self._symbolic:
            return None
        try:
            result = self._symbolic.route_reasoning(text)
            if result:
                return {"answer": str(result), "confidence": 0.85}
        except Exception as e:
            logger.debug("_try_symbolic: %s", e)
        return None

    async def _try_memory(self, text: str, ctx: Dict) -> Optional[Dict]:
        if not self._ham:
            return None
        try:
            memories = await self._ham.retrieve(text, limit=3)
            if memories:
                parts = []
                for m in memories[:3]:
                    if isinstance(m, dict):
                        content = m.get("content", m.get("response", ""))
                        if content:
                            parts.append(content)
                if parts:
                    return {"answer": "\n".join(parts), "confidence": 0.70}
        except Exception as e:
            logger.debug("_try_memory: %s", e)
        return None

    @staticmethod
    def _detect_weather_query(text: str) -> Tuple[bool, Optional[str]]:
        t = text.lower()
        weather_keywords = [
            "天氣", "天气", "氣溫", "气温", "溫度", "温度",
            "weather", "temperature", "forecast",
            "下雨", "刮風", "颱風", "颱風", "rain", "snow",
        ]
        location_patterns = [
            r"(.{1,10})(?:的)?(?:天氣|天气|氣溫|weather)",
            r"(?:天氣|天气|weather|forecast)\s+(?:in|at|of)?\s*(.+)",
        ]
        for kw in weather_keywords:
            if kw in t:
                for pat in location_patterns:
                    m = re.search(pat, t)
                    if m:
                        loc = m.group(1).strip()
                        if loc and loc not in ("天氣", "天气", "the", "a", "今天", "現在", "目前"):
                            return True, loc
                return True, None
        return False, None

    @staticmethod
    def _detect_dictionary_query(text: str) -> Tuple[bool, str]:
        t = text.strip()
        patterns = [
            r"(?:什麼意思|是什么意思|meaning of|define|翻譯|翻译|translate)\s+(.+)",
            r"(.+?)(?:的?意思|的?翻譯|的?翻译|的意思)",
            r"how do you say\s+(.+?)(?:\s+in\s+(?:chinese|english|japanese))?",
        ]
        for pat in patterns:
            m = re.search(pat, t, re.IGNORECASE)
            if m:
                query = m.group(1).strip()
                if query and len(query) >= 1:
                    return True, query
        # Bare short-string translation only when it looks like a LOOKUP:
        # single word / short noun phrase. Questions, greetings and
        # chit-chat must NOT be hijacked (measured: "你好呀" -> "你好 = hello").
        if len(t) <= 10 and re.match(r"^[\w\s\-\u4e00-\u9fff]+$", t):
            question_marks = ("?", "？", "吗", "嗎", "呢")
            greetings = (
                "你好", "您好", "hi", "hello", "hey", "嗨", "哈囉", "哈嘍",
                "早安", "晚安", "午安", "謝謝", "谢谢", "再見", "再见",
                "你好呀", "您好吗", "你好嗎", "你好吗",
            )
            if any(g in t for g in greetings) or any(mk in t for mk in question_marks):
                return False, ""
            words = t.split()
            if len(words) > 3:      # a sentence, not a lookup
                return False, ""
            return True, t
        return False, ""


_pipeline_instance: Optional[KnowledgePipeline] = None


def get_knowledge_pipeline(
    math_verifier=None,
    knowledge_base=None,
    weather_service=None,
    dictionary_layer=None,
    symbolic_reasoner=None,
    web_search_tool=None,
    ham_memory=None,
) -> KnowledgePipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = KnowledgePipeline(
            math_verifier=math_verifier,
            knowledge_base=knowledge_base,
            weather_service=weather_service,
            dictionary_layer=dictionary_layer,
            symbolic_reasoner=symbolic_reasoner,
            web_search_tool=web_search_tool,
            ham_memory=ham_memory,
        )
    return _pipeline_instance


__all__ = ["KnowledgePipeline", "get_knowledge_pipeline"]
