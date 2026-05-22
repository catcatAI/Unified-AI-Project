# Dual Server Architecture

The backend contains two FastAPI servers, both defaulting to port 8000.

## App A: `main.py` (System Management)

| Property | Value |
|----------|-------|
| File | `apps/backend/main.py` |
| Routes | 7 |
| Purpose | System management, hardware probe, cluster orchestration |
| Lifespan | BootstrapManager → ClusterManager → SyncManager → KG → Monitor |
| Port | 8000 (default), accepts `--port` |

## App B: `main_api_server.py` (Primary AI Server)

| Property | Value |
|----------|-------|
| File | `apps/backend/src/services/main_api_server.py` |
| Routes | ~104 (including ~50 shared from `api/router.py`) |
| Purpose | AI inference, chat, biological simulation, state matrix |
| Lifespan | Chat/LLM/Bio pre-init → `_initialize_all_services()` → `MetabolicHeartbeat.start()` |
| Port | 8000 (default) |

## Shared Router

Both servers include the same shared router at `api/router.py`, providing routes under `/api/v1/*` for drive, pet, vision, audio, tactile, mobile, economy, trace, and ops endpoints.

## Deployment Constraint

**Only one server can bind to port 8000 at a time.** The other must use `--port`.

## Known Startup Bug (Server Cannot Start)

`main_api_server.py:292` does a **module-level** import:
```python
from services.chat_service import generate_angela_response, get_angela_chat_service
```
After `chat_service.py` was rewritten from 1281 lines to a 306-line class-based `ChatService`, these standalone functions no longer exist. Since this is a top-level import (not inside a function), **the server crashes at import time before any route is served**.

Additionally, `main_api_server.py:695,1370` and `api/router.py:175` also import these functions inside functions — those would crash at runtime even if the top-level import were fixed.

**Fix**: Either restore `generate_angela_response()` as a wrapper that calls `ChatService.generate_response()`, or update all callers to use the new class-based API.

## Middleware

- **CORS**: App B uses config-driven origins; App A hard-codes `["*"]`
- **EncryptedCommunication**: Both servers. HMAC-SHA256 signature verification only, no body encryption. Protects `/api/v1/mobile/`, `/api/v1/system/status/detailed`, `/api/v1/system/module-control`.
