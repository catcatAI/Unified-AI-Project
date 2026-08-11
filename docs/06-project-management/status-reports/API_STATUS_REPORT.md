# API Status Report (Unified-AI-Project)

This document enumerates all current HTTP API endpoints exposed by the backend service in the monorepo. Unless otherwise noted, the base URL in development is:

- Backend (direct): http://localhost:8000
- Through Frontend Proxy: http://localhost:3000/api/py

Important: New v1 endpoints live under /api/v1/... while some legacy integration endpoints still exist under /api/.... This report covers both for clarity.

## Index
- [Health and System](#health-and-system)
- [AI Chat and Sessions](#ai-chat-and-sessions)
- [Code, Search, Image](#code-search-image)
- [Atlassian CLI Bridge (v1)](#atlassian-cli-bridge-v1)
- [Models and Agents (placeholders/extended)](#models-and-agents-placeholdersextended)
- [Legacy Atlassian/Integrations (non-v1)](#legacy-atlassianintegrations-non-v1)
- [Rovo Dev Integrations](#rovo-dev-integrations)

---

## Health and System

- GET `/`  
  Root welcome. Returns a welcome message.

- GET `/api/v1/health`  
  Overall health and basic services status.

- GET `/api/v1/system/services`  
  Extended system service list/status (if implemented in your branch).

- GET `/api/v1/system/metrics/detailed`  
  Detailed metrics (CPU, Memory, Disk, Network). Uses real psutil values.

Proxy via Next.js: `/api/py/api/v1/health`, `/api/py/api/v1/system/services`, `/api/py/api/v1/system/metrics/detailed`

## AI Chat and Sessions

- POST `/api/v1/session/start`  
  Starts a new session. Returns `session_id` and greeting.

- POST `/api/v1/chat`  
  Body: `{ text, user_id, session_id }`  
  Returns generated response text and metadata.

Proxy: `/api/py/api/v1/session/start`, `/api/py/api/v1/chat`

## Code, Search, Image

- POST `/api/v1/code`  
  Body: `{ code, language }` (also accepts `{ query }` as code).  
  Returns code analysis result.

- POST `/api/v1/search`  
  Body: `{ query }`  
  Returns structured search results.

- POST `/api/v1/image`  
  Body: `{ prompt, style }`  
  Returns generated image info or placeholder URL.

Proxy: `/api/py/api/v1/code`, `/api/py/api/v1/search`, `/api/py/api/v1/image`

## Atlassian CLI Bridge (v1)

These endpoints shell out to `acli.exe` via the bridge and return parsed results.

- GET `/api/v1/atlassian/status`  
  Returns: `{ acli_available, version, path }`.

- GET `/api/v1/atlassian/jira/projects`  
  Returns list of projects (JSON-parsed ACLI output).

- GET `/api/v1/atlassian/jira/issues`  
  Query params: `jql` (optional), `limit` (default 50).  
  Returns list of issues.

- POST `/api/v1/atlassian/jira/issue`  
  Body: `{ project_key, summary, description?, issue_type?, priority?, labels? }`  
  - `priority`: e.g. High/Medium/Low (string)
  - `labels`: comma-separated string or array of strings  
  Creates a Jira issue.

- GET `/api/v1/atlassian/confluence/spaces`  
  Returns list of Confluence spaces.

- GET `/api/v1/atlassian/confluence/search`  
  Query params: `query`, `limit` (default 25).  
  Searches Confluence content.

Proxy: `/api/py/api/v1/atlassian/...`

## Models and Agents (placeholders/extended)

These routes appear in the current file but may be placeholders or extended in your branch. Confirm implementation details before use.

- GET `/api/v1/agents`  
- GET `/api/v1/agents/{agent_id}`  
- POST `/api/v1/agents/{agent_id}/action`  

- GET `/api/v1/models`  
- GET `/api/v1/models/{model_id}/metrics`  
- GET `/api/v1/models/{model_id}/training`  

- GET `/api/v1/images/history`  
- DELETE `/api/v1/images/{image_id}`  
- POST `/api/v1/images/batch-delete`  
- GET `/api/v1/images/statistics`

Proxy: `/api/py` + above paths

## Legacy Atlassian/Integrations (non-v1)

These endpoints exist in the same file (likely earlier API style). They are not routed via /api/v1. Prefer using the v1 ACLI bridge endpoints unless you rely on existing flows.

- POST `/api/atlassian/config`
- POST `/api/atlassian/test-connection`
- GET `/api/atlassian/confluence/spaces`
- GET `/api/atlassian/confluence/spaces/{space_key}/pages`
- POST `/api/atlassian/confluence/pages`
- GET `/api/atlassian/jira/projects`
- GET `/api/atlassian/jira/projects/{project_key}/issues`
- POST `/api/atlassian/jira/issues`
- POST `/api/atlassian/jira/search`

Note: These may be superseded by the v1 ACLI endpoints above.

## Rovo Dev Integrations

Legacy Rovo Dev integration endpoints (not under v1 prefix):

- GET `/api/rovo-dev/status`
- POST `/api/rovo-dev/tasks`
- GET `/api/rovo-dev/tasks`
- GET `/api/rovo-dev/tasks/history`

---

## Usage Notes
- For frontend requests, always use the proxy prefix: `/api/py` + backend path.
- For CLI, the default base URL is `http://localhost:8000`. You can override with `--url` or environment variable `CLI_BASE_URL`.
- Some integrations require credentials (e.g., Atlassian ACLI). Configure those per vendor docs.

## Maintenance
Regenerate this report whenever API routes are added or changed. You can grep the backend service file for patterns like `@app.get(` and `@app.post(` to discover routes.
