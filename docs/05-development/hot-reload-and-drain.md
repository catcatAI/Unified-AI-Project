# Hot Reload, Hot Migration (Blue/Green), and Draining

This document describes the minimal hot-reload and hot-migration capabilities introduced for the backend API (FastAPI) and the global service singletons managed in `src/core_services`.

## Overview

- Hot Reload (LLM): Safely replaces the `MultiLLMService` instance and re-wires dependent components (ToolDispatcher, DialogueManager) without restarting the process.
- Hot Migration (HSP, blue/green): Establishes a new `HSPConnector`, subscribes, and swaps global reference before disconnecting the old connector.
- Draining: Advisory mechanism to pause acceptance of new work while allowing in-flight requests to complete.

All features are implemented conservatively to avoid breaking existing tests and runtime behavior.

## Endpoints

Base router prefix: `/api/v1/hot`

- `POST /drain/start`: Begin draining mode (advisory flag). New task-creating endpoints may reject while draining (see Integration section).
- `POST /drain/stop`: Exit draining mode.
- `GET /status`: Returns the draining state, a snapshot of initialized services, and communication status (HSP/MCP).
- `POST /reload/llm`: Replaces the LLM interface and re-wires dependencies.
- `POST /reload/tools`: Hot-reloads tool implementations (optionally a single tool via `?tool=<key>`).
- `POST /reload/hsp`: Performs blue/green reload of HSP connector and re-subscribes minimal topics.
- `POST /reload/personality`: Reloads personality profile (optionally `?profile=<name>`), updates EmotionSystem/DialogueManager.

## Status Endpoint Reference (Examples)

Example response schema (best-effort; fields may be None depending on runtime and mocks):

```json
{
  "draining": false,
  "services_initialized": {
    "llm_interface": true,
    "ham_manager": true,
    "personality_manager": true,
    "hsp_connector": true
  },
  "hsp": { "hsp_available": true, "is_connected": true, "fallback_enabled": true },
  "mcp": { "mcp_available": false, "is_connected": false, "fallback_enabled": true },
  "metrics": {
    "hsp": { "is_connected": true, "pending_acks_count": 0, "retry_counts_active": 0 },
    "mcp": { "is_connected": false, "fallback_initialized": false },
    "learning": { "known_ai_count": 1 },
    "memory": { "ham_store_size": 124 },
    "lis": { "incidents_recent": 5, "antibodies_recent": 2 }
  }
}
```

Notes:
- Values depend on environment (mock vs real connectors) and may be null if the metric is unavailable.
- This endpoint is safe to call during draining and reload operations for observability.

## Implementation

- File: `apps/backend/src/services/hot_reload_service.py`
- Router wiring: `apps/backend/src/services/main_api_server.py`

Key operations:

1) Draining
- Maintains an in-memory flag in `HotReloadService` guarded by an `asyncio.Lock`.
- Exposed via `/drain/start` and `/drain/stop`.

2) Reload LLM
- Closes the old LLM interface via `await old_llm.close()` (if exists).
- Instantiates a fresh interface via `get_multi_llm_service()`.
- Swaps `core_services.llm_interface_instance` with the new one.
- Re-wires ToolDispatcher and DialogueManager references via explicit setter if present or direct attribute assignment.

3) Reload HSP (Blue/Green)
- Reads broker config from the existing connector.
- Creates and connects a new `HSPConnector`.
- Re-subscribes minimal topics used by initialization (capability adverts, results, facts).
- Swaps `core_services.hsp_connector_instance` to the new connector, then disconnects the old one.

## Integration

- A dependency helper `reject_if_draining()` is available in `main_api_server.py`. Attach it via FastAPI `Depends` to task-creating endpoints to return `503 Service Unavailable` while draining.
- This helper is not yet attached to existing endpoints by default to avoid affecting current tests.

## Future Extensions

- Tools hot reload: Rescan the tools directory, dynamically load/unload tools, and update ToolDispatcher. Provide `/api/v1/hot/reload/tools`.
- Personality hot reload: Reload `PersonalityManager` from configuration and update EmotionSystem / DialogueManager.
- Observability: Extend `/status` to report connector health, message counts, recent errors.
- Graceful queues: Optionally queue requests while draining and process after resuming.

## Notes

- All operations are best-effort and designed not to crash or destabilize the process on failure.
- For production-grade zero-downtime deployments, combine these features with a process manager / orchestrator and a health-checking reverse proxy.
