# Web Search Tool

## Overview

The `WebSearchTool` (`src/tools/web_search_tool.py`) provides the Unified-AI-Project with the capability to **perform web searches and retrieve relevant information from the internet**. By leveraging search engines (specifically DuckDuckGo in its current implementation), this tool enables the AI to access up-to-date external knowledge, answer factual questions, and gather information for various tasks.

This module is crucial for extending the AI's knowledge base beyond its training data and for providing real-time information.

## Key Responsibilities and Features

1.  **Web Search Execution (`search`)**:
    *   Takes a `query` string and an optional `num_results` parameter.
    *   Constructs a search URL for DuckDuckGo's HTML interface.
    *   Sends an HTTP GET request to the search engine.
    *   Parses the HTML response to extract search results, including `title`, `snippet`, and `url` for each result.

2.  **DuckDuckGo Integration**: 
    *   Specifically designed to interact with DuckDuckGo's HTML search interface, which can be useful for programmatic access without requiring complex API keys.

3.  **Configurable Parameters**: 
    *   The `search_url_template` and `user_agent` can be configured via a `system_config.yaml` file, allowing for flexibility in search engine choice or request headers.

4.  **Robust Error Handling**: 
    *   Includes error handling for network issues (`requests.exceptions.RequestException`) and HTTP status errors, ensuring graceful failure and informative error messages.

5.  **HTML Parsing**: 
    *   Utilizes the `BeautifulSoup` library to efficiently parse the HTML content of search results and extract structured information.

## How it Works

When the `search` method is called, it formats the input query into a URL for DuckDuckGo. It then sends an HTTP request with a specified user agent. Upon receiving the HTML response, `BeautifulSoup` is used to navigate the HTML structure and extract elements corresponding to search result titles, snippets, and URLs. These extracted details are then returned as a list of dictionaries.

## Integration with Other Modules

-   **`DailyLanguageModel`**: The `DailyLanguageModel` would be responsible for identifying user intent for web search and extracting the search query.
-   **`RAGManager`**: The results from the `WebSearchTool` could be fed into the `RAGManager` to augment LLM responses with up-to-date information.
-   **`ProjectCoordinator`**: Complex tasks requiring external research or information gathering would leverage this tool as a sub-step.
-   **`KnowledgeGraph`**: Information retrieved from web searches could potentially be used to update or expand the AI's internal `KnowledgeGraph`.

## Code Location

`src/tools/web_search_tool.py`
