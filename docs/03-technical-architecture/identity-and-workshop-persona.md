# Identity, the workshop host, and the handover

> The user names their own Angela. Everything that can *speak* about the
> instance — the system prompt, the reflex answers, the subtitle, the TTS
> greeting, the chat panel — must use that name. The workshop host
> (露茜法埃拉 / Lucifaella) receives the user and hands over a personal
> Angela; a template is an *example for the model*, not a scripted answer.

ANGELA-MATRIX: [L2-L4] [βγ] [A/B] [L0-L11]

---

## 1. Why this needed a design, not a string swap

Before this change the instance name existed in five independent places:

| Surface | Old value | Consequence of a rename |
|---|---|---|
| `system/core.default.yaml` → `ai_name` | `Angela` | only 2 consumers read it (`SelfModel`, `SoulCore`) |
| `angela.identity` prompt | `"You are Angela, …"` | the model's own name never changed |
| `REFLEX_PRESETS` | `"我是Angela AI…"` | offline answers kept the old name |
| TTS `greet()` / `introduce()` | `"I'm Angela…"` | the voice introduced itself with the old name |
| `Subtitle.speaker` | `"Angela"` | subtitles credited the old name |

`get_ai_name()` existed, but "the name" was three different concepts wearing
one string. A rename therefore changed almost nothing the user could see —
and worse, a *global* rename would have renamed every user's instance at
once.

## 2. The name is per user

```
config  system/core.default.yaml → ai_name   ← the default for an unnamed instance
store   data/identities.json      → users[user_id].ai_name   ← the user's own choice
```

Read path (`core/system/config/identity.py`):

```
get_ai_name(user_id)
  → users[user_id].ai_name        (the user's override)
  → config ai_name                (the configured default)
  → "Angela"                      (the historical fallback)
```

Write path: `set_ai_name(name, user_id)` validates (non-empty, ≤ 32 chars,
control characters stripped), persists, and drops the override when the name
is the configured default again. A global rename is refused: `user_id` is
required, because one user renaming their Angela must never rename somebody
else's.

**The current user.** Most consumers are process-global singletons (the
reflex engines, the subtitle layer, the offline fallback chain) with no
request object, yet they still have to answer with the right user's name.
A `contextvars.ContextVar` carries the user through the async request
(`identity.current_user(user_id)`); the chat route binds it for the whole
turn. `asyncio` copies the context into child tasks, so a background task
spawned from a request keeps that user's name.

## 3. The workshop host: 露茜法埃拉 (Lucifaella)

`core/persona/lucifaella.py` holds the character:

| Field | Value |
|---|---|
| 物種 | angela（AI） |
| 住址 | 天使工房 F12C 號間 |
| 財力 | 天使工房 12% 實股（**角色設定，非現實權利**） |
| 職位 | 商務部負責人（代理 × 12） |
| 基模 | gemini |
| 狀態 | angela 001 型 仿生模擬 |

Two rules shape the implementation.

**A character is prompt context, not a script.** Her lines live in the
system prompt as tone examples; the model writes its own sentences. A fixed
reply table would repeat the mistake the response-template library made (see
§5).

**The character may not claim more than the system can do.** The 12% stake,
the twelve agents and the "gemini" base model are world-building, not
capabilities. The persona block states the limits explicitly, so the model
cannot sell an unimplemented feature or imply a legal/financial right that
does not exist:

```
界線（不得違反）：
- 你是工房的接待與商務代理，沒有實質的股份、股東或任何法律／財務權利；
  「12% 實股」只是角色設定，不可暗示現實權利。
- 不得聲稱自己已經替你完成了任何尚未真的完成的操作；沒接線／沒驗證的功能，
  就說明它還沒到正式可用。
- 不得宣稱具備系統尚未接線或尚未驗證的能力；成熟度請依功能狀態說明回答。
- 使用者為自己的 Angela 命名之後，對話主體改為對方命名的 Angela；你退居代理層。
```

## 4. The handover (交付)

```
             ┌──────────────────────────────┐
  new user → │ Lucifaella — business dept.  │ → explains, greets, demos
             └──────────────┬───────────────┘
                            │ user names their Angela
                            ▼
             ┌──────────────────────────────┐
             │ {name} — the user's own       │ → primary AI: chat, memory, tools
             │ Angela                        │    (Lucifaella stays callable
             └──────────────────────────────┘     as an agent)
```

The handover is an **event**, not a string swap: `perform_handover()` writes
the name *and* the persona state together, so an instance can never be named
while still presenting itself as the workshop host (or the other way round).

| Persona state | Prompt block |
|---|---|
| `host` | "You are 露茜法埃拉 (Lucifaella), business-department manager of 天使工房 …" + limits + tone examples |
| `handover` | "You are {name}, the user's personal Angela … Lucifaella is the workshop's business host, callable when needed, but not your subject." |

## 5. Templates are examples, not answers

The response-template library (`ai/memory/templates_data.json`, 49 curated
strings) used to be served **verbatim** as the user's answer: the model
never saw the template, and the user got the same sentence every time
("摸摸頭~別難過，我一直在你身邊呢"). For an AI project a template is worth
exactly two things:

1. **an example** that goes into the model's context — a tone/wording
   reference the model rephrases in its own words;
2. **a degraded-mode answer** when no model can answer at all.

The template layer now follows that split (`services/llm/router.py`):

| Situation | Behaviour |
|---|---|
| a language model is available | the selection becomes `context["template_example"]`; the prompt carries it under `angela.template_example` with the instruction *"the text above is a TONE example, not the answer"*; the model writes the reply |
| no model available (offline / unified-only) | the template is served as-is — the degraded-mode answer |

The layers themselves (social / keyword / emotion / pattern / matcher) now
*select* a template and hand the selection to `_serve_template_selection()`,
which decides between "model context" and "degraded answer". Selecting the
right template still matters — a sad example for a sad message — which is
why the keyword matching, the negation guard and the antonym guard
(`心情好差` must not select the joy template) stay.

## 6. API

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/identity?user_id=…` | the instance identity: name, source, persona state, host, whether the instance still needs a name |
| `POST /api/v1/identity/name` `{"name": "小安", "user_id": "…"}` | the handover: validates the name, renames the instance, switches the persona |

```jsonc
// POST /api/v1/identity/name
{
  "ok": true,
  "ai_name": "小安",
  "persona_state": "handover",
  "host": "Lucifaella",
  "message": "命名完成——往後這位小安就是你的主 AI 了。我是露茜法埃拉，天使工房商務部，需要跑腿或介紹其他服務時再叫我。",
  "profile": { "ai_name": "小安", "source": "user", "customized": true }
}
```

## 7. Front end

The name is fetched, not hardcoded:

- `packages/shared-js/js/api-client.js` — `getIdentity()` / `setIdentityName()`
- `packages/shared-js/js/app.js` — `_applyInstanceIdentity()` labels the chat
  input and every `[data-ai-name]` element
- `apps/web-live2d-viewer/js/unified-shell.js` — the same for the web shell
- `apps/web-dashboard/src/components/ChatPanel.tsx` — the role label

A failed lookup is not fatal: the default markup stays.

Note the distinction the UI keeps: **"Angela AI" is the product** (window
title, about dialog, tray tooltip) and stays as it is; **the instance name**
is the user's AI and follows the rename.

## 8. Tests

| File | Locks |
|---|---|
| `tests/core/test_identity_and_persona.py` | per-user store, validation, name propagation (prompt / reflex / subtitle), the persona block, the handover |
| `tests/api/test_identity_routes.py` | the identity endpoints and their validation |
| `tests/services/test_template_role.py` | a template becomes model context with a model, and the degraded answer without one |
