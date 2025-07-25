# Models and Tools

This document provides an overview of the models and tools used in the Unified AI Project.

## Models

### Mathematics

*   **Math Model**
    *   **Description:** The math model is a lightweight model that can be used to solve basic arithmetic problems.
    *   **Location:** `src/tools/math_model/`
    *   **Status:** Built-in
    *   **Usage:** The math model can be used through the `math_tool` tool.

### Logic

*   **Logic Model**
    *   **Description:** The logic model is a lightweight model that can be used to solve basic logic problems.
    *   **Location:** `src/tools/logic_model/`
    *   **Status:** Built-in
    *   **Usage:** The logic model can be used through the `logic_tool` tool.

### Computer Vision

*   **Image Recognition Model**
    *   **Description:** The image recognition model can be used to recognize images using template matching.
    *   **Location:** `src/tools/image_recognition_tool.py`
    *   **Status:** Downloadable
    *   **Usage:** The image recognition model can be used through the `image_recognition_tool` tool.

### Natural Language Processing

*   **Speech-to-Text Model**
    *   **Description:** The speech-to-text model can be used to recognize speech from an audio file.
    *   **Location:** `src/tools/speech_to_text_tool.py`
    *   **Status:** Downloadable
    *   **Usage:** The speech-to-text model can be used through the `speech_to_text_tool` tool.

*   **Natural Language Generation Model**
    *   **Description:** The natural language generation model can be used to generate text from a prompt.
    *   **Location:** `src/tools/natural_language_generation_tool.py`
    *   **Status:** Downloadable
    *   **Usage:** The natural language generation model can be used through the `natural_language_generation_tool` tool.

### Game

*   **Game**
    *   **Description:** A GBA-style life simulation game.
    *   **Location:** `src/game/`
    *   **Status:** Built-in
    *   **Usage:** The game can be played through the Electron app.

## Tools

### Mathematics

*   **Math Tool**
    *   **Description:** The math tool can be used to solve basic arithmetic problems.
    *   **Location:** `src/tools/math_tool.py`
    *   **Status:** Completed
    *   **Usage:** The math tool can be used through the `ToolDispatcher`.

*   **Calculator Tool**
    *   **Description:** The calculator tool can be used to calculate the result of a mathematical expression.
    *   **Location:** `src/tools/calculator_tool.py`
    *   **Status:** Completed
    *   **Usage:** The calculator tool can be used through the `ToolDispatcher`.

### Logic

*   **Logic Tool**
    *   **Description:** The logic tool can be used to solve basic logic problems.
    *   **Location:** `src/tools/logic_tool.py`
    *   **Status:** Completed
    *   **Usage:** The logic tool can be used through the `ToolDispatcher`.

### Computer Vision

*   **Image Recognition Tool**
    *   **Description:** The image recognition tool can be used to recognize images using template matching.
    *   **Location:** `src/tools/image_recognition_tool.py`
    *   **Status:** Completed
    *   **Usage:** The image recognition tool can be used through the `ToolDispatcher`.

### Natural Language Processing

*   **Speech-to-Text Tool**
    *   **Description:** The speech-to-text tool can be used to recognize speech from an audio file.
    *   **Location:** `src/tools/speech_to_text_tool.py`
    *   **Status:** Completed
    *   **Usage:** The speech-to-text tool can be used through the `ToolDispatcher`.

*   **Natural Language Generation Tool**
    *   **Description:** The natural language generation tool can be used to generate text from a prompt.
    *   **Location:** `src/tools/natural_language_generation_tool.py`
    *   **Status:** Completed
    *   **Usage:** The natural language generation tool can be used through the `ToolDispatcher`.

### Web

*   **Web Search Tool**
    *   **Description:** The web search tool can be used to search the web for a given query.
    *   **Location:** `src/tools/web_search_tool.py`
    *   **Status:** Completed
    *   **Usage:** The web search tool can be used through the `ToolDispatcher`.

### File System

*   **File System Tool**
    *   **Description:** The file system tool can be used to perform file system operations, such as listing files, reading files, and writing files.
    *   **Location:** `src/tools/file_system_tool.py`
    *   **Status:** Completed
    *   **Usage:** The file system tool can be used through the `ToolDispatcher`.
