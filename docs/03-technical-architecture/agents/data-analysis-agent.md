# DataAnalysisAgent: Specialized Agent for Data Analysis

## Overview

This document provides an overview of the `DataAnalysisAgent` module (`src/agents/data_analysis_agent.py`). This agent is a specialized sub-agent designed for analyzing data, with a particular focus on CSV files.

## Purpose

The `DataAnalysisAgent` provides the AI with the capability to perform data analysis tasks by leveraging the `CsvTool`. This agent can be delegated tasks that involve processing structured data, extracting insights, and generating summaries or specific data points from CSV content.

## Key Responsibilities and Features

*   **Inheritance from `BaseAgent`**: The `DataAnalysisAgent` inherits from `BaseAgent`, utilizing its foundational functionalities for service initialization, HSP network connection, and boilerplate task handling. This ensures consistency and reduces redundant code.
*   **Defined Capabilities**: The agent advertises a specific capability on the Heterogeneous Service Protocol (HSP) network, making its services discoverable by other AI components:
    *   **`analyze_csv_data`**: Analyzes provided CSV data based on a natural language query (e.g., 'summarize', 'columns', 'shape').
*   **Tool Integration**: Directly uses the `ToolDispatcher` to invoke the `analyze_csv` tool. This allows the agent to perform its core function without directly managing the `pandas` library or CSV parsing logic, promoting modularity.
*   **HSP Task Handling**: Overrides the `handle_task_request` method from `BaseAgent` to process incoming HSP tasks related to CSV data analysis. It extracts `csv_content` and `query` from the task payload, dispatches them to the `ToolDispatcher`, and sends back the analysis result as an HSP task result.

## How it Works

When the `DataAnalysisAgent` receives an HSP task request for its `analyze_csv_data` capability, it extracts the CSV content and the analysis query from the task payload. It then uses its `ToolDispatcher` instance to call the `analyze_csv` tool with these parameters. The result obtained from the `CsvTool` (which performs the actual data processing using `pandas`) is then formatted as an `HSPTaskResultPayload` and sent back to the original requester via the `HSPConnector`.

## Integration with Other Modules

*   **`BaseAgent`**: Provides the foundational framework for the agent, handling common lifecycle and communication aspects.
*   **`ToolDispatcher`**: Used to invoke the `analyze_csv` tool, acting as an intermediary between the agent's request and the tool's execution.
*   **`CsvTool`**: The actual tool that performs the CSV analysis (accessed indirectly via `ToolDispatcher`).
*   **HSP Communication Types**: Utilizes `HSPTaskRequestPayload`, `HSPTaskResultPayload`, and `HSPMessageEnvelope` for structured communication over the HSP network.

## Code Location

`src/agents/data_analysis_agent.py`