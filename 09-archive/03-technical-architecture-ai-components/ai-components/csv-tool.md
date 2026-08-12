# CSV Tool: Data Analysis for Structured Data

## Overview

The `CsvTool` (`src/tools/csv_tool.py`) is a specialized utility within the Unified-AI-Project that enables the AI to **perform basic analysis on CSV (Comma Separated Values) data**. It provides a straightforward interface for processing tabular data, making it accessible for AI-driven insights and operations.

This tool is crucial for tasks involving data interpretation, summarization, and quick structural checks of structured datasets.

## Key Responsibilities and Features

1.  **CSV Data Ingestion**: 
    *   Accepts CSV content as a raw string, allowing for flexible input from various sources.

2.  **Query-Based Analysis (`analyze`)**: 
    *   Processes the CSV data based on natural language queries.
    *   Currently supports the following queries:
        *   `"summarize"`: Returns a statistical summary of the DataFrame (e.g., count, mean, std, min, max for numerical columns).
        *   `"columns"`: Lists all column names present in the CSV.
        *   `"shape"`: Provides the dimensions of the CSV data (number of rows and columns).

3.  **Robust Error Handling**: 
    *   Includes `try-except` blocks to gracefully handle potential errors during CSV parsing or data analysis (e.g., malformed CSV, unsupported queries).

4.  **Pandas Integration**: 
    *   Leverages the powerful `pandas` library for efficient data manipulation and analysis, converting the input CSV string into a DataFrame.

## How it Works

The `analyze` method of the `CsvTool` takes a CSV content string and a natural language query. It first uses `pandas.read_csv` to parse the string into a DataFrame. Then, based on keywords in the `query`, it performs the requested operation (e.g., `df.describe()`, `df.columns.tolist()`, `df.shape`). The result is returned in a structured dictionary, indicating success or failure and providing the analysis output or an error message.

## Integration with Other Modules

-   **`ToolDispatcher`**: The `ToolDispatcher` would route user queries related to CSV analysis to the `CsvTool`.
-   **`DailyLanguageModel`**: The `DailyLanguageModel` would be responsible for identifying user intent for CSV analysis and extracting the `csv_content` and `query` parameters.
-   **`DataAnalysisAgent`**: The `DataAnalysisAgent` (if implemented) would likely utilize the `CsvTool` as its core capability for processing structured data.
-   **`ProjectCoordinator`**: Complex tasks involving data processing or reporting could leverage the `CsvTool` for specific steps.

## Code Location

`src/tools/csv_tool.py`
