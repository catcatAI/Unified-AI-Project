# API Endpoints

This document provides a summary of all the API endpoints available in the Unified AI Project.

## Backend API Endpoints (`apps/backend`)

All backend endpoints are defined in `apps/backend/src/services/main_api_server.py`.

### General

- **`GET /`**: Returns a welcome message.
- **`GET /status`**: Returns the status of the backend services.
- **`GET /services/health`**: Returns the health status of the backend services.
- **`GET /metrics`**: Returns system metrics.
- **`GET /api/health`**: Returns a simple health check response.

### Chat

- **`POST /chat`**: Handles a chat message.
- **`POST /api/v1/chat`**: Handles a chat message (V1 API).

### Session

- **`POST /api/v1/session/start`**: Starts a new session.

### HSP (Heterogeneous Service Protocol)

- **`GET /api/v1/hsp/services`**: Returns a list of available HSP services.
- **`POST /api/v1/hsp/tasks`**: Creates a new HSP task.
- **`GET /api/v1/hsp/tasks/{correlation_id}`**: Returns the status of an HSP task.

### Hot Reload and Drain

Minimal operational endpoints for safe hot actions. See docs/05-development/hot-reload-and-drain.md for details.

- **`POST /api/v1/hot/drain/start`**: Begin draining (pause acceptance of new work; advisory flag).
- **`POST /api/v1/hot/drain/stop`**: End draining.
- **`GET /api/v1/hot/status`**: Get draining state and initialized services snapshot.
- **`POST /api/v1/hot/reload/llm`**: Reload MultiLLMService and rewire dependents (ToolDispatcher, DialogueManager).
- **`POST /api/v1/hot/reload/hsp`**: Reload HSP connector with blue/green swap.

### Atlassian Integration

- **`POST /api/atlassian/config`**: Configures the Atlassian integration.
- **`POST /api/atlassian/test-connection`**: Tests the connection to Atlassian.
- **`GET /api/atlassian/confluence/spaces`**: Returns a list of Confluence spaces.
- **`GET /api/atlassian/confluence/spaces/{space_key}/pages`**: Returns a list of pages in a Confluence space.
- **`POST /api/atlassian/confluence/pages`**: Creates a new Confluence page.
- **`GET /api/atlassian/jira/projects`**: Returns a list of Jira projects.
- **`GET /api/atlassian/jira/projects/{project_key}/issues`**: Returns a list of issues in a Jira project.
- **`POST /api/atlassian/jira/issues`**: Creates a new Jira issue.
- **`POST /api/atlassian/jira/search`**: Searches for Jira issues.

### Rovo-Dev Integration

- **`GET /api/rovo-dev/status`**: Returns the status of the Rovo-Dev integration.
- **`POST /api/rovo-dev/tasks`**: Creates a new Rovo-Dev task.
- **`GET /api/rovo-dev/tasks`**: Returns a list of Rovo-Dev tasks.
- **`GET /api/rovo-dev/tasks/history`**: Returns the history of Rovo-Dev tasks.

### Other

- **`POST /code`**: Handles a code-related request.
- **`POST /search`**: Handles a search request.
- **`POST /image`**: Handles an image-related request.

## Frontend API Usage (`apps/frontend-dashboard`)

The frontend application uses the following endpoints. Note the `/api/py` prefix, which is likely added by a reverse proxy.

- `GET /api/py/api/health`
- `GET /api/py/status`
- `POST /api/py/chat`
- `GET /api/py/services/health`
- `GET /api/py/metrics`

## Desktop App API Usage (`apps/desktop-app`)

The desktop application uses the following endpoints:

- `GET /api/v1/hsp/services`
- `POST /api/v1/hsp/tasks`
- `GET /api/v1/hsp/tasks/{correlationId}`
- `POST /api/v1/session/start`
- `POST /api/v1/chat`
