# Frontend Migration Note: Unified Chat Endpoint

## Why this migration

To reduce cross-client/session confusion and prepare for multi-persona AI interfaces,
backend now provides a unified chat endpoint:

- `POST /api/v1/chat/unified`

Legacy endpoints are still available during migration:

- `POST /dialogue`
- `POST /angela/chat`

## Required payload fields (recommended)

All frontends should gradually include:

- `tenant_id`
- `persona_id`
- `user_id`
- `client_id`
- `session_id` (optional but recommended)
- `message`

## Frontend update checklist

1. Switch primary chat request path to `/api/v1/chat/unified`.
2. Keep legacy fallback (404 => `/dialogue`) only during migration window.
3. Pass persona-specific context in every request.
4. Log and monitor `migration_note` and `context` fields from response.
5. Log `session_namespace` for debugging cross-persona/session isolation.
6. Treat `session_id` as client-facing token; backend now applies namespace internally.

### Known path updates for current clients

- Desktop status: use `GET /api/v1/system/status` (instead of `/status`).
- Desktop economy: use `GET /api/v1/economy/balance/{user_id}`.
- Desktop pet action trigger: use `POST /api/v1/pet/action/trigger`.

## Port migration note

- Current default backend address remains `127.0.0.1:8000`.
- Frontends should make backend address configurable (env/settings) so future
  dedicated AI service ports can be rolled out without code rewrites.
