# Frontend-Backend Connection Flow

This document illustrates the data flow from a user interaction in the Electron/React frontend to the FastAPI backend and back.

```mermaid
sequenceDiagram
    participant User
    participant ReactUI as React UI Component (e.g., Chat.tsx)
    participant APIModule as Frontend API Module (e.g., api/chat.ts)
    participant ElectronMain as Electron Main Process (main.js)
    participant FastAPI as FastAPI Backend (main_api_server.py)
    participant CoreServices as Core AI Services (e.g., DialogueManager)

    User->>ReactUI: Types message and clicks "Send"
    ReactUI->>APIModule: Calls sendMessage(text, sessionId)
    APIModule->>FastAPI: POST /api/v1/chat with JSON body
    Note over FastAPI: The HTTP request is received by the FastAPI server.
    FastAPI->>CoreServices: Gets DialogueManager instance and calls get_simple_response(text, ...)
    CoreServices->>FastAPI: Returns AI response text
    FastAPI->>APIModule: Responds with 200 OK and JSON payload containing AI response
    APIModule->>ReactUI: Returns AI response data to the component
    ReactUI->>User: Updates state, displaying the AI's message in the chat window
```
