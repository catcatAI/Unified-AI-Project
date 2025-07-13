```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant ElectronApp
    participant MainAPIServer
    participant DialogueManager
    participant LearningManager
    participant HAM
    participant ContentAnalyzer
    participant HSPConnector

    User->>CLI: "query: Hello"
    CLI->>DialogueManager: get_simple_response("Hello")
    DialogueManager->>LearningManager: process_and_store_learnables("Hello")
    LearningManager->>HAM: store_experience("Hello")
    LearningManager->>ContentAnalyzer: process_hsp_fact_content("Hello")
    ContentAnalyzer->>HAM: store_experience("Hello")
    DialogueManager->>HSPConnector: publish_fact("Hello")
    DialogueManager-->>CLI: "Miko: Hello there!"
    CLI-->>User: "Miko: Hello there!"

    User->>ElectronApp: "Hello"
    ElectronApp->>MainAPIServer: /api/v1/query
    MainAPIServer->>DialogueManager: get_simple_response("Hello")
    DialogueManager->>LearningManager: process_and_store_learnables("Hello")
    LearningManager->>HAM: store_experience("Hello")
    LearningManager->>ContentAnalyzer: process_hsp_fact_content("Hello")
    ContentAnalyzer->>HAM: store_experience("Hello")
    DialogueManager->>HSPConnector: publish_fact("Hello")
    DialogueManager-->>MainAPIServer: "Miko: Hello there!"
    MainAPIServer-->>ElectronApp: "Miko: Hello there!"
    ElectronApp-->>User: "Miko: Hello there!"
```
