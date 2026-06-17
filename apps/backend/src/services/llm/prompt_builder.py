# ANGELA-MATRIX: L3 [β] [A] [L2-L6]
"""Angela prompt construction — standalone module for A3 split"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.backend.src.core.prompt_manager import prompt, get_prompt_manager

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
                parts.append(prompt("angela.bio.arousal", value=f"{bio['arousal']:.1f}"))
            if "stress_level" in bio:
                parts.append(prompt("angela.bio.stress", value=f"{bio['stress_level']:.2f}"))
            if "mood" in bio:
                parts.append(prompt("angela.bio.mood", value=f"{bio['mood']:.2f}"))
            if "dominant_emotion" in bio:
                parts.append(prompt("angela.bio.emotion", value=bio['dominant_emotion']))
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
    return prompt("angela.bio.uninitialized")


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
        lines.append(prompt("angela.formula.hsm", value=f"{_get_hsm().calculate_hsm():.4f}"))
    except (ImportError, AttributeError) as e:
        logger.debug(f"HSM formula unavailable: {e}")
    try:
        lines.append(prompt("angela.formula.life_intensity", value=f"{_get_life_intensity().calculate_life_intensity():.4f}"))
    except (ImportError, AttributeError) as e:
        logger.debug(f"LifeIntensity formula unavailable: {e}")
    try:
        lines.append(prompt("angela.formula.active_cognition", value=f"{_get_active_cognition().calculate_active_cognition():.4f}"))
    except (ImportError, AttributeError) as e:
        logger.debug(f"ActiveCognition formula unavailable: {e}")
    try:
        from core.cdm_dividend_model import CognitiveInvestment, CognitiveActivity
        cdm = _get_cdm()
        inv = CognitiveInvestment(activity_type=CognitiveActivity.INTERACTING, duration_seconds=1.0, intensity=0.5)
        output = cdm.calculate_life_sense_output(inv)
        lines.append(prompt("angela.formula.cdm", amount=f"{output.output_amount:.2f}", quality=f"{output.quality_score:.2f}"))
    except (ImportError, AttributeError) as e:
        logger.debug(f"CDM formula unavailable: {e}")
    try:
        state = _get_non_paradox().calculate_coexistence_state("angela_dialogue")
        if state:
            lines.append(prompt("angela.formula.non_paradox_coherence", value=f"{state.get('coherence', 0):.2f}"))
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
    try:
        from core.life.autonomous_life_cycle import AutonomousLifeCycle
        lifecycle = AutonomousLifeCycle()
        summary = lifecycle.get_lifecycle_summary()

        lines = []
        current = summary.get("current_phase", {})
        if current:
            lines.append(prompt("angela.decision.current_phase", phase=current.get('cn_name', current.get('name', 'unknown'))))

        metrics = summary.get("current_metrics", {})
        if metrics:
            lines.append(f"HSM: {metrics.get('hsm_value', 0):.3f}")
            lines.append(prompt("angela.formula.life_intensity", value=f"{metrics.get('life_intensity', 0):.3f}"))

        decisions = summary.get("recent_decisions", [])
        if decisions:
            lines.append(prompt("angela.decision.recent"))
            for d in decisions[:3]:
                lines.append(prompt("angela.decision.item", type=d.get('type', 'unknown'), trigger=d.get('triggered_by', 'unknown'), confidence=f"{d.get('confidence', 0):.2f}"))

        stats = summary.get("statistics", {})
        if stats:
            lines.append(prompt("angela.decision.explorations", count=stats.get('explorations_triggered', 0)))

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
            lines.append(prompt("angela.theta.creation_urge", value=f"{report.get('creation_urge', 0):.2f}"))
        if report.get("theta_negativity", 0) > 0.3:
            lines.append(prompt("angela.theta.mismatch_doubt", value=f"{report.get('theta_negativity', 0):.2f}"))

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
        theta_lines.append(prompt("angela.theta.novelty", value=f"{novelty:.2f} ({novelty_desc})"))
        theta_lines.append(prompt("angela.theta.mismatch_doubt", value=f"{negativity:.2f} ({negativity_desc})"))
        theta_lines.append(prompt("angela.theta.creation_urge", value=f"{creation:.2f}"))
        theta_lines.append(prompt("angela.theta.correction", value=f"{correction:.2f}"))

        eta = state_for_llm.get("eta", {})
        if eta:
            eta_lines.append(prompt("angela.eta.active_modules", count=eta.get('module_count', 0)))
            eta_lines.append(prompt("angela.eta.success_rate", value=f"{eta.get('success_rate', 0):.1%}"))
            eta_lines.append(prompt("angela.eta.drift", value=f"{eta.get('structural_drift', 0):.2f}"))

        guidance = state_for_llm.get("guidance", [])
        if guidance:
            guidance_lines = [f"- {g}" for g in guidance[:3]]

    bio_line = bio_status.strip() if bio_status else ""
    axes_block = "\n".join(axis_lines)
    theta_block = "\n  ".join(theta_lines) if theta_lines else prompt("angela.theta.default")
    eta_block = "\n  ".join(eta_lines) if eta_lines else prompt("angela.eta.default")
    guidance_block = "\n".join(guidance_lines) if guidance_lines else ""

    system_prompt = f"""{prompt('angela.identity')}
{bio_line}"""

    if axes_block or theta_lines:
        system_prompt += f"""

{prompt('angela.state_header')}
{axes_block}

{prompt('angela.meta_cognition')}
  {theta_block}

{prompt('angela.execution')}
  {eta_block}

{prompt('angela.atmosphere')}
{guidance_block if guidance_block else prompt('angela.no_guidance')}"""

    formula_block = get_formula_summaries()
    if formula_block:
        system_prompt += f"""

{prompt('angela.theory_formulas')}
{formula_block}"""

    # Autonomous cognition decisions
    autonomous_block = get_autonomous_decisions()
    if autonomous_block:
        system_prompt += f"""

{prompt('angela.autonomous_decisions')}
{autonomous_block}"""

    # Theta router state (only when significant)
    theta_state = get_theta_state()
    if theta_state:
        system_prompt += f"""

{prompt('angela.theta_routing')}
{theta_state}"""

    # Execution results from tool calls (injected into system prompt)
    action_result = context.get("last_action_result")
    if action_result:
        result_type = action_result.get("type", "unknown")
        success = action_result.get("success", False)
        result_text = action_result.get("result", "") or ""
        error_text = action_result.get("error", "") or ""
        exec_block = f"""

{prompt('angela.execution_result')}
{prompt('angela.result_type', type=result_type)}
{prompt('angela.result_success', success='是' if success else '否')}
{prompt('angela.result_content', result=result_text[:500])}
{prompt('angela.result_error', error=error_text)}

{prompt('angela.result_instruction')}"""
        system_prompt += exec_block

    # Execution rules for continuation safety
    system_prompt += f"""

{prompt('angela.execution_rules')}"""

    # Continuation loop protection
    continuation = context.get("continuation_count", 0)
    if continuation >= 3:
        system_prompt += f"\n\n{prompt('angela.max_continuation')}"

    messages = [{"role": "system", "content": system_prompt.strip()}]

    user_profile = context.get("user_profile", {})
    if user_profile:
        profile_lines = [f"\n\n{prompt('angela.user_info')}"]
        for k, v in user_profile.items():
            if isinstance(v, list):
                profile_lines.append(f"- {k}: {', '.join(v)}")
            else:
                profile_lines.append(f"- {k}: {v}")
        messages[0]["content"] += "\n".join(profile_lines)

    drive_files = context.get("drive_files", [])
    if drive_files:
        drive_block = f"\n\n{prompt('angela.google_drive')}\n"
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

{prompt('angela.image_analysis')}
{prompt('angela.filename', filename=filename)}
{prompt('angela.analysis_content')}
{analysis}"""
        messages[0]["content"] += image_block

    history = context.get("history", [])
    for h in history[-10:]:
        messages.append({"role": h.get("role", "assistant"), "content": h.get("content", "")})

    retrieved = context.get("retrieved_context")
    if retrieved:
        retrieved_block = f"\n{prompt('angela.related_context')}\n"
        for item in retrieved:
            role = item.get("role", "assistant")
            content = item.get("content", "")[:200]
            score = item.get("relevance", 0)
            retrieved_block += f"- [{role}] {content} {prompt('angela.relevance', score=score)}\n"
        messages.append({"role": "user", "content": retrieved_block})

    # ========== Dialogue Context (Cross-turn) ==========
    dialogue_ctx = context.get("dialogue_context")
    if dialogue_ctx:
        summary = dialogue_ctx.get("summary", {})
        key_points = summary.get("key_points", [])
        if key_points:
            points_str = "\n".join(f"- {p}" for p in key_points[:5])
            messages.append({"role": "system", "content": f"{prompt('angela.dialogue_summary')}\n{points_str}"})
        recent_msgs = dialogue_ctx.get("messages", [])
        if recent_msgs:
            ctx_block = f"\n{prompt('angela.recent_dialogue')}\n"
            for m in recent_msgs[-5:]:
                role = m.get("role", "user")
                content = m.get("content", "")[:150]
                ctx_block += f"- [{role}] {content}\n"
            messages.append({"role": "user", "content": ctx_block})

    # ========== Recent Memories ==========
    recent_memories = context.get("recent_memories")
    if recent_memories:
        mem_block = f"\n{prompt('angela.related_memories')}\n"
        for mem in recent_memories[:3]:
            content = mem.get("content", "")[:150]
            mem_type = mem.get("memory_type", "unknown")
            mem_block += f"- [{mem_type}] {content}\n"
        messages.append({"role": "user", "content": mem_block})

    # ========== ED3N/GARDEN Draft Response (Refinement) ==========
    draft_response = context.get("draft_response")
    if draft_response:
        refinement_block = f"""
{prompt('angela.draft_response')}
{draft_response}

{prompt('angela.refinement_instruction')}
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
