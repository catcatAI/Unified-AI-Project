# AtlassianBridge: Unified and Resilient Atlassian Integration

## Overview

This document provides an overview of the `AtlassianBridge` module (`src/integrations/atlassian_bridge.py`). This module serves as a unified and resilient bridge layer for interacting with a suite of Atlassian services, including Confluence, Jira, and Bitbucket.

## Purpose

The `AtlassianBridge` is designed to provide a single, consistent, and robust interface for the AI to interact with Atlassian products. It abstracts away the complexities of the individual Atlassian REST APIs and adds a layer of resilience, including features like endpoint fallback, caching, and offline support, to ensure reliable communication.

## Key Responsibilities and Features

*   **Unified Interface**: Provides a set of high-level, asynchronous methods for common Atlassian operations, abstracting the underlying API calls:
    *   **Confluence**: `create_confluence_page`, `update_confluence_page`, `get_confluence_page`, `search_confluence_pages`.
    *   **Jira**: `create_jira_issue`, `update_jira_issue`, `get_jira_issue`, `search_jira_issues`, `transition_jira_issue`.
    *   **Bitbucket**: `get_bitbucket_repositories`, `get_bitbucket_pull_requests`.
*   **Resilience and High Availability**:
    *   **Endpoint Management**: Manages a list of primary and backup URLs for each Atlassian service, allowing for seamless failover.
    *   **Automatic Fallback**: If a request to the primary URL for a service fails, the bridge automatically retries the request with the configured backup URLs.
    *   **Health Monitoring**: Includes a background task that periodically checks the health of all configured endpoints and can dynamically switch to a healthy endpoint if the primary one becomes unavailable.
*   **Performance and Offline Capabilities**:
    *   **Caching**: Implements both in-memory and file-based caching for `GET` requests. This improves performance by reducing redundant API calls and provides a basic level of offline access.
    *   **Offline Mode**: Can be configured to serve stale (expired) cache data when all endpoints for a service are unavailable, ensuring that the AI can still access previously retrieved information.
    *   **Offline Queue**: For write operations (`POST`, `PUT`, `DELETE`), if all endpoints are down, the bridge can queue the requests to be processed later when a connection is restored.
*   **Content Handling**: Includes a helper method (`_markdown_to_confluence_storage`) to convert Markdown text into the Confluence storage format (XHTML-based) that is required by the Confluence API.
*   **Integration with `RovoDevConnector`**: Leverages the `EnhancedRovoDevConnector` to make the actual HTTP requests, taking advantage of its built-in retry and error handling capabilities.

## How it Works

The `AtlassianBridge` is initialized with an `EnhancedRovoDevConnector` instance, which handles the low-level HTTP communication. When a method like `create_jira_issue` is called on the bridge, it constructs the appropriate API request payload. It then uses its `_make_request_with_fallback` method to send the request. This method intelligently tries the primary URL for the service first. If that fails, it iterates through the configured backup URLs. For `GET` requests, it checks the cache before making a network call. If all endpoints are unavailable, it can queue write operations or serve stale data for read operations, depending on its configuration.

## Integration with Other Modules

*   **`EnhancedRovoDevConnector`**: The underlying connector that is used for making all HTTP requests to the Atlassian APIs.
*   **`aiohttp`**: The HTTP client library that is used by the connector.
*   **`FastAPI` Server**: The main API server can use the `AtlassianBridge` to expose Atlassian functionalities to external clients.
*   **`ToolDispatcher`**: Could use the `AtlassianBridge` to provide a suite of Atlassian-related tools to the AI, allowing it to manage projects, documents, and code repositories.

## Code Location

`src/integrations/atlassian_bridge.py`