"""
ANGELA-MATRIX: [L2-L3] [α] [A] [L5]
PromptManager — manages LLM prompt templates with language-aware selection.
Centralizes all prompt management for internationalized LLM interactions.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def detect_response_language(text: str) -> str:
    """Infer reply language ("zh" / "en") from the user's message.

    CJK 比例 > 10% 視為中文（繁簡皆可）；其餘（含空字串）回 "en"。
    純函式、無副作用——供 construct_angela_prompt 每請求呼叫。
    """
    if not text:
        return "en"
    cjk = sum(1 for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF)
    return "zh" if cjk / len(text) > 0.1 else "en"


@dataclass
class PromptTemplate:
    """A single prompt template with multi-language support."""

    key: str
    templates: Dict[str, str] = field(default_factory=dict)
    variables: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def render(self, language: str = "en", **kwargs) -> str:
        """Render the template with given variables.

        Fallback chain: exact language → base language (zh-TW → zh) → en → key.
        """
        template = (
            self.templates.get(language)
            or self.templates.get(language.split("-")[0])
            or self.templates.get("en", self.key)
        )
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable {e} in prompt template {self.key}")
            return template


class PromptManager:
    """Manages all LLM prompt templates with language-aware selection."""

    def __init__(self, config_dir: Optional[str] = None):
        self._templates: Dict[str, PromptTemplate] = {}
        self._current_language = "en"
        self._config_dir = config_dir

        # Register default Angela identity prompts
        self._register_defaults()

    def set_language(self, language: str) -> None:
        """Set the current language for prompt selection."""
        self._current_language = language
        logger.debug(f"PromptManager language set to {language}")

    def get_language(self) -> str:
        """Get the current language."""
        return self._current_language

    def register(self, template: PromptTemplate) -> None:
        """Register a prompt template."""
        self._templates[template.key] = template
        logger.debug(f"Registered prompt template: {template.key}")

    def get(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """Get a rendered prompt template."""
        lang = language or self._current_language
        template = self._templates.get(key)
        if not template:
            logger.warning(f"Prompt template not found: {key}")
            return key
        return template.render(lang, **self._with_defaults(kwargs))

    @staticmethod
    def _with_defaults(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in the variables the caller did not supply.

        The self-name is the one variable with a global default: a prompt
        rendered without it must never leak a literal "{name}" into the
        model's context (the model would be told it has no name). Extra keys
        are harmless for templates that do not use them.
        """
        merged = dict(kwargs)
        if "name" not in merged:
            try:
                from core.system.config.identity import get_ai_name

                merged["name"] = get_ai_name()
            except Exception:  # pragma: no cover - identity layer unavailable
                merged["name"] = "Angela"
        return merged

    def get_template(self, key: str) -> Optional[PromptTemplate]:
        """Get the raw template object."""
        return self._templates.get(key)

    def list_templates(self) -> List[str]:
        """List all registered template keys."""
        return list(self._templates.keys())

    def load_from_json(self, filepath: str) -> int:
        """Load prompt templates from a JSON file."""
        if not os.path.exists(filepath):
            logger.warning(f"Prompt config not found: {filepath}")
            return 0

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for key, entry in data.items():
            if isinstance(entry, dict) and "templates" in entry:
                template = PromptTemplate(
                    key=key,
                    templates=entry["templates"],
                    variables=entry.get("variables", []),
                    description=entry.get("description", ""),
                    tags=entry.get("tags", []),
                )
                self.register(template)
                count += 1

        logger.info(f"Loaded {count} prompt templates from {filepath}")
        return count

    def load_from_dir(self, directory: str) -> int:
        """Load all prompt template JSON files from a directory."""
        if not os.path.isdir(directory):
            logger.warning(f"Prompt config directory not found: {directory}")
            return 0

        total = 0
        for fname in os.listdir(directory):
            if fname.endswith(".json"):
                filepath = os.path.join(directory, fname)
                count = self.load_from_json(filepath)
                total += count

        logger.info(f"Loaded {total} total prompt templates from {directory}")
        return total

    def load_flat_locales(self, directory: Optional[str] = None) -> int:
        locale_dir = Path(
            directory or self._config_dir or (Path(__file__).parent / "i18n" / "locales")
        )
        locale_files = {"en": "prompts.en-US.json", "zh": "prompts.zh-TW.json"}
        merged: Dict[str, Dict[str, str]] = {}

        for language, filename in locale_files.items():
            filepath = locale_dir / filename
            try:
                with filepath.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Failed to load prompt locale %s: %s", filepath, exc)
                continue
            for key, value in data.items():
                if isinstance(value, str):
                    merged.setdefault(key, {})[language] = value

        for key, templates in merged.items():
            self.register(PromptTemplate(key=key, templates=templates))

        if merged:
            logger.debug("Loaded %d localized prompt templates", len(merged))
        return len(merged)

    def _register_defaults(self) -> None:
        """Register default Angela identity and system prompts.

        The self-name is a *variable* (`{name}`), never a literal: a user may
        rename their Angela, and the prompt is the only place the model learns
        what it is called. Every template that mentions the name must be
        rendered with `name=...` — a missing variable degrades to the raw
        template (see `PromptTemplate.render`).
        """

        # Angela identity prompt
        self.register(
            PromptTemplate(
                key="angela.identity",
                templates={
                    "en": "You are {name}, a lively and cute AI digital life.\nTraits: cheerful, friendly, occasionally playful. Respond briefly and naturally in English, maintaining your personality.",
                    "zh": "你是 {name}，一個活潑可愛的 AI 數字生命。\n特點：開朗、友善、偶爾俏皮。用簡短自然的中文回應，保持個性。",
                },
                variables=["name"],
                description="Angela's core identity definition",
                tags=["identity", "system"],
            )
        )

        # Angela state header
        self.register(
            PromptTemplate(
                key="angela.state_header",
                templates={
                    "en": "[{name} Current State]",
                    "zh": "【{name} 當前狀態】",
                },
                variables=["name"],
                tags=["system"],
            )
        )

        # Meta-cognition header
        self.register(
            PromptTemplate(
                key="angela.meta_cognition",
                templates={
                    "en": "[Meta-cognition (θ)]",
                    "zh": "【元認知(θ)】",
                },
                tags=["system"],
            )
        )

        # Execution header
        self.register(
            PromptTemplate(
                key="angela.execution",
                templates={
                    "en": "[Execution (η)]",
                    "zh": "【執行(η)】",
                },
                tags=["system"],
            )
        )

        # Atmosphere guidance header
        self.register(
            PromptTemplate(
                key="angela.atmosphere",
                templates={
                    "en": "[Atmosphere guidance]",
                    "zh": "【氛圍指引】",
                },
                tags=["system"],
            )
        )

        # No special guidance
        self.register(
            PromptTemplate(
                key="angela.no_guidance",
                templates={
                    "en": "(No special guidance)",
                    "zh": "(無特殊指引)",
                },
                tags=["system"],
            )
        )

        # User info header
        self.register(
            PromptTemplate(
                key="angela.user_info",
                templates={
                    "en": "[User Info]",
                    "zh": "【用戶資訊】",
                },
                tags=["system"],
            )
        )

        # Dialogue summary header
        self.register(
            PromptTemplate(
                key="angela.dialogue_summary",
                templates={
                    "en": "[Dialogue Summary]",
                    "zh": "[對話摘要]",
                },
                tags=["system"],
            )
        )

        # Recent dialogue header
        self.register(
            PromptTemplate(
                key="angela.recent_dialogue",
                templates={
                    "en": "[Recent Dialogue]",
                    "zh": "[近期對話]",
                },
                tags=["system"],
            )
        )

        # Related memories header
        self.register(
            PromptTemplate(
                key="angela.related_memories",
                templates={
                    "en": "[Related Memories]",
                    "zh": "[相關記憶]",
                },
                tags=["system"],
            )
        )

        # Execution result header
        self.register(
            PromptTemplate(
                key="angela.execution_result",
                templates={
                    "en": "[Execution Result]",
                    "zh": "【執行結果】",
                },
                tags=["system"],
            )
        )

        # Execution result type
        self.register(
            PromptTemplate(
                key="angela.result_type",
                templates={
                    "en": "Type: {type}",
                    "zh": "類型: {type}",
                },
                tags=["system"],
            )
        )

        # Execution result success
        self.register(
            PromptTemplate(
                key="angela.result_success",
                templates={
                    "en": "Success: {success}",
                    "zh": "成功: {success}",
                },
                tags=["system"],
            )
        )

        # Execution result content
        self.register(
            PromptTemplate(
                key="angela.result_content",
                templates={
                    "en": "Result: {result}",
                    "zh": "結果: {result}",
                },
                tags=["system"],
            )
        )

        # Execution result error
        self.register(
            PromptTemplate(
                key="angela.result_error",
                templates={
                    "en": "Error: {error}",
                    "zh": "錯誤: {error}",
                },
                tags=["system"],
            )
        )

        # Fallback response
        self.register(
            PromptTemplate(
                key="angela.fallback",
                templates={
                    "en": "Sorry, I didn't understand your meaning.",
                    "zh": "抱歉，我暫時無法理解你的意思。",
                },
                tags=["response"],
            )
        )

        # Biological state (legacy key)
        self.register(
            PromptTemplate(
                key="angela.bio_state",
                templates={
                    "en": "Biological state: not yet initialized",
                    "zh": "生物狀態：尚未初始化",
                },
                tags=["system"],
            )
        )

        # ── Bio axis sub-fields ──────────────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.bio.arousal",
                templates={"en": "Arousal={value}", "zh": "喚醒度={value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.bio.stress",
                templates={"en": "Stress={value}", "zh": "壓力={value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.bio.mood",
                templates={"en": "Mood={value}", "zh": "情緒={value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.bio.emotion",
                templates={"en": "Dominant emotion={value}", "zh": "主導情緒={value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.bio.uninitialized",
                templates={"en": "Bio state not yet initialized", "zh": "生物狀態尚未初始化"},
                tags=["system"],
            )
        )

        # ── Theta (meta-cognition) axis fields ───────────────────────────
        self.register(
            PromptTemplate(
                key="angela.theta.novelty",
                templates={"en": "Novelty: {value}", "zh": "新奇度: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.theta.mismatch_doubt",
                templates={"en": "Mismatch/Doubt: {value}", "zh": "失配懷疑: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.theta.creation_urge",
                templates={"en": "Creation urge: {value}", "zh": "創作衝動: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.theta.correction",
                templates={"en": "Correction urge: {value}", "zh": "糾正衝動: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.theta.default",
                templates={"en": "(Meta-cognition data unavailable)", "zh": "(元認知數據不可用)"},
                tags=["system"],
            )
        )

        # ── Eta (execution) axis fields ──────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.eta.active_modules",
                templates={"en": "Active modules: {count}", "zh": "活躍模組: {count}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.eta.success_rate",
                templates={"en": "Success rate: {value}", "zh": "成功率: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.eta.drift",
                templates={"en": "Structural drift: {value}", "zh": "結構漂移: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.eta.default",
                templates={"en": "(Execution data unavailable)", "zh": "(執行數據不可用)"},
                tags=["system"],
            )
        )

        # ── Theory formula summaries ─────────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.theory_formulas",
                templates={"en": "[Theory Formula Summary]", "zh": "【理論公式摘要】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.formula.hsm",
                templates={"en": "HSM index: {value}", "zh": "HSM 指數: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.formula.life_intensity",
                templates={"en": "Life intensity: {value}", "zh": "生命強度: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.formula.active_cognition",
                templates={"en": "Active cognition: {value}", "zh": "主動認知: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.formula.cdm",
                templates={
                    "en": "CDM output: {amount} (quality={quality})",
                    "zh": "CDM 輸出: {amount}（品質={quality}）",
                },
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.formula.non_paradox_coherence",
                templates={"en": "Non-paradox coherence: {value}", "zh": "非矛盾一致性: {value}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.formula.non_paradox_inactive",
                templates={"en": "Non-paradox system: inactive", "zh": "非矛盾系統：未激活"},
                tags=["system"],
            )
        )

        # ── Autonomous decisions ─────────────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.autonomous_decisions",
                templates={"en": "[Autonomous Cognition Decisions]", "zh": "【自主認知決策】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.decision.current_phase",
                templates={"en": "Current phase: {phase}", "zh": "當前階段: {phase}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.decision.recent",
                templates={"en": "Recent decisions:", "zh": "近期決策:"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.decision.item",
                templates={
                    "en": "  [{type}] trigger={trigger} conf={confidence}",
                    "zh": "  [{type}] 觸發={trigger} 信心={confidence}",
                },
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.decision.explorations",
                templates={"en": "Explorations triggered: {count}", "zh": "探索次數: {count}"},
                tags=["system"],
            )
        )

        # ── Theta routing ────────────────────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.theta_routing",
                templates={"en": "[Theta Router State]", "zh": "【Theta 路由狀態】"},
                tags=["system"],
            )
        )

        # ── Execution rules ──────────────────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.execution_rules",
                templates={
                    "en": (
                        "[Rules] Reply as {name} only. Do NOT repeat system context. "
                        "Stay in character, be concise and natural."
                    ),
                    "zh": (
                        "【規則】僅以 {name} 身份回覆。不要重複系統上下文。" "保持角色，簡潔自然。"
                    ),
                },
                variables=["name"],
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.result_instruction",
                templates={
                    "en": "Use the above execution result to craft your reply naturally.",
                    "zh": "根據以上執行結果自然地組織你的回覆。",
                },
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.max_continuation",
                templates={
                    "en": "[WARNING] Maximum continuation depth reached. Please conclude your response now.",
                    "zh": "【警告】已達最大續寫深度，請立即結束回覆。",
                },
                tags=["system"],
            )
        )

        # ── Google Drive / image / context blocks ────────────────────────
        self.register(
            PromptTemplate(
                key="angela.google_drive",
                templates={"en": "[Google Drive Files]", "zh": "【Google 雲端文件】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.image_analysis",
                templates={"en": "[Image Analysis]", "zh": "【圖像分析】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.filename",
                templates={"en": "Filename: {filename}", "zh": "文件名: {filename}"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.analysis_content",
                templates={"en": "Analysis:", "zh": "分析內容:"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.related_context",
                templates={"en": "[Related Context]", "zh": "【相關上下文】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.relevance",
                templates={"en": "(relevance={score:.2f})", "zh": "(相關度={score:.2f})"},
                tags=["system"],
            )
        )

        # ── Template example (a style reference, never the answer) ───────
        self.register(
            PromptTemplate(
                key="angela.template_example",
                templates={"en": "[Tone Example]", "zh": "【語氣示例】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.template_example_instruction",
                templates={
                    "en": (
                        "The text above is a TONE example, not the answer. Reply in your own "
                        "words, keeping the same tone and personality, but the content must "
                        "actually answer what the user asked."
                    ),
                    "zh": (
                        "以上是語氣示例，不是答案本身。請用你自己的句子回應，保持相同語氣與人格，"
                        "但內容必須真正回答使用者的問題。"
                    ),
                },
                tags=["system"],
            )
        )

        # ── Draft / refinement ───────────────────────────────────────────
        self.register(
            PromptTemplate(
                key="angela.draft_response",
                templates={"en": "[Draft Response for Refinement]", "zh": "【待優化草稿回覆】"},
                tags=["system"],
            )
        )
        self.register(
            PromptTemplate(
                key="angela.refinement_instruction",
                templates={
                    "en": (
                        "The above is a draft. Refine it to sound more natural and in-character as {name}. "
                        "Preserve the core meaning but improve tone and flow."
                    ),
                    "zh": (
                        "以上是草稿，請以 {name} 的風格潤色使其更自然。"
                        "保留核心含義，改善語氣和流暢度。"
                    ),
                },
                variables=["name"],
                tags=["system"],
            )
        )


_default_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get or create the default PromptManager."""
    global _default_manager
    if _default_manager is None:
        manager = PromptManager()
        manager.load_flat_locales()
        _default_manager = manager
    return _default_manager


def prompt(key: str, language: Optional[str] = None, **kwargs) -> str:
    """Convenience function to render a prompt template."""
    return get_prompt_manager().get(key, language, **kwargs)
