"""
Angela Math Verifier - 雙軌數學驗證系統
========================================

架構：LLM 提取計算式 → 引擎驗證結果 → 比對並校正

| 組件 | 職責 |
|------|------|
| MathExtractor | LLM 提取數學表達式 + 理解 |
| SpatialEngine | 原生空間幾何運算（ground truth）|
| MathVerifier | 比對器 + 觸發狀態更新 |

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger("angela_math_verifier")


@dataclass
class ExtractionResult:
    """LLM 提取結果"""
    expression: Optional[str] = None
    understanding: Optional[str] = None
    assumptions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    llm_answer: Optional[float] = None
    raw_response: Optional[str] = None
    is_valid: bool = False


@dataclass
class VerificationResult:
    """驗證結果"""
    expression: str
    llm_answer: Optional[float] = None
    engine_answer: Optional[float] = None
    matches: bool = False
    discrepancy: float = 0.0
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    extraction: Optional[ExtractionResult] = None
    final_answer: Optional[float] = None
    response_text: Optional[str] = None


class MathExtractor:
    """
    [L4-Cognitive] LLM 數學提取器
    負責從自然語言中識別數學意圖並提取計算式
    """

    MATH_EXTRACTION_PROMPT = """你是一個數學意圖提取器。分析用戶的輸入：

1. 如果包含數學計算，返回 JSON：
{
    "understanding": "用戶想計算什麼（你的理解）",
    "expression": "數學表達式（如 1500-3*299）",
    "assumptions": ["你的假設列表"],
    "confidence": 0.0~1.0（你對提取的自信度）",
    "answer": 你的計算結果
}

2. 如果沒有數學內容，返回：
{"is_math": false}

重要：
- confidence < 0.7 時，說明你不確定，assumptions 要列出可能的歧義
- 計算式要完整、可執行（包含括號）
- 金額默認使用小數（如 299.00）"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    async def extract(self, user_message: str) -> ExtractionResult:
        """
        從用戶消息中提取數學意圖
        """
        result = ExtractionResult()

        if not self._contains_likely_math(user_message):
            return result

        try:
            if self.llm_service:
                raw = await self._call_llm(user_message)
            else:
                raw = self._fallback_extract(user_message)

            result.raw_response = raw

            if not raw:
                return result

            if raw.startswith("{"):
                data = json.loads(raw)
                if data.get("is_math") is False:
                    return result

                result.expression = data.get("expression")
                result.understanding = data.get("understanding", "")
                result.assumptions = data.get("assumptions", [])
                result.confidence = float(data.get("confidence", 0.5))
                result.llm_answer = self._safe_float(data.get("answer"))
                result.is_valid = bool(result.expression and result.expression.strip())

            elif raw:
                result.expression = self._fallback_extract_expression(raw)
                result.understanding = raw
                result.confidence = 0.3
                result.is_valid = bool(result.expression)

        except json.JSONDecodeError:
            result.expression = self._fallback_extract_expression(raw)
            result.understanding = "從文本推斷的計算"
            result.confidence = 0.2
            result.is_valid = bool(result.expression)
        except Exception as e:
            logger.warning(f"[MathExtractor] Extraction failed: {e}", exc_info=True)
            result.expression = self._fallback_extract_expression(user_message)
            result.understanding = "Fallback 提取"
            result.confidence = 0.1
            result.is_valid = bool(result.expression)

        return result

    def _contains_likely_math(self, text: str) -> bool:
        """快速檢查是否可能包含數學意圖"""
        cfg = None
        try:
            from core.config_loader import get_angela_config
            cfg = get_angela_config().get_authority("angela_core", {}).get("math_verifier", {})
        except Exception as e:
            logger.warning(f"Failed to load math_verifier config: {e}", exc_info=True)
        math_keywords = cfg.get("keywords", {}).get("contains_math", []) if cfg else []
        if not math_keywords:
            math_keywords = [
                "多少", "多少錢", "價格", "計算", "等於", "總共",
                "剩下", "剩餘", "花了", "買了", "賣了",
                "折扣", "打折", "稅", "百分比",
                "+", "-", "*", "/", "×", "÷",
                "加", "減", "乘", "除", "平方", "開根號",
                "次方", "次幂",
            ]
        unit_pat = (cfg.get("unit_pattern") if cfg else None) or r'\d+\s*(元|塊|美元|人民幣|日圓)'
        op_pat = (cfg.get("operator_pattern") if cfg else None) or r'\d+[\+\-\*\/\(\)]'
        text_lower = text.lower()
        return (
            any(kw in text_lower for kw in math_keywords) or
            bool(re.search(op_pat, text)) or
            bool(re.search(unit_pat, text))
        )

    async def _call_llm(self, user_message: str) -> str:
        """調用 LLM 提取"""
        from services.angela_llm_service import get_llm_service

        service = self.llm_service or await get_llm_service()
        return await service.generate_text(
            f"{self.MATH_EXTRACTION_PROMPT}\n\n用戶輸入：{user_message}",
            max_tokens=256,
            temperature=0.3,
        )

    def _fallback_extract(self, user_message: str) -> str:
        """Fallback 正則提取"""
        expression = self._fallback_extract_expression(user_message)
        if expression:
            return json.dumps({
                "expression": expression,
                "understanding": "從文本提取的計算式",
                "assumptions": [],
                "confidence": 0.3,
                "answer": None
            })
        return '{"is_math": false}'

    def _fallback_extract_expression(self, text: str) -> Optional[str]:
        """使用正則表達式簡單提取數學表達式"""
        patterns = [
            r"[\d\.]+[\s]*[\+\-\*\/\(\)][\s]*[\d\.]+",
            r"[\d\.]+[\s]*×[\s]*[\d\.]+",
            r"[\d\.]+[\s]*÷[\s]*[\d\.]+",
            r"\([\d\.\s\+\-\*\/\(\)]+\)",
        ]
        for p in patterns:
            m = re.search(p, text.replace("×", "*").replace("÷", "/"))
            if m:
                return m.group().replace("×", "*").replace("÷", "/").replace(" ", "")

        word_expr = self._parse_chinese_word_problem(text)
        if word_expr:
            return word_expr

        return None

    def _parse_chinese_word_problem(self, text: str) -> Optional[str]:
        """解析中文應用題：提取運算式"""
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if len(numbers) < 2:
            return None

        cfg = None
        try:
            from core.config_loader import get_angela_config
            cfg = get_angela_config().get_authority("angela_core", {}).get("math_verifier", {}).get("word_problem_operators", {})
        except Exception as e:
            logger.warning(f"Failed to load word problem operators config: {e}", exc_info=True)

        pow_ops = tuple(cfg.get("pow", [])) if cfg else ("次方", "次幂", "幂")
        for kw in pow_ops:
            if kw in text:
                a, b = numbers[0], numbers[1]
                return f"{a}**{b}"

        subtract_ops = tuple(cfg.get("subtract", [])) if cfg else ("吃了", "吃掉", "減", "-", "剩", "還有", "拿走", "用掉", "花了", "丟掉", "消失", "掉了", "死", "過世", "離開", "不見", "去哪")
        add_ops = tuple(cfg.get("add", [])) if cfg else ("加", "+", "又買", "再拿", "撿到", "找到", "獲得", "生出")
        multiply_ops = tuple(cfg.get("multiply", [])) if cfg else ("倍", "乘", "*", "x")

        for kw in subtract_ops:
            if kw in text:
                idx1 = text.find(numbers[0])
                idx2 = text.find(numbers[1])
                if idx1 > 0 and idx2 > idx1:
                    op1 = numbers[0]
                    op2 = numbers[1]
                    return f"{op1}-{op2}"

        for kw in add_ops:
            if kw in text:
                op1 = numbers[0]
                op2 = numbers[1]
                return f"{op1}+{op2}"

        if any(kw in text for kw in multiply_ops) and len(numbers) >= 2:
            return f"{numbers[0]}*{numbers[1]}"

        return None

    def _safe_float(self, value) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class SpatialEngine:
    """
    [L4-Execution] 原生空間幾何運算引擎 (ground truth)
    封裝 StateMatrix4D 的 evaluate_math_spatially
    """

    def __init__(self, state_matrix=None):
        self.state_matrix = state_matrix
        self._local_cache: Dict[str, float] = {}

    def evaluate(self, expression: str) -> Tuple[float, bool]:
        """
        評估數學表達式，返回 (結果, 是否成功)
        """
        if not expression or not expression.strip():
            return 0.0, False

        if expression in self._local_cache:
            return self._local_cache[expression], True

        try:
            if self.state_matrix:
                result = self.state_matrix.evaluate_math_spatially(expression)
            else:
                result = self._eval_simple(expression)

            self._local_cache[expression] = result
            return result, True
        except Exception as e:
            logger.warning(f"[SpatialEngine] Evaluation failed for '{expression}': {e}", exc_info=True)
            return 0.0, False

    def _get_math_config(self, key: str, default):
        try:
            from core.config_loader import get_angela_config
            return get_angela_config().get_authority("angela_core", {}).get("math_verifier", {}).get(key, default)
        except Exception:
            return default

    def _eval_simple(self, expression: str) -> float:
        """安全的本地計算（不依賴 StateMatrix）"""
        clean = expression.strip().replace(" ", "")
        allowed_chars = self._get_math_config("allowed_chars", "0123456789.+-*/()")
        clean = re.sub(r"[^" + re.escape(allowed_chars) + r"]", "", clean)
        if not clean:
            return 0.0
        allowed = set(allowed_chars)
        if all(c in allowed for c in clean):
            from core.security.secure_eval import safe_eval
            result = safe_eval(clean)
            return float(result.result) if result.success else 0.0
        return 0.0


class MathVerifier:
    """
    [L5-Execution] 數學驗證器 - 雙軌驗證核心
    ==========================================

    流程：
    1. LLM 提取 → 獲取計算式 + 理解 + 置信度
    2. 引擎計算 → 確定性結果 (ground truth)
    3. 比對 → 一致則信任 LLM，不一致則校正
    4. 觸發狀態更新 → epsilon 置信度影響情緒
    """

    def __init__(
        self,
        llm_service=None,
        state_matrix=None,
    ):
        self.extractor = MathExtractor(llm_service)
        self.engine = SpatialEngine(state_matrix)

    async def verify(self, user_message: str, user_name: str = "朋友") -> VerificationResult:
        """
        雙軌驗證主流程
        """
        result = VerificationResult(expression="")

        extraction = await self.extractor.extract(user_message)
        result.extraction = extraction

        if not extraction.is_valid or not extraction.expression:
            return result

        result.expression = extraction.expression

        if extraction.llm_answer is not None:
            result.llm_answer = extraction.llm_answer

        engine_result, engine_ok = self.engine.evaluate(extraction.expression)
        if engine_ok:
            result.engine_answer = engine_result
            result.final_answer = engine_result

        thresh_cfg = self.engine._get_math_config("thresholds", {})
        match_diff = thresh_cfg.get("verification_match_diff", 0.01)
        clarify_conf = thresh_cfg.get("clarification_trigger_confidence", 0.7)

        if extraction.llm_answer is not None and engine_ok:
            diff = abs(extraction.llm_answer - engine_result)
            result.discrepancy = diff
            result.matches = diff < match_diff
        elif engine_ok:
            result.matches = True
            result.discrepancy = 0.0

        if extraction.confidence < clarify_conf and extraction.assumptions:
            result.needs_clarification = True
            result.clarification_question = self._build_clarification(
                extraction.understanding,
                extraction.assumptions,
                user_name
            )

        result.response_text = self._build_response(
            result, extraction, user_name
        )

        return result

    def _build_clarification(
        self, understanding: str, assumptions: List[str], user_name: str
    ) -> str:
        """構建確認問題"""
        if not assumptions:
            return f"{user_name}，我想確認一下：{understanding}，是這樣嗎？"
        unique = list(dict.fromkeys(assumptions))
        if len(unique) <= 2:
            options = "還是".join(unique[:2])
            return f"{user_name}，我不太確定... 是「{unique[0]}」，{options}？"
        return (
            f"{user_name}，這個問題有點複雜。"
            f"我的理解是：{understanding}。"
            f"請問是這個意思嗎？"
        )

    def _build_response(
        self,
        result: VerificationResult,
        extraction: ExtractionResult,
        user_name: str,
    ) -> str:
        """構建最終回應文本"""
        if result.needs_clarification:
            return result.clarification_question

        answer = result.final_answer
        if answer is None:
            return ""

        if result.clarification_question:
            return result.clarification_question

        high_conf = self.engine._get_math_config("thresholds", {}).get("high_confidence_threshold", 0.8)
        if result.matches:
            if extraction.confidence >= high_conf:
                return f"計算結果是 {answer}。"
            else:
                return f"嗯... 我算了一下，應該是 {answer}。"
        else:
            return (
                f"等一下... 我剛才算出來的結果有點不對。"
                f"（再驗證一次）正確答案是 {answer} 才對！"
            )

    def is_math_message(self, message: str) -> bool:
        """快速判斷是否可能是數學問題"""
        return self.extractor._contains_likely_math(message)