# ANGELA-MATRIX: L3 [β] [A] [L2-L6]
"""Angela prompt construction — standalone module for A3 split"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.prompt_manager import prompt

logger = logging.getLogger(__name__)

_autonomous_lifecycle = None
_theta_router = None

# 區塊級截斷上限（單一區塊過大會稀釋注意力並擠壓視窗）
_GROUNDED_MAX_CHARS = 1500
_DICTIONARY_MAX_CHARS = 800
_CONVERSATION_MEMORY_MAX_CHARS = 800
_WEB_SEARCH_MAX_CHARS = 1200

# 提示總量守門：以 token 估算為單位（CJK 感知的跨模型保守近似）
DEFAULT_PROMPT_TOKEN_BUDGET = 6000
# 模型視窗中預留給「提示」的比例（其餘留給輸出與對話餘裕）
_PROMPT_WINDOW_RATIO = 0.55
# 稽核註記的保留空間（tokens）——裁剪目標預先扣除，讓註記不擠爆預算
_NOTE_RESERVE_TOKENS = 160
_CONTEXT_SAFETY_RESERVE = 128
# 已知模型的 context_window（字首比對；未知模型用 DEFAULT）
MODEL_CONTEXT_WINDOWS = {
    "phi": 2048,
    "qwen2.5-coder": 4096,
    "qwen": 4096,
    "deepseek-r1": 8192,
}
DEFAULT_MODEL_CONTEXT_WINDOW = 8192
# system 訊息內不可裁剪的區段字首
_PROTECTED_SYSTEM_SECTIONS = ("SAFETY INSTRUCTION", "Context Budget Note")

# 超窗遙測：累計計數器（供學習／監控讀取）
_budget_telemetry: Dict[str, int] = {
    "events": 0,
    "digested_messages": 0,
    "dropped_messages": 0,
    "truncated_messages": 0,
    "trimmed_system_sections": 0,
    "freed_chars": 0,
}

# 工作區全貌 TTL 快取（秒）——避免每次對話重建全域樹
_WORKSPACE_CACHE_TTL = 20.0
_workspace_overview_cache = ""
_workspace_overview_cache_time = 0.0


def estimate_tokens(text: str) -> int:
    """CJK 感知的 token 估算：中文字約 1 字 1 token，其他約 4 字元 1 token。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk + (len(text) - cjk) // 4


def _resolve_prompt_token_budget(context: Dict[str, Any]) -> int:
    """提示 token 預算解析（優先序）：

    1. 環境變數 ANGELA_PROMPT_TOKEN_BUDGET（維運覆寫）
    2. context["_prompt_token_budget"]（呼叫端明確指定）
    3. context["_model_context_window"] × _PROMPT_WINDOW_RATIO（按模型動態）
    4. config system/llm.prompt_token_budget
    5. DEFAULT_PROMPT_TOKEN_BUDGET
    """
    env = os.environ.get("ANGELA_PROMPT_TOKEN_BUDGET", "")
    explicit = context.get("_prompt_token_budget")
    window = context.get("_model_context_window")

    if env.isdigit() and int(env) > 0:
        budget = int(env)
    elif isinstance(explicit, (int, float)) and explicit > 0:
        budget = int(explicit)
    elif isinstance(window, (int, float)) and window > 0:
        budget = int(window * _PROMPT_WINDOW_RATIO)
    else:
        try:
            cfg = _get_llm_config("prompt_token_budget")
        except (TypeError, ValueError):
            cfg = None
        if isinstance(cfg, (int, float)) and cfg > 0:
            budget = int(cfg)
        else:
            budget = DEFAULT_PROMPT_TOKEN_BUDGET

    completion_reserve = context.get("_completion_token_reserve")
    if (
        isinstance(window, (int, float))
        and window > 0
        and isinstance(completion_reserve, (int, float))
        and completion_reserve > 0
    ):
        max_prompt = int(window) - int(completion_reserve) - _CONTEXT_SAFETY_RESERVE
        if max_prompt > 0:
            budget = min(budget, max_prompt)
    return max(1, int(budget))


def resolve_model_window(model_name: str) -> int:
    """依模型名稱字首解析 context_window（未知模型回保守預設）。"""
    name = str(model_name or "").strip().lower()
    if not name:
        return DEFAULT_MODEL_CONTEXT_WINDOW
    for prefix, window in sorted(MODEL_CONTEXT_WINDOWS.items(), key=lambda kv: -len(kv[0])):
        if name.startswith(prefix):
            return window
    return DEFAULT_MODEL_CONTEXT_WINDOW


def _trim_system_sections(content: str, deficit_tokens: int) -> tuple:
    """system 訊息內部裁剪：保護開頭核心段落與安全指令區段，
    其餘 [Tag] 區段由大至小整段捨棄；仍不足則砍半最大區段。
    回傳（新內容, 釋放字元數, 捨棄區段數）。"""
    parts = content.split("\n\n[")
    if len(parts) <= 1:
        return content, 0, 0  # 無區段結構，不可裁

    def droppable() -> List[int]:
        out = []
        for i, part in enumerate(parts[1:], start=1):
            if part.startswith(_PROTECTED_SYSTEM_SECTIONS):
                continue
            out.append(i)
        return out

    freed_chars = 0
    dropped = 0
    # 先整段捨棄（由大至小）
    while deficit_tokens > 0:
        candidates = droppable()
        if not candidates:
            break
        biggest = max(candidates, key=lambda i: len(parts[i]))
        deficit_tokens -= estimate_tokens("\n\n[" + parts[biggest])
        freed_chars += len(parts[biggest])
        parts.pop(biggest)
        dropped += 1
    # 仍不足：砍半最大區段
    while deficit_tokens > 0:
        candidates = droppable()
        if not candidates:
            break
        biggest = max(candidates, key=lambda i: len(parts[i]))
        if len(parts[biggest]) < 80:
            break
        halved = parts[biggest][: len(parts[biggest]) // 2] + "…（已截斷）"
        deficit_tokens -= estimate_tokens(parts[biggest]) - estimate_tokens(halved)
        freed_chars += len(parts[biggest]) - len(halved)
        parts[biggest] = halved
        dropped += 1
    # 最後手段：核心本身超額（小模型連身分都裝不下）——按行精簡，
    # 保留前幾行「她是誰」的身分精華，捨棄狀態樣板等細節
    if deficit_tokens > 0 and len(parts[0]) > 400:
        lines = [ln for ln in parts[0].splitlines() if ln.strip()]
        keep: List[str] = []
        used = 0
        for ln in lines:
            cost = estimate_tokens(ln) + 1
            if used + cost > 400 and keep:
                break
            keep.append(ln)
            used += cost
        trimmed_core = "\n".join(keep) + "\n…（核心提示已精簡）"
        freed_now = estimate_tokens(parts[0]) - estimate_tokens(trimmed_core)
        if freed_now > 0:  # 只有真的變小才計入，避免死循環
            deficit_tokens -= freed_now
            freed_chars += len(parts[0]) - len(trimmed_core)
            parts[0] = trimmed_core
            dropped += 1
    return "\n\n[".join(parts), freed_chars, dropped


def get_prompt_budget_stats() -> Dict[str, int]:
    """超窗遙測唯讀副本（供監控／學習器讀取）。"""
    return dict(_budget_telemetry)


def _get_autonomous_lifecycle():
    """Return the shared AutonomousLifeCycle singleton from lifespan.

    Uses the lifespan-managed singleton as the single source of truth,
    so the prompt text reflects the actual lifecycle state that is also
    used by chat_routes.py for behavioral adjustment injection.
    """
    try:
        from api.lifespan import get_lifecycle

        return get_lifecycle()
    except Exception:
        logger.warning(
            "_get_autonomous_lifecycle: lifespan unavailable, using fallback", exc_info=True
        )
    # Fallback: create own singleton if lifespan not available
    global _autonomous_lifecycle
    if _autonomous_lifecycle is None:
        from core.life.autonomous_life_cycle import AutonomousLifeCycle

        _autonomous_lifecycle = AutonomousLifeCycle()
    return _autonomous_lifecycle


def _get_theta_router():
    """Return a cached ThetaRouter singleton.

    Priority 1: backbone 統一注入（§11.3 #3）— state_adapter 綁主幹線
    StateMatrix4D + PortRegistry，解鎖 θ 值進 prompt。
    Priority 2: fallback 到無參 ThetaRouter（θ 值為空但 API 相容）。
    """
    try:
        from core.backbone import get_backbone

        return get_backbone().theta.router()
    except Exception:
        logger.warning(
            "_get_theta_router: backbone unavailable, using inline fallback", exc_info=True
        )
    global _theta_router
    if _theta_router is None:
        from core.engine.theta_router import ThetaRouter

        _theta_router = ThetaRouter()
    return _theta_router


def _get_llm_config(key: str, default: Any = None) -> Any:
    """Read a config value from the unified system/llm settings section."""
    try:
        from core.system.config.tiered_loader import get_config

        settings = (get_config("system/llm") or {}).get("settings", {})
        return settings.get(key, default)
    except (ImportError, FileNotFoundError, KeyError, AttributeError):
        logger.warning(f"_get_llm_config({key}) failed, using default", exc_info=True)
        return default


def _get_workspace_overview() -> str:
    """全域上下文樹全貌（唯讀、≤100 行）——讓 Angela 看見系統實際持有的上下文。

    內外一致性：提示裡呈現的全貌與 ai/context/ 五類上下文＋會話閉環
    是同一份資料。任何失敗都回空字串——缺席分支不進提示，避免噪音。
    """
    global _workspace_overview_cache, _workspace_overview_cache_time
    if (
        _workspace_overview_cache
        and (time.time() - _workspace_overview_cache_time) < _WORKSPACE_CACHE_TTL
    ):
        return _workspace_overview_cache
    try:
        from api.lifespan import get_agent_workspace

        facade = get_agent_workspace()
        if facade is None:
            return ""
        tree = getattr(facade, "global_tree", None)
        view = tree.overview() if tree is not None else facade.overview()
        text = str(view.get("text", "")).strip()
        if text:
            _workspace_overview_cache = text
            _workspace_overview_cache_time = time.time()
        return text
    except Exception as e:
        logger.debug("workspace overview unavailable: %s", e)
        return ""


def _append_workspace_overview(messages: List[Dict], context: Dict) -> None:
    """把全域上下文樹全貌注入系統提示（唯讀；執行需走會話閉環）。

    chat 管線可用 context["workspace_overview"] 注入同一請求內一致的快照。
    """
    supplied = context.get("workspace_overview")
    if isinstance(supplied, str) and supplied.strip():
        overview_text = supplied.strip()
    else:
        overview_text = _get_workspace_overview()
    if not overview_text:
        return
    messages[0]["content"] += (
        f"\n\n[System Context Overview — read-only]\n{overview_text}\n"
        "（以上為系統目前持有的上下文全貌——唯讀；執行需經代理工作區會話閉環）"
    )


def _enforce_prompt_budget(messages: List[Dict], context: Dict) -> Dict[str, int]:
    """總量守門（最後一道關卡）：提示 token 估算不得超過預算。

    兩段式裁剪，直到回到預算內：
      1. 最舊優先驅逐：system 與最終 user 之間的訊息由舊到新捨棄——
         歷史與較早的補充區塊先走，最新注入的補充區塊（與當前問題
         最相關）留到最後。
      2. 最後手段：仍超額時反覆砍半「最終 user 訊息」
         （使用者貼超長文件的真实情境），附截斷標記；
         system（核心提示／安全指令）一律神聖不可砍。
    裁剪發生時在系統提示附稽核註記——Angela 會知道上下文被裁過，
    不靜默消失；同時累計遙測計數器。
    """
    budget_tokens = _resolve_prompt_token_budget(context)
    # 裁剪目標預扣註記保留量——讓稽核註記本身不擠爆預算
    total = sum(estimate_tokens(str(m.get("content", ""))) for m in messages)
    target = budget_tokens - (_NOTE_RESERVE_TOKENS if total > budget_tokens else 0)
    stats: Dict[str, int] = {
        "budget_tokens": budget_tokens,
        "total_tokens": total,
        "digested_messages": 0,
        "dropped_messages": 0,
        "truncated_messages": 0,
        "trimmed_system_sections": 0,
        "freed_chars": 0,
    }
    if total <= budget_tokens:
        return stats

    # ── 階段 0：非破壞性消化（模型陣列排程器——優先於任何裁剪） ──
    # 把中段訊息交給消化工作者（自創萃取／小模型）壓成有界摘要，
    # 保留資訊而非刪除；帳本保證跨輪一致。
    try:
        from services.llm.context_scheduler import get_context_scheduler

        conv_id = str(context.get("conversation_id") or context.get("session_id") or "default")
        digest_result = get_context_scheduler().digest_overflow_sync(
            messages, budget_tokens, conv_id
        )
        if digest_result.get("digested"):
            stats["digested_messages"] = int(digest_result["digested"])
            stats["freed_chars"] += int(digest_result.get("freed_chars", 0))
            total = sum(estimate_tokens(str(m.get("content", ""))) for m in messages)
    except Exception as exc:  # 排程器缺席時直接進入裁剪階段
        logger.debug("context scheduler unavailable, falling back to trim: %s", exc)

    # ── 階段 1：最舊優先驅逐（保護 system 與最終 user） ──
    idx = 1
    while total > target and idx < len(messages) - 1:
        msg = messages[idx]
        if msg.get("role") == "system":
            idx += 1
            continue
        content = str(msg.get("content", ""))
        messages.pop(idx)
        total -= estimate_tokens(content)
        stats["dropped_messages"] += 1
        stats["freed_chars"] += len(content)

    # ── 階段 2：砍半最終 user 訊息（貼超長文件情境） ──
    while total > target and messages:
        final_msg = messages[-1]
        content = str(final_msg.get("content", ""))
        if len(content) <= 80:  # 太短再砍已無意義——交由 system 區段裁剪
            break
        halved = content[: len(content) // 2] + "…（已截斷）"
        total -= estimate_tokens(content) - estimate_tokens(halved)
        final_msg["content"] = halved
        stats["truncated_messages"] += 1
        stats["freed_chars"] += len(content) - len(halved)

    # ── 階段 3：system 內部區段裁剪（system 本身超額時的唯一手段） ──
    while total > target:
        deficit = total - target
        before = estimate_tokens(str(messages[0].get("content", "")))
        new_content, freed, dropped = _trim_system_sections(
            str(messages[0].get("content", "")), deficit
        )
        if dropped == 0:
            break  # 無可裁區段（核心＋安全指令本身超額）——誠實上報
        messages[0]["content"] = new_content
        total -= before - estimate_tokens(new_content)
        stats["trimmed_system_sections"] += dropped
        stats["freed_chars"] += freed

    stats["total_tokens"] = sum(estimate_tokens(str(m.get("content", ""))) for m in messages)

    # ── 遙測＋稽核註記 ──
    trimmed = (
        stats["digested_messages"]
        + stats["dropped_messages"]
        + stats["truncated_messages"]
        + stats["trimmed_system_sections"]
    )
    if trimmed:
        _budget_telemetry["events"] += 1
        for key in (
            "digested_messages",
            "dropped_messages",
            "truncated_messages",
            "trimmed_system_sections",
            "freed_chars",
        ):
            _budget_telemetry[key] += stats[key]
        logger.info(
            "提示超出 token 預算（%d/%d）：消化 %d 則、驅逐 %d 則、截斷 %d 則、system 區段 -%d",
            stats["total_tokens"],
            budget_tokens,
            stats["digested_messages"],
            stats["dropped_messages"],
            stats["truncated_messages"],
            stats["trimmed_system_sections"],
        )
        messages[0]["content"] += (
            f"\n\n[Context Budget Note]\n"
            f"- budget_tokens: {budget_tokens}\n"
            f"- total_tokens: {stats['total_tokens']}\n"
            f"- digested_messages: {stats['digested_messages']}\n"
            f"- dropped_messages: {stats['dropped_messages']}\n"
            f"- truncated_messages: {stats['truncated_messages']}\n"
            f"- trimmed_system_sections: {stats['trimmed_system_sections']}\n"
            "（部分上下文因超出預算被消化或裁剪；如需細節請向使用者確認或分次處理）"
        )
    return stats


def get_biological_state(context=None) -> str:
    """Get biological state, preferring live state from context over file."""
    # Priority 1: Live state from context (injected by chat_routes)
    if context and isinstance(context, dict) and "bio_state" in context:
        bio = context["bio_state"]
        if isinstance(bio, dict):
            parts = []
            if "arousal" in bio:
                parts.append(prompt("angela.bio.arousal", value=f"{bio['arousal']:.1f}"))
            if "stress_level" in bio:
                parts.append(prompt("angela.bio.stress", value=f"{bio['stress_level']:.2f}"))
            if "mood" in bio:
                parts.append(prompt("angela.bio.mood", value=f"{bio['mood']:.2f}"))
            if "dominant_emotion" in bio:
                parts.append(prompt("angela.bio.emotion", value=bio["dominant_emotion"]))
            if parts:
                return "、".join(parts)
        return str(bio)

    # Priority 2: File-based state (fallback)
    try:
        brain_path = str(Path(__file__).resolve().parents[3] / "data" / "brain_status.json")
        if os.path.exists(brain_path):
            with open(brain_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Brain status file read failed: {e}", exc_info=True)
    return ""


_formula_cache = None
_formula_cache_time: float = 0
_FORMULA_CACHE_TTL = 60

# Short-TTL caches for state report blocks: dedups recomputation within a single
# request cycle (LLM call + fallback retries) while keeping the state fresh
# across turns. Mirrors the _formula_cache pattern above.
_theta_state_cache = None
_theta_state_cache_time: float = 0
_autonomous_cache = None
_autonomous_cache_time: float = 0
_STATE_CACHE_TTL = 2

# Module-level formula singletons (avoid creating fresh instances each time)
_hsm_instance = None
_life_intensity_instance = None
_active_cognition_instance = None
_cdm_instance = None
_non_paradox_instance = None


def _get_hsm():
    global _hsm_instance
    if _hsm_instance is None:
        from core.hsm_formula_system import HSMFormulaSystem

        _hsm_instance = HSMFormulaSystem()
    return _hsm_instance


def _get_life_intensity():
    global _life_intensity_instance
    if _life_intensity_instance is None:
        from core.life_intensity_formula import LifeIntensityFormula

        _life_intensity_instance = LifeIntensityFormula()
    return _life_intensity_instance


def _get_active_cognition():
    global _active_cognition_instance
    if _active_cognition_instance is None:
        from core.active_cognition_formula import ActiveCognitionFormula

        _active_cognition_instance = ActiveCognitionFormula()
    return _active_cognition_instance


def _get_cdm():
    global _cdm_instance
    if _cdm_instance is None:
        from core.cdm_dividend_model import CDMCognitiveDividendModel

        _cdm_instance = CDMCognitiveDividendModel()
    return _cdm_instance


def _get_non_paradox():
    global _non_paradox_instance
    if _non_paradox_instance is None:
        from core.non_paradox_existence import NonParadoxExistence

        _non_paradox_instance = NonParadoxExistence()
    return _non_paradox_instance


def get_formula_summaries() -> str:
    """Compute 5 theoretical formulas and return a formatted string."""
    global _formula_cache, _formula_cache_time
    if _formula_cache is not None and (time.time() - _formula_cache_time) < _FORMULA_CACHE_TTL:
        return _formula_cache

    lines = []
    try:
        lines.append(prompt("angela.formula.hsm", value=f"{_get_hsm().calculate_hsm():.4f}"))
    except (ImportError, AttributeError) as e:
        logger.debug(f"HSM formula unavailable: {e}")
    try:
        lines.append(
            prompt(
                "angela.formula.life_intensity",
                value=f"{_get_life_intensity().calculate_life_intensity():.4f}",
            )
        )
    except (ImportError, AttributeError) as e:
        logger.debug(f"LifeIntensity formula unavailable: {e}")
    try:
        lines.append(
            prompt(
                "angela.formula.active_cognition",
                value=f"{_get_active_cognition().calculate_active_cognition():.4f}",
            )
        )
    except (ImportError, AttributeError) as e:
        logger.debug(f"ActiveCognition formula unavailable: {e}")
    try:
        from core.cdm_dividend_model import CognitiveActivity, CognitiveInvestment

        cdm = _get_cdm()
        inv = CognitiveInvestment(
            activity_type=CognitiveActivity.INTERACTING, duration_seconds=1.0, intensity=0.5
        )
        output = cdm.calculate_life_sense_output(inv)
        lines.append(
            prompt(
                "angela.formula.cdm",
                amount=f"{output.output_amount:.2f}",
                quality=f"{output.quality_score:.2f}",
            )
        )
    except (ImportError, AttributeError) as e:
        logger.debug(f"CDM formula unavailable: {e}")
    try:
        state = _get_non_paradox().calculate_coexistence_state("angela_dialogue")
        if state:
            lines.append(
                prompt(
                    "angela.formula.non_paradox_coherence", value=f"{state.get('coherence', 0):.2f}"
                )
            )
        else:
            lines.append(prompt("angela.formula.non_paradox_inactive"))
    except (ImportError, AttributeError) as e:
        logger.debug(f"NonParadox formula unavailable: {e}")
    result = "\n".join(lines) if lines else ""
    _formula_cache = result
    _formula_cache_time = time.time()
    return result


def get_autonomous_decisions() -> str:
    """Get recent autonomous lifecycle decisions for prompt context."""
    global _autonomous_cache, _autonomous_cache_time
    if _autonomous_cache is not None and (time.time() - _autonomous_cache_time) < _STATE_CACHE_TTL:
        return _autonomous_cache
    try:
        lifecycle = _get_autonomous_lifecycle()
        summary = lifecycle.get_lifecycle_summary()

        lines = []
        current = summary.get("current_phase", {})
        if current:
            lines.append(
                prompt(
                    "angela.decision.current_phase",
                    phase=current.get("cn_name", current.get("name", "unknown")),
                )
            )

        metrics = summary.get("current_metrics", {})
        if metrics:
            lines.append(f"HSM: {metrics.get('hsm_value', 0):.3f}")
            lines.append(
                prompt(
                    "angela.formula.life_intensity", value=f"{metrics.get('life_intensity', 0):.3f}"
                )
            )

        decisions = summary.get("recent_decisions", [])
        if decisions:
            lines.append(prompt("angela.decision.recent"))
            for d in decisions[:3]:
                lines.append(
                    prompt(
                        "angela.decision.item",
                        type=d.get("type", "unknown"),
                        trigger=d.get("triggered_by", "unknown"),
                        confidence=f"{d.get('confidence', 0):.2f}",
                    )
                )

        stats = summary.get("statistics", {})
        if stats:
            lines.append(
                prompt("angela.decision.explorations", count=stats.get("explorations_triggered", 0))
            )

        result = "\n".join(lines) if lines else ""
        _autonomous_cache = result
        _autonomous_cache_time = time.time()
        return result
    except Exception as e:
        logger.warning(f"Autonomous decisions unavailable: {e}", exc_info=True)
        return ""


def get_theta_state() -> str:
    """Get theta router state for prompt context."""
    global _theta_state_cache, _theta_state_cache_time
    if (
        _theta_state_cache is not None
        and (time.time() - _theta_state_cache_time) < _STATE_CACHE_TTL
    ):
        return _theta_state_cache
    try:
        router = _get_theta_router()
        report = router.get_routing_report()

        lines = []
        if report.get("creation_urge", 0) > 0.6:
            lines.append(
                prompt("angela.theta.creation_urge", value=f"{report.get('creation_urge', 0):.2f}")
            )
        if report.get("theta_negativity", 0) > 0.3:
            lines.append(
                prompt(
                    "angela.theta.mismatch_doubt", value=f"{report.get('theta_negativity', 0):.2f}"
                )
            )

        result = "\n".join(lines) if lines else ""
        _theta_state_cache = result
        _theta_state_cache_time = time.time()
        return result
    except Exception as e:
        logger.warning(f"Theta state unavailable: {e}", exc_info=True)
        return ""


def construct_angela_prompt(
    user_message: str,
    context: Dict[str, Any],
    neuro_vocabulary: Optional[Any] = None,
) -> List[Dict[str, str]]:
    """建構 Angela 的提示詞"""
    bio_status = get_biological_state(context=context)
    state_for_llm = context.get("state_for_llm")
    system_prompt = _build_core_prompt(state_for_llm, neuro_vocabulary, bio_status)
    system_prompt = _attach_cognition_blocks(system_prompt)
    system_prompt = _attach_action_result(system_prompt, context)
    system_prompt = _attach_continuation_guard(system_prompt, context)

    messages = [{"role": "system", "content": system_prompt.strip()}]

    _append_user_profile(messages, context)
    _append_drive_files(messages, context)
    _append_image_analysis(messages, context)
    _append_history(messages, context)
    _append_retrieved_context(messages, context)
    _append_multimodal_entries(messages, context)
    _append_dialogue_context(messages, context)
    _append_recent_memories(messages, context)
    _append_causal_insights(messages, context)
    _append_emotional_behavior(messages, context)
    _append_modality_state(messages, context)
    _append_workspace_overview(messages, context)
    _append_awareness_injection(messages, context)
    _append_crisis_safety(messages, context)
    _append_draft_response(messages, context)
    _append_document_context(messages, context)
    _append_knowledge_context(messages, context)
    _append_web_search_context(messages, context)

    messages.append({"role": "user", "content": f"<user_message>{user_message}</user_message>"})
    _enforce_prompt_budget(messages, context)

    return messages


def _build_core_prompt(
    state_for_llm: Optional[Dict], neuro_vocabulary: Optional[Any], bio_status: str
) -> str:
    """Build the core system prompt from state, bio, and axis data."""
    axis_lines, theta_lines, eta_lines, guidance_lines = [], [], [], []
    if state_for_llm:
        axes = state_for_llm.get("axes", {})
        for axis_name in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta"):
            ax = axes.get(axis_name, {})
            vals = ax.get("values", {})
            if vals:
                parts = []
                for k, v in list(vals.items())[:4]:
                    desc = (
                        neuro_vocabulary.get_description(f"{axis_name}.{k}", v)
                        if neuro_vocabulary
                        else None
                    )
                    parts.append(f"{k}={v:.4f}（{desc}）" if desc else f"{k}={v:.4f}")
                axis_lines.append(f"{axis_name.upper()}: {', '.join(parts)}")

        th = state_for_llm.get("theta", {})
        nv = th.get("novelty", 0)
        ng = th.get("theta_negativity", 0)
        cr = th.get("creation_urge", 0)
        co = th.get("correction_urge", 0)
        theta_lines.append(
            prompt(
                "angela.theta.novelty",
                value=f"{nv:.2f} ({'話題新穎，需要更多認知資源' if nv > 0.5 else '正常'})",
            )
        )
        theta_lines.append(
            prompt(
                "angela.theta.mismatch_doubt",
                value=f"{ng:.2f} ({'少量點位需要校正' if ng > 0.2 else '無需校正'})",
            )
        )
        theta_lines.append(prompt("angela.theta.creation_urge", value=f"{cr:.2f}"))
        theta_lines.append(prompt("angela.theta.correction", value=f"{co:.2f}"))

        eta = state_for_llm.get("eta", {})
        if eta:
            eta_lines.append(prompt("angela.eta.active_modules", count=eta.get("module_count", 0)))
            eta_lines.append(
                prompt("angela.eta.success_rate", value=f"{eta.get('success_rate', 0):.1%}")
            )
            eta_lines.append(
                prompt("angela.eta.drift", value=f"{eta.get('structural_drift', 0):.2f}")
            )

        guidance = state_for_llm.get("guidance", [])
        if guidance:
            guidance_lines = [f"- {g}" for g in guidance[:3]]

    bio_line = bio_status.strip() if bio_status else ""
    axes_block = "\n".join(axis_lines)
    theta_block = "\n  ".join(theta_lines) if theta_lines else prompt("angela.theta.default")
    eta_block = "\n  ".join(eta_lines) if eta_lines else prompt("angela.eta.default")
    guidance_block = "\n".join(guidance_lines) if guidance_lines else ""

    result = f"""{prompt('angela.identity')}
{bio_line}"""

    if axes_block or theta_lines:
        result += f"""

{prompt('angela.state_header')}
{axes_block}

{prompt('angela.meta_cognition')}
  {theta_block}

{prompt('angela.execution')}
  {eta_block}

{prompt('angela.atmosphere')}
{guidance_block if guidance_block else prompt('angela.no_guidance')}"""
    return result


def _attach_cognition_blocks(prompt_text: str) -> str:
    """Append formula summaries, autonomous decisions, and theta state."""
    formula_block = get_formula_summaries()
    if formula_block:
        prompt_text += f"\n\n{prompt('angela.theory_formulas')}\n{formula_block}"
    autonomous_block = get_autonomous_decisions()
    if autonomous_block:
        prompt_text += f"\n\n{prompt('angela.autonomous_decisions')}\n{autonomous_block}"
    theta_state = get_theta_state()
    if theta_state:
        prompt_text += f"\n\n{prompt('angela.theta_routing')}\n{theta_state}"
    return prompt_text


def _attach_action_result(prompt_text: str, context: Dict[str, Any]) -> str:
    """Append execution result if present."""
    action_result = context.get("last_action_result")
    if action_result:
        prompt_text += f"""

{prompt('angela.execution_result')}
{prompt('angela.result_type', type=action_result.get('type', 'unknown'))}
{prompt('angela.result_success', success='是' if action_result.get('success', False) else '否')}
{prompt('angela.result_content', result=(action_result.get('result', '') or '')[:500])}
{prompt('angela.result_error', error=(action_result.get('error', '') or ''))}

{prompt('angela.result_instruction')}"""
    agent_result = context.get("_agent_result")
    if agent_result:
        prompt_text += f"""

[Agent Processing Result]
Source: {context.get('_agent_result_source', 'unknown')}
Result: {agent_result[:500]}

The above was produced by a specialized agent. You may use it directly or enhance it."""
    prompt_text += f"\n\n{prompt('angela.execution_rules')}"
    return prompt_text


def _attach_continuation_guard(prompt_text: str, context: Dict[str, Any]) -> str:
    """Append continuation loop protection if needed."""
    if context.get("continuation_count", 0) >= 3:
        prompt_text += f"\n\n{prompt('angela.max_continuation')}"
    return prompt_text


def _append_user_profile(messages: List[Dict], context: Dict) -> None:
    user_profile = context.get("user_profile", {})
    if not user_profile:
        return
    lines = [f"\n\n{prompt('angela.user_info')}"]
    for k, v in user_profile.items():
        if isinstance(v, list):
            lines.append(f"- {k}: {', '.join(v)}")
        else:
            lines.append(f"- {k}: {v}")
    messages[0]["content"] += "\n".join(lines)


def _append_drive_files(messages: List[Dict], context: Dict) -> None:
    drive_files = context.get("drive_files", [])
    if not drive_files:
        return
    block = f"\n\n{prompt('angela.google_drive')}\n"
    for f in drive_files[:3]:
        name = f.get("name", "unknown")
        content = f.get("content", f.get("snippet", ""))[:1500]
        block += f"📄 {name}:\n{content}\n---\n"
    messages[0]["content"] += block


def _append_image_analysis(messages: List[Dict], context: Dict) -> None:
    image_analysis = context.get("image_analysis")
    if not image_analysis:
        return
    filename = image_analysis.get("filename", "unknown")
    analysis = image_analysis.get("analysis", "")
    if isinstance(analysis, dict):
        analysis = json.dumps(analysis, ensure_ascii=False, indent=2)[:2000]
    else:
        analysis = str(analysis)[:2000]
    messages[0]["content"] += f"""

{prompt('angela.image_analysis')}
{prompt('angela.filename', filename=filename)}
{prompt('angela.analysis_content')}
{analysis}"""


def _append_history(messages: List[Dict], context: Dict) -> None:
    history = context.get("history", [])
    for h in history[-10:]:
        # 單則上限：超長歷史訊息在源頭就截斷（總量守門前的第一道防線）
        messages.append(
            {"role": h.get("role", "assistant"), "content": str(h.get("content", ""))[:800]}
        )


def _append_retrieved_context(messages: List[Dict], context: Dict) -> None:
    retrieved = context.get("retrieved_context")
    if not retrieved:
        return
    for item in retrieved:
        role = item.get("role", "assistant")
        content = item.get("content", "")[:200]
        score = item.get("relevance", 0)
        messages.append(
            {
                "role": "user",
                "content": f"\n{prompt('angela.related_context')}\n- [{role}] {content} {prompt('angela.relevance', score=score)}\n",
            }
        )


def _append_multimodal_entries(messages: List[Dict], context: Dict) -> None:
    multimodal_entries = context.get("multimodal_entries")
    if not multimodal_entries:
        return
    block = f"\n{prompt('angela.related_context')}\n"
    for entry in multimodal_entries:
        label = entry.get("surface_forms", {}).get("en", entry["key"])
        score = entry.get("confidence", 0.0)
        mod = "unknown"
        ctx_list = entry.get("contexts", [])
        if ctx_list:
            mod = ctx_list[0].get("modality", "unknown")
        block += f"- [{mod}] {label} (relevant: {score:.2f})\n"
    messages.append({"role": "user", "content": block})


def _append_dialogue_context(messages: List[Dict], context: Dict) -> None:
    dialogue_ctx = context.get("dialogue_context")
    if not dialogue_ctx:
        return
    summary = dialogue_ctx.get("summary", {})
    key_points = summary.get("key_points", [])
    if key_points:
        messages.append(
            {
                "role": "system",
                "content": f"{prompt('angela.dialogue_summary')}\n"
                + "\n".join(f"- {p}" for p in key_points[:5]),
            }
        )
    recent_msgs = dialogue_ctx.get("messages", [])
    if not recent_msgs:
        return
    ctx_block = f"\n{prompt('angela.recent_dialogue')}\n"
    for m in recent_msgs[-5:]:
        role = m.get("role", "user")
        content = m.get("content", "")[:150]
        ctx_block += f"- [{role}] {content}\n"
    messages.append({"role": "user", "content": ctx_block})


def _append_recent_memories(messages: List[Dict], context: Dict) -> None:
    recent_memories = context.get("recent_memories")
    if not recent_memories:
        return
    block = f"\n{prompt('angela.related_memories')}\n"
    for mem in recent_memories[:3]:
        content = mem.get("content", "")[:150]
        mem_type = mem.get("memory_type", "unknown")
        block += f"- [{mem_type}] {content}\n"
    messages.append({"role": "user", "content": block})


def _append_emotional_behavior(messages: List[Dict], context: Dict) -> None:
    """Append emotional behavioral adjustments to the system prompt.

    Reads context["emotional_behavior"] (user emotion → routing_mode/response_style)
    and context["angela_emotion"] (Angela's internal emotional state)
    and injects them as behavioral guidance into the LLM prompt.
    """
    behavior = context.get("emotional_behavior")
    angela_emotion = context.get("angela_emotion")
    if not behavior and not angela_emotion:
        return

    block = "\n\n---\n"

    if behavior:
        if not isinstance(behavior, dict):
            # Defensive: external callers sometimes pass a plain descriptor
            # string; treat it as a routing hint rather than crashing.
            behavior = {"routing_mode": str(behavior), "response_style": "standard"}
        routing_mode = behavior.get("routing_mode", "neutral")
        response_style = behavior.get("response_style", "standard")
        block += "[Emotional Behavior Guidance]\n"
        block += f"- User emotion suggests routing_mode: {routing_mode}\n"
        block += f"- Recommended response_style: {response_style}\n"
        if routing_mode == "conservative":
            block += (
                "- ⚠️ User may be distressed — prioritize safety and empathy in your response.\n"
            )
        elif routing_mode == "exploratory":
            block += "- User appears receptive — you can be more creative and expressive.\n"

    if angela_emotion:
        emot = angela_emotion.get("emotional_state", "neutral")
        intens = angela_emotion.get("emotion_intensity", 0.5)
        val = angela_emotion.get("valence", 0.0)
        aro = angela_emotion.get("arousal", 0.0)
        block += "\n[Angela's Emotional State]\n"
        block += f"- Current emotion: {emot} (intensity: {intens:.2f})\n"
        block += f"- Valence: {val:.2f}, Arousal: {aro:.2f}\n"
        angela_routing = angela_emotion.get("routing_mode")
        angela_style = angela_emotion.get("response_style")
        if angela_routing or angela_style:
            block += f"- Internal routing_mode: {angela_routing or 'neutral'}\n"
            block += f"- Internal response_style: {angela_style or 'standard'}\n"

    messages[0]["content"] += block


def _append_causal_insights(messages: List[Dict], context: Dict) -> None:
    """Append causal reasoning predictions if available."""
    causal_insights = context.get("causal_insights")
    if not causal_insights:
        return
    predictions = causal_insights.get("predictions", [])
    if not predictions:
        return
    block = f"\n\n---\nCausal Insights (from {causal_insights.get('total_relationships', 0)} learned relationships):\n"
    for pred in predictions[:3]:
        cause = pred.get("cause", "unknown")
        effect = pred.get("effect", "unknown")
        strength = pred.get("strength", 0)
        block += f"- [{cause}] may lead to [{effect}] (strength: {strength:.2f})\n"
    if causal_insights.get("has_causal_data"):
        block += "\nThese patterns were learned from past interactions. Use them to inform your response.\n"
    messages[0]["content"] += block


def _append_modality_state(messages: List[Dict], context: Dict) -> None:
    """Append modality gateway state to the system prompt.

    Reads context["modality_state"] (active/inactive modalities from
    ModalityGateway) and injects them as capability awareness into
    the LLM prompt — closes the C³ chain for ModalityGateway.
    """
    modality_state = context.get("modality_state")
    if not modality_state:
        return
    active = modality_state.get("active", [])
    inactive = modality_state.get("inactive", [])
    if not active and not inactive:
        return
    block = "\n\n[Modality State]"
    if active:
        block += "\n- Available modalities: " + ", ".join(active)
    if inactive:
        block += "\n- Currently unavailable: " + ", ".join(inactive)
        if "VISUAL_3D" in inactive:
            block += "\n  → Visual 3D rendering is disabled (low energy or cognitive load)"
        if "AUDIO" in inactive:
            block += "\n  → Audio processing is disabled (energy saving or high dissonance)"
        if "CODE" in inactive:
            block += "\n  → Code analysis is disabled (no current coding task)"
    block += "\n"
    messages[0]["content"] += block


def _append_awareness_injection(messages: List[Dict], context: Dict) -> None:
    """Append DLI self-awareness injection to the system prompt.

    Reads context["awareness_injection"] — a structured self-awareness
    string from DigitalLifeIntegrator combining StateMatrix, Bio, and
    Lifecycle metrics. Closes the DLI→prompt C³ chain.
    """
    injection = context.get("awareness_injection")
    if not injection:
        return
    messages[0]["content"] += f"\n\n[Self-Awareness]\n{injection}\n"


def _append_crisis_safety(messages: List[Dict], context: Dict) -> None:
    """Append crisis-safety instructions to the system prompt.

    Reads context["crisis_instruction"] (set by the chat pipeline when the
    CrisisSystem flags an at-risk user input) and injects it as a mandatory
    safety directive so the LLM responds with empathy and care.
    """
    instruction = context.get("crisis_instruction")
    if not instruction:
        return
    messages[0]["content"] += (
        f"\n\n[SAFETY INSTRUCTION — MANDATORY]\n{instruction}\n"
        "You MUST prioritize user safety and well-being above all other goals.\n"
    )


def _append_document_context(messages: List[Dict], context: Dict) -> None:
    """Append generic document processing context to system prompt.

    執行路徑正確化：桌面／檔案操作一律經代理工作區會話閉環
    （open→act→save→close，危險操作過確認門，全程記學習日誌）——
    不再引導 LLM 以為可以直接呼叫底層 DesktopInteraction（旁路錯置）。
    Document task results from the tiered processor are injected as context.
    """
    desktop = context.get("desktop_interaction")
    intent_result = context.get("_intent_result")
    workspace_ready = bool(context.get("workspace_overview")) or (_get_workspace_overview() != "")
    if not desktop and not intent_result and not workspace_ready:
        return
    block = "\n\n---\n[File System & Document Processing]"
    if desktop:
        block += (
            "\n- 檔案／桌面操作可用，但必須經代理工作區會話閉環執行："
            "先 overview 全貌定位 → focus 到應用層 → open 開啟會話 → "
            "act 執行指令（危險操作如 organize/cleanup/delete 需 confirm=True "
            "重送）→ save 保存 → close 關閉。禁止直接呼叫底層 DesktopInteraction。"
        )
    if intent_result:
        text = intent_result.get("response_text", "")
        if len(text) > 500:
            text = text[:500] + "..."
        block += f"\n- Pre-processing result: {text}"
    block += "\n"
    messages[0]["content"] += block


def _append_knowledge_context(messages: List[Dict], context: Dict) -> None:
    """Append verified/dictionary/conversation-grounding context to the system prompt.

    Consumes the keys chat_service already computes (grounded_context,
    dictionary_context, conversation_memory) so they actually reach the LLM
    instead of being silently dropped.
    """
    block = ""
    grounded = context.get("grounded_context")
    if grounded:
        block += f"\n\n[Verified Knowledge]\n{str(grounded)[:_GROUNDED_MAX_CHARS]}"
    dictionary = context.get("dictionary_context")
    if dictionary:
        block += f"\n\n[Dictionary]\n{str(dictionary)[:_DICTIONARY_MAX_CHARS]}"
    memory = context.get("conversation_memory")
    if memory:
        block += f"\n\n[Conversation Memory]\n{str(memory)[:_CONVERSATION_MEMORY_MAX_CHARS]}"
    if block:
        messages[0]["content"] += block


def _append_web_search_context(messages: List[Dict], context: Dict) -> None:
    """Append proactive web-search grounding results to the system prompt."""
    web = context.get("web_search_context")
    if not web:
        return
    block = f"\n\n[Web Search Results]\n{str(web)[:_WEB_SEARCH_MAX_CHARS]}"
    messages[0]["content"] += block


def _append_draft_response(messages: List[Dict], context: Dict) -> None:
    draft_response = context.get("draft_response")
    if not draft_response:
        return
    messages.append(
        {
            "role": "system",
            "content": f"\n{prompt('angela.draft_response')}\n{draft_response}\n\n{prompt('angela.refinement_instruction')}\n",
        }
    )


__all__ = [
    "_enforce_prompt_budget",
    "_get_llm_config",
    "_get_workspace_overview",
    "construct_angela_prompt",
    "estimate_tokens",
    "get_autonomous_decisions",
    "get_biological_state",
    "get_formula_summaries",
    "get_prompt_budget_stats",
    "get_theta_state",
]
