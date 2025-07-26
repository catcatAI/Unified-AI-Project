# API and Endpoint Summary

This document provides an overview of the various API endpoints and network addresses used within the Unified-AI-Project.

## 1. Internal/Local API Endpoints

These endpoints are typically used for inter-service communication within the local development environment or deployed system.

*   **Main API Server:**
    *   **Endpoint:** `http://127.0.0.1:8000/api/v1/health` (Health Check)
    *   **Configuration:** Defined in `configs/system_config.yaml` (`system.api_server.host`, `system.api_server.port`)
    *   **Usage:** Used by `scripts/health_check.py` and potentially other internal services.
    *   **Source Files:** `configs/system_config.yaml`, `scripts/health_check.py`, `src/services/main_api_server.py`

*   **Electron App Frontend API:**
    *   **Endpoint:** `http://localhost:8000/api/v1`
    *   **Usage:** Frontend communication with the backend API.
    *   **Source File:** `src/interfaces/electron_app/renderer.js`

*   **Ollama Local LLM Service:**
    *   **Endpoint:** `http://localhost:11434`
    *   **Configuration:** Defined in `configs/system_config.yaml` (`core_systems.ollama.base_url`)
    *   **Usage:** Local Large Language Model (LLM) inference.
    *   **Source Files:** `configs/system_config.yaml`, `src/services/llm_interface.py`

*   **Node.js Services Placeholder:**
    *   **Endpoint:** `http://localhost:${port}` (dynamic port)
    *   **Usage:** Placeholder for potential Node.js based services.
    *   **Source File:** `src/services/node_services/server.js`

## 2. External API Endpoints

These endpoints connect to external services or third-party APIs.

*   **Context7 MCP (Message Communication Protocol):**
    *   **Production Endpoint:** `https://api.context7.com/mcp`
    *   **Usage:** Communication with the Context7 Message Communication Protocol service.
    *   **Source Files:** `docs/technical_design/CONTEXT7_MCP_INTEGRATION.md`, `tests/mcp/test_context7_connector.py`
    *   **Test Endpoints:** `https://test.com`, `https://test-mcp.context7.com` (used in `tests/mcp/test_context7_connector.py`)

*   **Pythagora.ai S3 Assets:**
    *   **Endpoint:** `https://s3.us-east-1.amazonaws.com/assets.pythagora.ai/scripts/utils.js`
    *   **Endpoint:** `https://s3.us-east-1.amazonaws.com/assets.pythagora.ai/logos/favicon.ico`
    *   **Usage:** Serving static assets (JavaScript utilities, favicon) for the Electron application.
    *   **Source Files:** `src/interfaces/electron_app/new_index.html`, `src/interfaces/electron_app/views/code_inspect/index.html`

*   **Google Fonts:**
    *   **Endpoint:** `https://fonts.googleapis.com`
    *   **Endpoint:** `https://fonts.gstatic.com`
    *   **Usage:** Loading custom fonts for the Electron application.
    *   **Source File:** `src/interfaces/electron_app/index.html`

*   **Dummy Image Service:**
    *   **Endpoint:** `https://dummyimage.com`
    *   **Usage:** Placeholder for image generation in `src/tools/image_generation_tool.py`.
    *   **Source File:** `src/tools/image_generation_tool.py`

*   **DuckDuckGo Web Search:**
    *   **Endpoint:** `https://duckduckgo.com/html/`
    *   **Usage:** Used by `src/tools/web_search_tool.py` for web search functionality.
    *   **Source File:** `src/tools/web_search_tool.py`

## 3. Ontology/Schema URIs (Non-Network Endpoints)

These are Uniform Resource Identifiers (URIs) used for defining and referencing concepts, properties, and instances within the project's knowledge representation and semantic mapping. They are not direct network endpoints for API calls.

*   **Example Ontologies/Schemas:**
    *   `http://example.com/ontology#...`
    *   `http://schema.org/...`
    *   `http://xmlns.com/foaf/0.1/...`
    *   `http://www.w3.org/2000/01/rdf-schema#...`
    *   `http://example.org/...`
    *   **Usage:** Semantic mapping, knowledge graph representation, data structuring.
    *   **Source Files:** `configs/ontology_mappings.yaml`, `scripts/mock_hsp_peer.py`, `src/core_ai/learning/learning_manager.py`, `tests/core_ai/learning/test_content_analyzer_module.py`, `tests/hsp/test_hsp_integration.py`

## 4. Documentation and Registry Links (Non-API Endpoints)

These are URLs found in documentation, configuration files, or dependency manifests, primarily for informational or dependency resolution purposes, not for direct API interaction by the application's runtime.

*   **MQTT Documentation:**
    *   `https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html`
    *   `https://mosquitto.org/documentation/`
    *   `https://www.hivemq.com/docs/`
    *   `https://www.emqx.io/docs/`
*   **Pytest Documentation:**
    *   `https://pypi.org/project/pytest-timeout/`
    *   `https://pypi.org/project/pytest-asyncio/`
    *   `https://docs.pytest.org/en/stable/goodpractices.html`
    *   `https://docs.pytest.org/en/stable/asyncio.html`
*   **Asset Source:**
    *   `https://chuckiecatt.itch.io/16x16-grassland-tileset`
    *   `https://creativecommons.org/licenses/by/4.0/`
*   **NPM Registry/GitHub/Sponsor Links (from `package-lock.json`):**
    *   Numerous `https://registry.npmjs.org/...`
    *   Numerous `https://github.com/...`
    *   `https://opencollective.com/webpack`
    *   `https://tidelift.com/...`
    *   `https://www.patreon.com/feross`
    *   `https://feross.org/support`
