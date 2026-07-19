# ANGELA-MATRIX: L3 [β] [A] [L2-L6]
"""Angela prompt construction — standalone module for A3 split"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.prompt_manager import get_prompt_manager, prompt

logger = logging.getLogger(__name__)

_autonomous_lifecycle = None
_theta_router = None


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
    """Return a cached ThetaRouter singleton."""
    global _theta_router
    if _theta_router is None:
        from core.engine.theta_router import ThetaRouter

        _theta_router = ThetaRouter()
    return _theta_router


def _get_llm_config(key: str, default: Any = None) -> Any:
    """Read a config value from the unified system/llm settings section."""
    try:
        from core.system.config.tiered_loader import get_config

        settings = get_config("system/llm").get("settings", {})
        return settings.get(key, default)
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
                parts.append(prompt("angela.bio.emotion", value=bio["dominant_emotion"]))
            if parts:
                return "、".join(parts)
        return str(bio)

    # Priority 2: File-based state (fallback)
    try:
        brain_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "brain_status.json"
        )
        if os.path.exists(brain_path):
            with open(brain_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"Brain status file read failed: {e}")
    return ""


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

        return "\n".join(lines) if lines else ""
    except Exception as e:
        logger.debug(f"Autonomous decisions unavailable: {e}")
        return ""


def get_theta_state() -> str:
    """Get theta router state for prompt context."""
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
    _append_awareness_injection(messages, context)
    _append_draft_response(messages, context)
    _append_document_context(messages, context)
    _append_knowledge_context(messages, context)
    _append_web_search_context(messages, context)

    messages.append({"role": "user", "content": f"<user_message>{user_message}</user_message>"})

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
        messages.append({"role": h.get("role", "assistant"), "content": h.get("content", "")})


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


def _append_document_context(messages: List[Dict], context: Dict) -> None:
    """Append generic document processing context to system prompt.

    Tells the LLM about DesktopInteraction availability for file operations.
    Document task results from the tiered processor are injected as context.
    """
    desktop = context.get("desktop_interaction")
    intent_result = context.get("_intent_result")
    if not desktop and not intent_result:
        return
    block = "\n\n---\n[File System & Document Processing]"
    if desktop:
        block += "\n- DesktopInteraction is available for read/write file operations."
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
        block += f"\n\n[Verified Knowledge]\n{grounded}"
    dictionary = context.get("dictionary_context")
    if dictionary:
        block += f"\n\n[Dictionary]\n{dictionary}"
    memory = context.get("conversation_memory")
    if memory:
        block += f"\n\n[Conversation Memory]\n{memory}"
    if block:
        messages[0]["content"] += block


def _append_web_search_context(messages: List[Dict], context: Dict) -> None:
    """Append proactive web-search grounding results to the system prompt."""
    web = context.get("web_search_context")
    if not web:
        return
    block = f"\n\n[Web Search Results]\n{web}"
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
    "_get_llm_config",
    "get_biological_state",
    "get_formula_summaries",
    "get_autonomous_decisions",
    "get_theta_state",
    "construct_angela_prompt",
]
