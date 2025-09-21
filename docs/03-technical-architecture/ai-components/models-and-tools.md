# Models and Tools

This document provides an overview of the models and tools used in the Unified
AI Project.

## Models

### Mathematics

- **Math Model**
  - **Description:** The math model is a lightweight model that can be used to
    solve basic arithmetic problems.
  - **Location:** `apps/backend/src/tools/math_model/`
  - **Status:** Built-in
  - **Usage:** The math model can be used through the `math_tool` tool.

### Logic

- **Logic Model**
  - **Description:** The logic model is a lightweight model that can be used to
    solve basic logic problems.
  - **Location:** `apps/backend/src/tools/logic_model/`
  - **Status:** Built-in
  - **Usage:** The logic model can be used through the `logic_tool` tool.

### Computer Vision

- **Image Recognition Model**
  - **Description:** The image recognition model can be used to recognize images
    using template matching.
  - **Location:** `apps/backend/src/tools/image_recognition_tool.py`
  - **Status:** Downloadable
  - **Usage:** The image recognition model can be used through the
    `image_recognition_tool` tool.

### Natural Language Processing

- **Multi-LLM Service**
  - **Description:** A unified interface for various large language models (LLMs) like OpenAI, Google Gemini, Anthropic Claude, etc.
  - **Location:** `apps/backend/src/services/multi_llm_service.py`
  - **Status:** Integrated
  - **Usage:** Used by `DialogueManager` and `ToolDispatcher` for natural language understanding and generation.

- **Speech-to-Text Model**
  - **Description:** The speech-to-text model can be used to recognize speech
    from an audio file.
  - **Location:** `apps/backend/src/tools/speech_to_text_tool.py`
  - **Status:** Integrated
  - **Usage:** The speech-to-text model can be used through the
    `speech_to_text_tool` tool.

### Game

- **Game**
  - **Description:** A GBA-style life simulation game.
  - **Location:** `apps/backend/src/game/`
  - **Status:** Built-in
  - **Usage:** The game can be played through the Electron app.

## Tools

### Mathematics

- **Math Tool**
  - **Description:** The math tool can be used to solve basic arithmetic
    problems.
  - **Location:** `apps/backend/src/tools/math_tool.py`
  - **Status:** Completed
  - **Usage:** The math tool can be used through the `ToolDispatcher`.



### Logic

- **Logic Tool**
  - **Description:** The logic tool can be used to solve basic logic problems.
  - **Location:** `apps/backend/src/tools/logic_tool.py`
  - **Status:** Completed
  - **Usage:** The logic tool can be used through the `ToolDispatcher`.

### Computer Vision

- **Image Recognition Tool**
  - **Description:** The image recognition tool can be used to recognize images
    using template matching.
  - **Location:** `apps/backend/src/tools/image_recognition_tool.py`
  - **Status:** Completed
  - **Usage:** The image recognition tool can be used through the
    `ToolDispatcher`.

### Natural Language Processing

- **Speech-to-Text Tool**
  - **Description:** The speech-to-text tool can be used to recognize speech
    from an audio file.
  - **Location:** `apps/backend/src/tools/speech_to_text_tool.py`
  - **Status:** Completed
  - **Usage:** The speech-to-text tool can be used through the `ToolDispatcher`.



### Web

- **Web Search Tool**
  - **Description:** The web search tool can be used to search the web for a
    given query.
  - **Location:** `apps/backend/src/tools/web_search_tool.py`
  - **Status:** Completed
  - **Usage:** The web search tool can be used through the `ToolDispatcher`.

### File System

- **File System Tool**
  - **Description:** The file system tool can be used to perform file system
    operations, such as listing files, reading files, and writing files.
  - **Location:** `apps/backend/src/tools/file_system_tool.py`
  - **Status:** Completed
  - **Usage:** The file system tool can be used through the `ToolDispatcher`.
