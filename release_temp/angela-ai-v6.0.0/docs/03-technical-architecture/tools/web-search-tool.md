# WebSearchTool: Searching the Web for Information

## Overview

This document provides an overview of the `WebSearchTool` module (`src/tools/web_search_tool.py`). Its primary function is to provide the AI with the ability to search the web for information using the DuckDuckGo search engine.

This tool is a critical component of the AI's ability to access real-time information, answer questions about current events, find specific facts, and gather context from online sources.

## Key Responsibilities and Features

*   **Web Scraping**: Utilizes the `requests` library to fetch search results from DuckDuckGo and the `BeautifulSoup` library to parse the resulting HTML. It extracts relevant information from the search results, including the title, snippet, and URL of each result.
*   **Configurable**: Loads its configuration from `system_config.yaml`, which allows for the easy customization of the `search_url_template` and the `user_agent` string. This makes the tool adaptable to changes in the search engine's HTML structure or to different search providers.
*   **Asynchronous Search (`search`)**: Provides an `async` method to perform a web search for a given `query`. It can be configured to return a specific number of results (`num_results`).
*   **Error Handling**: Includes basic error handling for network requests, ensuring that the tool can gracefully handle connection issues or other web-related errors.

## How it Works

The `WebSearchTool` constructs a search URL by formatting the `search_url_template` with the user's query. It then sends an HTTP GET request to this URL, using a configurable `User-Agent` to mimic a standard web browser. The HTML content of the search results page is then parsed using `BeautifulSoup`. The tool specifically looks for `div` elements with the class `result__body` and extracts the title, snippet, and URL from the `a` tags within these elements. The extracted information is collected into a list of dictionaries and returned to the caller.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool is designed to be invoked by the `ToolDispatcher` when the AI's intent is to search the web. The `ToolDispatcher` would extract the search query from the user's request and pass it to this tool.
*   **`WebSearchAgent`**: A specialized agent could be built around this tool to perform more complex web search tasks, such as multi-page scraping, deep-diving into search results, or summarizing information from multiple sources.
*   **External Libraries**: Relies on `requests` for making HTTP requests, `BeautifulSoup` for parsing HTML, and `PyYAML` for loading its configuration.

## Code Location

`src/tools/web_search_tool.py`