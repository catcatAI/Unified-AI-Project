# Atlassian Bridge: Seamless Integration with Atlassian Services

## Overview

The `AtlassianBridge` (`src/integrations/atlassian_bridge.py`) is a comprehensive integration layer within the Unified-AI-Project that provides a **unified and resilient interface for interacting with Atlassian services**, specifically Confluence, Jira, and Bitbucket. Its primary goal is to enable the AI (Angela) to seamlessly perform tasks, manage documentation, track projects, and collaborate within the Atlassian ecosystem.

This module is crucial for automating workflows, enhancing project management capabilities, and allowing the AI to participate actively in development and knowledge-sharing processes.

## Key Responsibilities and Features

1.  **Unified Service Interface**: 
    *   Provides a single point of access for Confluence, Jira, and Bitbucket operations, abstracting away the individual API complexities of each service.

2.  **Robust Fallback Mechanism (`_make_request_with_fallback`)**: 
    *   Implements a sophisticated fallback strategy that attempts requests against primary and then backup URLs for each service.
    *   Includes retry logic and configurable delays to ensure communication resilience in the face of network issues or service outages.

3.  **Caching (`_get_from_cache`, `_save_to_cache`)**: 
    *   Supports both in-memory and file-based caching of GET request results.
    *   Improves performance by reducing redundant API calls and provides a mechanism for serving stale data in offline scenarios.

4.  **Offline Mode and Queue (`_add_to_offline_queue`, `process_offline_queue`)**: 
    *   When enabled, write operations (POST, PUT, DELETE) are queued if the service is unreachable.
    *   The `process_offline_queue` method attempts to re-process these queued operations when connectivity is restored, ensuring data consistency.

5.  **Endpoint Health Monitoring (`_start_health_monitoring`, `_check_endpoints_health`)**: 
    *   Periodically checks the health status of configured primary and backup endpoints for each Atlassian service.
    *   Updates internal health status, allowing the system to dynamically select healthy endpoints.

6.  **Confluence Operations**: 
    *   `create_confluence_page`: Creates new pages with specified content (Markdown to Confluence storage format conversion included).
    *   `update_confluence_page`: Updates existing pages.
    *   `get_confluence_page`: Retrieves page content and metadata.
    *   `search_confluence_pages`: Searches for pages using Confluence Query Language (CQL).
    *   `get_confluence_spaces`: Retrieves a list of available Confluence spaces.

7.  **Jira Operations**: 
    *   `create_jira_issue`: Creates new Jira issues with various fields.
    *   `update_jira_issue`: Updates fields of existing Jira issues.
    *   `get_jira_issue`: Retrieves detailed information about a Jira issue.
    *   `search_jira_issues`: Searches for issues using Jira Query Language (JQL).
    *   `transition_jira_issue`: Changes the status of a Jira issue.
    *   `get_jira_projects`: Retrieves a list of available Jira projects.

8.  **Bitbucket Operations**: 
    *   `get_bitbucket_repositories`: Retrieves a list of repositories within a workspace.
    *   `get_bitbucket_pull_requests`: Retrieves pull requests for a given repository and state.

9.  **Utility Methods**: 
    *   `_markdown_to_confluence_storage`: Converts Markdown content to Confluence's storage format.
    *   `link_jira_to_confluence`: Facilitates linking Jira issues to Confluence pages.

## Integration with Other Modules

-   **`ProjectCoordinator`**: Heavily relies on the `AtlassianBridge` to manage tasks, create documentation, and track progress within Jira and Confluence.
-   **`LearningManager`**: Could potentially learn from Jira issue resolutions or Confluence documentation updates.
-   **`RovoDevConnector`**: The `AtlassianBridge` uses an instance of `EnhancedRovoDevConnector` (aliased as `RovoDevConnector`) to make the actual HTTP requests, leveraging its retry and request handling capabilities.

## Code Location

`src/integrations/atlassian_bridge.py`
