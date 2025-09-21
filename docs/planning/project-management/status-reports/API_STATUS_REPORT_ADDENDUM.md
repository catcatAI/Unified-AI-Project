# API Status Report – Addendum (Updates)

This addendum records recent and planned API changes to keep the planning set aligned with the codebase.

## New (Implemented)
- GET `/api/v1/openapi`
  - Returns the FastAPI OpenAPI schema (same data as `/openapi.json`).
  - Purpose: tooling/automation for documentation and client generation.

## Planned (LLM Routing Phase 1)
- GET `/api/v1/models/available`
  - Returns a list of ModelProfile (provider, model_name, context_window, capabilities, cost/latency estimates), discovered from adapters and environment keys.
- POST `/api/v1/models/route`
  - Dry-run routing endpoint.
  - Body: `{ task_type, input_chars, needs_tools?, needs_vision?, latency_target?, cost_ceiling? }`
  - Returns: `{ best: {model_id, score, rationale}, candidates: [...] }`

## Notes
- The v1 Atlassian endpoints have been extended:
  - POST `/api/v1/atlassian/jira/issue` accepts `priority` and `labels` (labels supports comma-separated string or array).
- For frontend, always go through the proxy prefix `/api/py`.
