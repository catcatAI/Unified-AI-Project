# CsvTool: Basic Analysis of CSV Data

## Overview

This document provides an overview of the `CsvTool` module (`src/tools/csv_tool.py`). This tool is designed to provide the AI with the capability to perform basic analysis on data provided in CSV (Comma-Separated Values) format.

## Purpose

The `CsvTool` is a fundamental tool for data analysis tasks. It allows the AI to ingest and understand tabular data from CSV content, which is a common format for data exchange. This enables the AI to answer questions about datasets, provide summaries, and perform other basic data analysis operations.

## Key Responsibilities and Features

*   **CSV Parsing**: Utilizes the powerful `pandas` library to parse CSV data from a string into a DataFrame. This allows for robust handling of various CSV formats.
*   **Basic Analysis (`analyze`)**:
    *   Accepts `csv_content` (as a string) and a `query` (a natural language command) as input.
    *   Supports a set of basic analysis queries:
        *   `"summarize"`: Returns a descriptive statistical summary of the data (using `df.describe()`).
        *   `"columns"`: Returns a list of the column names in the dataset.
        *   `"shape"`: Returns the dimensions of the dataset (number of rows and columns).
*   **Error Handling**: Includes `try-except` blocks to gracefully handle potential errors during CSV parsing or analysis and returns a structured error message to the caller.

## How it Works

The `analyze` method is the core of the tool. It takes a string of CSV content and a query string. It uses Python's `io.StringIO` to treat the input string as a file, which is then passed to `pandas.read_csv` to be parsed into a DataFrame. Based on the user's query, the tool then performs a simple operation on the resulting DataFrame (e.g., describing the data, listing columns) and returns the result as a string within a structured dictionary.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool is designed to be invoked by the `ToolDispatcher` when the AI's intent is to analyze CSV data. The `ToolDispatcher` would extract the `csv_content` and the `query` from the user's request and pass them to this tool.
*   **`pandas`**: The core external library that provides the data manipulation and analysis capabilities (i.e., the DataFrame object and its methods).

## Code Location

`src/tools/csv_tool.py`