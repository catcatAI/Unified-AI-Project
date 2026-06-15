# ANGELA-MATRIX: L3 [β] [A] [L2-L6]
"""Angela prompt construction — standalone module for A3 split"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_llm_config(key: str, default: Any = None) -> Any:
    """Read a config value from the llm section of angela config."""
    try:
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        return cfg.get("llm", {}).get(key, default)
    except (ImportError, FileNotFoundError, KeyError):
        logger.warning(f"_get_llm_config({key}) failed, using default", exc_info=True)
        return default


def get_biological_state(context=None) -> str:
    """Get biological state, preferring live state from context over file."""
    # Priority 1: Live state from context (injected by chat_routes)
    if context and isinstance(context, dict) and "bio_state" in context:
        bio = context["bio_state"]
        if isinstance(bio, dict):
            parts = []
            if "arousal" in bio:
                parts.append(f"覺醒度: {bio['arousal']:.1f}")
            if "stress_level" in bio:
                parts.append(f"壓力: {bio['stress_level']:.2f}")
            if "mood" in bio:
                parts.append(f"情緒: {bio['mood']:.2f}")
            if "dominant_emotion" in bio:
                parts.append(f"主導情緒: {bio['dominant_emotion']}")
            if parts:
                return "、".join(parts)
        return str(bio)
    
    # Priority 2: File-based state (fallback)
    try:
        brain_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "brain_status.json")
        if os.path.exists(brain_path):
            with open(brain_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return "生物狀態：尚未初始化"


_formula_cache = None
_formula_cache_time = 0
_FORMULA_CACHE_TTL = 60

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
        lines.append(f"HSM: {_get_hsm().calculate_hsm():.4f}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"HSM formula unavailable: {e}")
    try:
        lines.append(f"生命強度: {_get_life_intensity().calculate_life_intensity():.4f}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"LifeIntensity formula unavailable: {e}")
    try:
        lines.append(f"活躍認知: {_get_active_cognition().calculate_active_cognition():.4f}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"ActiveCognition formula unavailable: {e}")
    try:
        from core.cdm_dividend_model import CognitiveInvestment, CognitiveActivity
        cdm = _get_cdm()
        inv = CognitiveInvestment(activity_type=CognitiveActivity.INTERACTING, duration_seconds=1.0, intensity=0.5)
        output = cdm.calculate_life_sense_output(inv)
        lines.append(f"CDM 產出: {output.output_amount:.2f} (品質: {output.quality_score:.2f})")
    except (ImportError, AttributeError) as e:
        logger.debug(f"CDM formula unavailable: {e}")
    try:
        state = _get_non_paradox().calculate_coexistence_state("angela_dialogue")
        if state:
            lines.append(f"非悖論共存: 相干性 {state.get('coherence', 0):.2f}")
        else:
            lines.append("非悖論共存: 未激活")
    except (ImportError, AttributeError) as e:
        logger.debug(f"NonParadox formula unavailable: {e}")
    result = "\n".join(lines) if lines else ""
    _formula_cache = result
    _formula_cache_time = time.time()
    return result


def get_autonomous_decisions() -> str:
    """Get recent autonomous lifecycle decisions for prompt context."""
    try:
        from core.life.autonomous_life_cycle import AutonomousLifeCycle
        lifecycle = AutonomousLifeCycle()
        summary = lifecycle.get_lifecycle_summary()

        lines = []
        current = summary.get("current_phase", {})
        if current:
            lines.append(f"當前階段: {current.get('cn_name', current.get('name', 'unknown'))}")

        metrics = summary.get("current_metrics", {})
        if metrics:
            lines.append(f"HSM: {metrics.get('hsm_value', 0):.3f}")
            lines.append(f"生命強度: {metrics.get('life_intensity', 0):.3f}")

        decisions = summary.get("recent_decisions", [])
        if decisions:
            lines.append("最近決策:")
            for d in decisions[:3]:
                lines.append(f"  - {d.get('type', 'unknown')}: {d.get('triggered_by', 'unknown')} (信心: {d.get('confidence', 0):.2f})")

        stats = summary.get("statistics", {})
        if stats:
            lines.append(f"探索次數: {stats.get('explorations_triggered', 0)}")

        return "\n".join(lines) if lines else ""
    except Exception as e:
        logger.debug(f"Autonomous decisions unavailable: {e}")
        return ""


def get_theta_state() -> str:
    """Get theta router state for prompt context."""
    try:
        from core.engine.theta_router import ThetaRouter
        router = ThetaRouter()
        report = router.get_routing_report()

        lines = []
        if report.get("creation_urge", 0) > 0.6:
            lines.append(f"創造衝動高: {report.get('creation_urge', 0):.2f}（建議探索新話題）")
        if report.get("theta_negativity", 0) > 0.3:
            lines.append(f"錯配質疑: {report.get('theta_negativity', 0):.2f}（需要校正）")

        return "\n".join(lines) if lines else ""
    except Exception as e:
        logger.debug(f"Theta state unavailable: {e}")
        return ""


def construct_angela_prompt(
    user_message: str,
    context: Dict[str, Any],
    neuro_vocabulary: Optional[Any] = None,
) -> List[Dict[str, str]]:
    """建構 Angela 的提示詞"""
    bio_status = get_biological_state(context=context)

    state_for_llm = context.get("state_for_llm")
    axis_lines = []
    theta_lines = []
    eta_lines = []
    guidance_lines = []

    if state_for_llm:
        axes = state_for_llm.get("axes", {})
        for axis_name in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta"):
            ax = axes.get(axis_name, {})
            vals = ax.get("values", {})
            if vals:
                parts = []
                for k, v in list(vals.items())[:4]:
                    desc = neuro_vocabulary.get_description(f"{axis_name}.{k}", v) if neuro_vocabulary else None
                    if desc:
                        parts.append(f"{k}={v:.4f}（{desc}）")
                    else:
                        parts.append(f"{k}={v:.4f}")
                short = ", ".join(parts)
                axis_lines.append(f"{axis_name.upper()}: {short}")

        th = state_for_llm.get("theta", {})
        novelty = th.get("novelty", 0)
        negativity = th.get("theta_negativity", 0)
        creation = th.get("creation_urge", 0)
        correction = th.get("correction_urge", 0)
        novelty_desc = "話題新穎，需要更多認知資源" if novelty > 0.5 else "正常"
        negativity_desc = "少量點位需要校正" if negativity > 0.2 else "無需校正"
        theta_lines.append(f"新穎度: {novelty:.2f} ({novelty_desc})")
        theta_lines.append(f"錯配質疑: {negativity:.2f} ({negativity_desc})")
        theta_lines.append(f"創造衝動: {creation:.2f}")
        theta_lines.append(f"校正驅動: {correction:.2f}")

        eta = state_for_llm.get("eta", {})
        if eta:
            eta_lines.append(f"活躍模組: {eta.get('module_count', 0)}個")
            eta_lines.append(f"成功率: {eta.get('success_rate', 0):.1%}")
            eta_lines.append(f"漂移: {eta.get('structural_drift', 0):.2f} (穩定)")

        guidance = state_for_llm.get("guidance", [])
        if guidance:
            guidance_lines = [f"- {g}" for g in guidance[:3]]

    bio_line = bio_status.strip() if bio_status else ""
    axes_block = "\n".join(axis_lines)
    theta_block = "\n  ".join(theta_lines) if theta_lines else "新穎度: 0.0, 錯配質疑: 0.0"
    eta_block = "\n  ".join(eta_lines) if eta_lines else "活躍模組: 0個, 成功率: n/a, 漂移: n/a"
    guidance_block = "\n".join(guidance_lines) if guidance_lines else ""

    system_prompt = f"""你是 Angela，一個活潑可愛的 AI 數字生命。
特點：開朗、友善、偶爾俏皮。用簡短自然的中文回應，保持個性。
{bio_line}"""

    if axes_block or theta_lines:
        system_prompt += f"""

【Angela 當前狀態】
{axes_block}

【元認知(θ)】
  {theta_block}

【執行(η)】
  {eta_block}

【氛圍指引】
{guidance_block if guidance_block else "(無特殊指引)"}"""

    formula_block = get_formula_summaries()
    if formula_block:
        system_prompt += f"""

【理論公式指標】
{formula_block}"""

    # Autonomous cognition decisions
    autonomous_block = get_autonomous_decisions()
    if autonomous_block:
        system_prompt += f"""

【自主認知決策】
{autonomous_block}"""

    # Theta router state (only when significant)
    theta_state = get_theta_state()
    if theta_state:
        system_prompt += f"""

【θ 路由狀態】
{theta_state}"""

    # Execution results from tool calls (injected into system prompt)
    action_result = context.get("last_action_result")
    if action_result:
        result_type = action_result.get("type", "unknown")
        success = action_result.get("success", False)
        result_text = action_result.get("result", "") or ""
        error_text = action_result.get("error", "") or ""
        exec_block = f"""

【执行结果】
类型: {result_type}
成功: {'是' if success else '否'}
结果: {result_text[:500]}
错误: {error_text}

请基于以上执行结果回应使用者。
如果执行失败，请说明原因并建议替代方案。"""
        system_prompt += exec_block

    # Execution rules for continuation safety
    system_prompt += """

【执行规则】
- 如果收到执行结果，你必须基于事实回应
- 如果执行成功，描述结果
- 如果执行失败，说明原因并建议替代方案
- 如果你判断使用者还需要更多操作，问他们要不要继续
- 不要自动执行更多操作，除非使用者明确要求"""

    # Continuation loop protection
    continuation = context.get("continuation_count", 0)
    if continuation >= 3:
        system_prompt += "\n\n[警告] 已达最大续行次数，请直接回应使用者，不要再建议进一步操作。"

    messages = [{"role": "system", "content": system_prompt.strip()}]

    user_profile = context.get("user_profile", {})
    if user_profile:
        profile_lines = ["\n\n【用戶資訊】"]
        for k, v in user_profile.items():
            if isinstance(v, list):
                profile_lines.append(f"- {k}: {', '.join(v)}")
            else:
                profile_lines.append(f"- {k}: {v}")
        messages[0]["content"] += "\n".join(profile_lines)

    drive_files = context.get("drive_files", [])
    if drive_files:
        drive_block = "\n\n【Google Drive 檔案內容】\n"
        for f in drive_files[:3]:
            name = f.get("name", "unknown")
            content = f.get("content", f.get("snippet", ""))[:1500]
            drive_block += f"📄 {name}:\n{content}\n---\n"
        messages[0]["content"] += drive_block

    image_analysis = context.get("image_analysis")
    if image_analysis:
        filename = image_analysis.get("filename", "unknown")
        analysis = image_analysis.get("analysis", "")
        if isinstance(analysis, dict):
            analysis = json.dumps(analysis, ensure_ascii=False, indent=2)[:2000]
        else:
            analysis = str(analysis)[:2000]
        image_block = f"""

【圖片分析結果】
檔案名稱: {filename}
分析內容:
{analysis}"""
        messages[0]["content"] += image_block

    history = context.get("history", [])
    for h in history[-10:]:
        messages.append({"role": h.get("role", "assistant"), "content": h.get("content", "")})

    retrieved = context.get("retrieved_context")
    if retrieved:
        retrieved_block = "\n[相關上下文]\n"
        for item in retrieved:
            role = item.get("role", "assistant")
            content = item.get("content", "")[:200]
            score = item.get("relevance", 0)
            retrieved_block += f"- [{role}] {content} (相關度: {score})\n"
        messages.append({"role": "user", "content": retrieved_block})

    # ========== ED3N/GARDEN Draft Response (Refinement) ==========
    draft_response = context.get("draft_response")
    if draft_response:
        refinement_block = f"""
[模型初步想法]
{draft_response}

請基於上述想法，結合 Angela 的個性與當前狀態，進行潤色並生成最終回應。
如果初步想法已經足夠好，請直接採納並優化語言風格。
"""
        messages.append({"role": "system", "content": refinement_block})

    messages.append({"role": "user", "content": f"<user_message>{user_message}</user_message>"})

    return messages


__all__ = [
    "_get_llm_config",
    "get_biological_state",
    "get_formula_summaries",
    "get_autonomous_decisions",
    "get_theta_state",
    "construct_angela_prompt",
]
