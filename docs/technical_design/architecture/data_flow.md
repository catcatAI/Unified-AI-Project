```mermaid
sequenceDiagram
    participant User
    participant ReactUI as React UI (in Electron)
    participant APIModule as Frontend API Module
    participant MainAPIServer as FastAPI Server
    participant DialogueManager
    participant HSPConnector
    participant LearningManager
    participant HAM

    User->>ReactUI: Enters "Hello" in Chat view
    ReactUI->>APIModule: sendMessage("Hello")
    APIModule->>MainAPIServer: POST /api/v1/chat
    MainAPIServer->>DialogueManager: get_simple_response("Hello")

    subgraph AI Core Processing
        DialogueManager->>LearningManager: process_and_store_learnables("Hello")
        LearningManager->>HAM: store_experience(...)
        DialogueManager->>HSPConnector: publish_fact(...)
    end

    DialogueManager-->>MainAPIServer: Returns "AI: Hello back!"
    MainAPIServer-->>APIModule: Returns JSON with response
    APIModule-->>ReactUI: Returns response text
    ReactUI-->>User: Displays "AI: Hello back!"
```

[See detailed flow here](./frontend_backend_flow.md)
