# Identity, the workshop host, and the handover

> The user names their own Angela. Everything that can _speak_ about the
> instance — the system prompt, the reflex answers, the subtitle, the TTS
> greeting, the chat panel — must use that name. The workshop host (露茜法埃拉 /
> Lucifaella) receives the user and hands over a personal Angela. Persona context
> supplements, but never replaces, the underlying AI identity; quotes/examples are
> optional tone references, not scripted or default answers.

ANGELA-MATRIX: [L2-L4] [βγ] [A/B] [L0-L11]

---

## 1. Why this needed a design, not a string swap

Before this change the instance name existed in five independent places:

| Surface                                | Old value             | Consequence of a rename                            |
| -------------------------------------- | --------------------- | -------------------------------------------------- |
| `system/core.default.yaml` → `ai_name` | `Angela`              | only 2 consumers read it (`SelfModel`, `SoulCore`) |
| `angela.identity` prompt               | `"You are Angela, …"` | the model's own name never changed                 |
| `REFLEX_PRESETS`                       | `"我是Angela AI…"`    | offline answers kept the old name                  |
| TTS `greet()` / `introduce()`          | `"I'm Angela…"`       | the voice introduced itself with the old name      |
| `Subtitle.speaker`                     | `"Angela"`            | subtitles credited the old name                    |

`get_ai_name()` existed, but "the name" was three different concepts wearing one
string. A rename therefore changed almost nothing the user could see — and
worse, a _global_ rename would have renamed every user's instance at once.

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
control characters stripped), persists, and drops the override when the name is
the configured default again. A global rename is refused: `user_id` is required,
because one user renaming their Angela must never rename somebody else's.

**The current user.** Most consumers are process-global singletons (the reflex
engines, the subtitle layer, the offline fallback chain) with no request object,
yet they still have to answer with the right user's name. A
`contextvars.ContextVar` carries the user through the async request
(`identity.current_user(user_id)`); the chat route binds it for the whole turn.
`asyncio` copies the context into child tasks, so a background task spawned from
a request keeps that user's name.

## 3. The workshop host: 露茜法埃拉 (Lucifaella)

`core/persona/lucifaella.py` holds the character:

| Field | Value                                         |
| ----- | --------------------------------------------- |
| Character ID/version | `angela.lucifaella@1.0.0`, based on `angela.core@1.0.0` |
| Identity | Angela AI character edition; persona context does not replace model identity |
| Role | Angel Workshop public-facing host and mascot (看板娘) |
| Setting | The workshop reception area is fictional role context, not a real address or authority |

Two rules shape the implementation.

**A character is optional prompt context, not a script or replacement identity.**
The underlying assistant remains Angela AI; role and personality context may
influence tone but cannot override model identity, actual capabilities, safety
rules, or the user's task. Quote examples are not required or verbatim responses.

**The character may not claim more than the system can do.** Older profile fields such as a 12% stake, twelve agents, and a named vendor as the base model are not canonical facts. Do not inject them as real ownership, staff, or implementation details.
The persona block states factuality limits explicitly, so the model does not sell an
unimplemented feature or imply a legal/financial right that does not exist:

```
界線（不得違反）：
- 你是工房的接待與商務代理；工房設定是虛構角色語境，不得聲稱擁有現實股份、法律／財務權利或僱員。
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

The handover is an **event**, not a string swap: `perform_handover()` writes the
name _and_ the persona state together, so an instance can never be named while
still presenting itself as the workshop host (or the other way round).

| Persona state | Prompt block                                                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `host`        | Angela AI with optional Lucifaella host context, limits, and non-verbatim tone guidance |
| `handover`    | Angela AI remains the underlying identity; `{name}` is the user's primary Angela instance, and Lucifaella is a callable workshop host, not the subject |

## 5. Templates and persona quotes are examples, not answers

The response-template library (`ai/memory/templates_data.json`) and persona quote lists are not the AI's identity. They may provide optional context where the active model path supports it; they must not override the user's task or become an automatic fixed answer. In particular, signature lines are never injected as required Lucifaella replies. Any no-model fallback must be clearly a system fallback, not presented as a model-generated response.

The template layer may provide context to a model where supported, but is not
permitted to replace normal AI generation with a fixed persona answer. The current
Lucifaella integration's greeting/error response compatibility methods return no
scripted response. Degraded-mode system fallback remains distinct from a
model-generated response.

Historical template behavior (documented for context; verify before relying on it):

| Situation                                   | Behaviour                                                                                                                                                                                                        |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| a language model is available               | character/persona content is contextual guidance only; the assistant generates a response for the request |
| no model available (offline / unified-only) | use a truthful system fallback for the failure state; do not describe it as model-generated or use persona quotes as default answers |

The layers themselves (social / keyword / emotion / pattern / matcher) now
_select_ a template and hand the selection to `_serve_template_selection()`,
which decides between "model context" and "degraded answer". Selecting the right
template still matters — a sad example for a sad message — which is why the
keyword matching, the negation guard and the antonym guard (`心情好差` must not
select the joy template) stay.

## 6. API

| Endpoint                                                        | Purpose                                                                                           |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `GET /api/v1/identity?user_id=…`                                | the instance identity: name, source, persona state, host, whether the instance still needs a name |
| `POST /api/v1/identity/name` `{"name": "小安", "user_id": "…"}` | the handover: validates the name, renames the instance, switches the persona                      |

```jsonc
// POST /api/v1/identity/name
{
  "ok": true,
  "ai_name": "小安",
  "persona_state": "handover",
  "host": "Lucifaella",
  "message": "命名完成——往後由小安作為你的 Angela AI 個人實例；露茜法埃拉是天使工房迎賓主持，需要工房協助時仍可呼叫。",
  "profile": { "ai_name": "小安", "source": "user", "customized": true },
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

Note the distinction the UI keeps: **"Angela AI" is the product** (window title,
about dialog, tray tooltip) and stays as it is; **the instance name** is the
user's AI and follows the rename.

## 8. Tests

| File                                      | Locks                                                                                                      |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `tests/core/test_identity_and_persona.py` | per-user store, validation, name propagation (prompt / reflex / subtitle), the persona block, the handover |
| `tests/api/test_identity_routes.py`       | the identity endpoints and their validation                                                                |
| `tests/services/test_template_role.py`    | a template becomes model context with a model, and the degraded answer without one                         |
