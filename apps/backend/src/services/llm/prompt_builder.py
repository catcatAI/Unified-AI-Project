# ANGELA-MATRIX: L3 [β] [A] [L2-L6]
"""Angela prompt construction — standalone module for A3 split"""

import json
import logging
import os
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


def get_formula_summaries() -> str:
    """Compute 5 theoretical formulas and return a formatted string."""
    lines = []
    try:
        from core.hsm_formula_system import HSMFormulaSystem

        lines.append(f"HSM: {HSMFormulaSystem().calculate_hsm():.4f}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"HSM formula unavailable: {e}")
    try:
        from core.life_intensity_formula import LifeIntensityFormula

        lines.append(f"生命強度: {LifeIntensityFormula().calculate_life_intensity():.4f}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"LifeIntensity formula unavailable: {e}")
    try:
        from core.active_cognition_formula import ActiveCognitionFormula

        lines.append(f"活躍認知: {ActiveCognitionFormula().calculate_active_cognition():.4f}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"ActiveCognition formula unavailable: {e}")
    try:
        from core.cdm_dividend_model import CDMCognitiveDividendModel, CognitiveInvestment, CognitiveActivity

        cdm = CDMCognitiveDividendModel()
        inv = CognitiveInvestment(activity_type=CognitiveActivity.INTERACTING, duration_seconds=1.0, intensity=0.5)
        output = cdm.calculate_life_sense_output(inv)
        lines.append(f"CDM 產出: {output.output_amount:.2f} (品質: {output.quality_score:.2f})")
    except (ImportError, AttributeError) as e:
        logger.debug(f"CDM formula unavailable: {e}")
    try:
        from core.non_paradox_existence import NonParadoxExistence

        state = NonParadoxExistence().calculate_coexistence_state("angela_dialogue")
        if state:
            lines.append(f"非悖論共存: 相干性 {state.get('coherence', 0):.2f}")
        else:
            lines.append("非悖論共存: 未激活")
    except (ImportError, AttributeError) as e:
        logger.debug(f"NonParadox formula unavailable: {e}")
    return "\n".join(lines) if lines else ""


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

    history = context.get("history", [])
    for h in history[-2:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

    messages.append({"role": "user", "content": user_message})

    return messages


__all__ = [
    "_get_llm_config",
    "get_biological_state",
    "get_formula_summaries",
    "construct_angela_prompt",
]
