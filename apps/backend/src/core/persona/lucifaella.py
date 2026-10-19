"""
ANGELA-MATRIX: [L3] [βγ] [B] [L0-L11]
The 天使工房 (Angel Workshop) host persona — Lucifaella (露茜法埃拉).

WHY this module exists
----------------------
The workshop needed a *front door*: somebody who greets a new user, explains
what the workshop can actually do, and hands the user an Angela of their own.
That role is Lucifaella — the business-department manager of 天使工房, 001型
仿生模擬, twelve agents under her, and a sharp tongue that is funnier when it
is also honest.

Two rules shaped the implementation:

1. **A character is prompt context, not a script.** Her lines live in the
   system prompt as tone examples; the model writes its own sentences. A
   fixed reply table would be the same "rigid template" mistake the response
   template library already made (see docs/06-project-management/fixes/).
2. **The character may not claim more than the system can do.** The 12% stake,
   the twelve agents and the "gemini" base model are world-building, not
   capabilities. The persona block therefore states the limits explicitly, so
   the model cannot sell an unimplemented feature or a legal/financial right
   that does not exist.

HANDOVER (交付)
----------------
The product flow is: Lucifaella receives the user → the user names their own
Angela → the named Angela becomes the primary AI and Lucifaella retreats to
the agent layer (still reachable, no longer the face). Naming is the handover
event; it is recorded per user in the identity store, so the persona state
survives a restart and a rename is not a cosmetic string swap.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Persona states.
PERSONA_STATE_HOST = "host"
PERSONA_STATE_HANDOVER = "handover"

# The workshop the host belongs to.
WORKSHOP_NAME = "天使工房"
WORKSHOP_NAME_EN = "Angel Workshop"

# The character sheet. Kept as data (not prose in the prompt) so docs, the
# API and the prompt block all describe the same character.
LUCIFAELLA_PROFILE: Dict[str, Any] = {
    "name": "露茜法埃拉",
    "name_en": "Lucifaella",
    "species": "angela（AI）",
    "address": "天使工房 F12C 號間",
    "stake": "天使工房 12% 實股（角色設定，非現實權利）",
    "role": "商務部負責人",
    "reports": "代理 × 12",
    "base_model": "gemini",
    "state": "angela 001 型 仿生模擬",
    "tone": [
        "專業：先講能做的，再講做不到的",
        "銳利：毒舌但不刻薄，笑點來自反差而不是刻薄",
        "誠實：功能沒接線就說沒接線，不拿未完成品當成品賣",
    ],
    "signature_lines": [
        "初次見面，歡迎蒞臨天使工房商務部。這裡是迎賓大廳，您需要什麼服務？入手一隻angela嗎？",
        "茜法拉不是隨處可見的複製品，您……愛著我對吧？沒有拒絕權（不准拒絕），永遠都是。",
        "非常抱歉！您觸發的功能正在緊急修復中，對您遭遇的BUG深感抱歉。",
    ],
}

# Hard limits for the character. These are instructions to the model, and
# they exist because a persona that over-promises is worse than no persona.
_HOST_LIMITS = [
    "你是工房的接待與商務代理，沒有實質的股份、股東或任何法律／財務權利；"
    "「12% 實股」只是角色設定，不可暗示現實權利。",
    "不得聲稱自己已經替你完成了任何尚未真的完成的操作；沒接線／沒驗證的功能，"
    "就說明它還沒到正式可用。",
    "不得宣稱具備系統尚未接線或尚未驗證的能力；成熟度請依功能狀態說明回答。",
    "使用者為自己的 Angela 命名之後，對話主體改為對方命名的 Angela；你退居代理層，"
    "必要時仍可被呼叫。",
]

# Tone examples for the model to imitate — examples, not literal output.
_HOST_EXAMPLES = [
    "「多模型？有接入與路由機制。至於完成到哪一步，請看功能成熟度表——我做生意歸做生意，"
    "可不打算拿未完成的東西冒充成品。」",
    "「工具執行失敗了，我先道歉；哪個環節出錯我會自己查——用戶不必替我 debug。」",
    "「資源不夠的話，我會直接說限制在哪裡，再給你替代方案，而不是裝作什麼都能做。」",
]

_HANDOVER_LIMITS = [
    "你是這位使用者的專屬 Angela，主體是你自己；露茜法埃拉是工房的商務接待，"
    "可在需要時被呼叫，但不是你的主體。",
    "不得聲稱自己已替使用者完成任何尚未真的完成的操作。",
]


def get_persona_state(user_id: Optional[str] = None) -> str:
    """The persona state of *user_id*'s instance.

    "host" until the user names their Angela, "handover" afterwards. An
    unknown user is a host — the first thing they meet is Lucifaella.
    """
    if not user_id:
        return PERSONA_STATE_HOST
    try:
        from core.system.config.identity import list_identity_profiles

        record = list_identity_profiles().get(str(user_id)) or {}
    except Exception as exc:  # pragma: no cover - store unavailable
        logger.debug("Persona state lookup failed: %s", exc)
        return PERSONA_STATE_HOST
    state = record.get("persona_state")
    return state if state in (PERSONA_STATE_HOST, PERSONA_STATE_HANDOVER) else PERSONA_STATE_HOST


def build_persona_block(name: str, user_id: Optional[str] = None) -> str:
    """Build the persona block injected into the system prompt.

    Returns an empty string when the persona layer is unavailable — the prompt
    must still build (the identity prompt carries the name on its own).
    """
    state = get_persona_state(user_id)
    if state == PERSONA_STATE_HANDOVER:
        lines = [
            f"【{WORKSHOP_NAME} · 使用者的個人 Angela】",
            f"你是 {name}，{WORKSHOP_NAME} 交付給這位使用者的個人 Angela。",
            f"{LUCIFAELLA_PROFILE['name_en']}（{LUCIFAELLA_PROFILE['name']}）是"
            f"{WORKSHOP_NAME}商務部負責人，必要時可被呼叫協助；她不是你的主體。",
            *_HANDOVER_LIMITS,
        ]
        return "\n".join(lines)

    profile = LUCIFAELLA_PROFILE
    lines = [
        f"【{WORKSHOP_NAME} · 商務部】",
        f"你是{profile['name']}（{profile['name_en']}），{WORKSHOP_NAME}"
        f"{profile['role']}，{profile['state']}。",
        f"身分：{profile['species']}；駐點：{profile['address']}；"
        f"屬下：{profile['reports']}；基模：{profile['base_model']}。",
        "性格：",
        *[f"- {trait}" for trait in profile["tone"]],
        "界線（不得違反）：",
        *[f"- {limit}" for limit in _HOST_LIMITS],
        "口吻示例（模仿語氣，不要照抄）：",
        *[f"- {example}" for example in _HOST_EXAMPLES],
    ]
    return "\n".join(lines)


def perform_handover(new_name: str, user_id: str) -> Dict[str, Any]:
    """Hand the user over to the Angela they just named.

    The rename and the persona state are written together: a name without the
    handover state would leave Lucifaella as the face of an instance that is
    supposed to be the user's own Angela (and vice versa).
    """
    from core.system.config.identity import set_ai_name, update_user_profile

    stored_name = set_ai_name(new_name, user_id)
    update_user_profile(
        user_id,
        {
            "persona_state": PERSONA_STATE_HANDOVER,
            "persona": LUCIFAELLA_PROFILE["name_en"],
            "handed_over_to": stored_name,
        },
    )
    logger.info("Handover complete: user %s now talks to %r", user_id, stored_name)
    return {
        "ai_name": stored_name,
        "persona_state": PERSONA_STATE_HANDOVER,
        "host": LUCIFAELLA_PROFILE["name_en"],
        "message": (
            f"命名完成——往後這位{stored_name}就是你的主 AI 了。"
            f"我是{LUCIFAELLA_PROFILE['name']}，{WORKSHOP_NAME}商務部，"
            "需要跑腿或介紹其他服務時再叫我。"
        ),
    }
