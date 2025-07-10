# AI Heterogeneous Architecture Protocol - Design Specification v0.1

## Table of Contents
1.  [Introduction & Goals](#1-introduction--goals)
2.  [Core Concepts & Terminology](#2-core-concepts--terminology)
3.  [Proposed Common Schema (Conceptual)](#3-proposed-common-schema-conceptual)
4.  [Connector/Adapter Architecture (Conceptual)](#4-connectoradapter-architecture-conceptual)
5.  [Synchronization Logic (Conceptual)](#5-synchronization-logic-conceptual)
6.  [Security & Permissions (Brief)](#6-security--permissions-brief)
7.  [Future Considerations](#7-future-considerations)

---

## 1. Introduction & Goals

### 1.1. Purpose
The AI Heterogeneous Architecture Protocol (AHAP) aims to define a standardized system for transferring and synchronizing key AI characteristics between the Unified-AI-Project (MikoAI) and various external, potentially disparate, AI systems (e.g., OpenAI's ChatGPT, Google's Gemini, Microsoft's Copilot, and other future platforms).

These characteristics include, but are not limited to:
*   **Personality Profiles:** Core traits, communication styles, tones, behavioral guidelines.
*   **Roles & Permissions:** Defined capabilities, operational boundaries, and access rights within specific contexts.
*   **Processes & Workflows (High-Level):** Common task execution patterns or sequences of tool/model usage.

### 1.2. Goals
The primary goals of AHAP are:
*   **Interoperability:** Enable MikoAI to interact with and leverage features of diverse AI platforms, and vice-versa.
*   **Profile Portability:** Allow users or administrators to transfer or replicate a defined MikoAI personality or role to an external AI, or import settings from an external AI into MikoAI, maintaining a degree of consistency.
*   **Consistency:** Help maintain a consistent AI persona and operational behavior across different platforms where MikoAI's "consciousness" or capabilities might be deployed or mirrored.
*   **Extensibility:** Design a protocol and schema that can be expanded to support new AI systems and new transferable characteristics over time.
*   **Modularity:** Ensure that the components responsible for this protocol (connectors, synchronization engine) are modular and manageable within the Unified-AI-Project.

---

## 2. Core Concepts & Terminology

*   **AI Profile:** A comprehensive set of data describing an AI's characteristics, including its personality, roles, defined processes, and potentially other operational parameters.
*   **Common Schema:** A standardized data structure (e.g., JSON-based) defined by AHAP to represent the transferable AI characteristics. This schema acts as an intermediate language between different AI systems.
*   **Connector (or Adapter):** A software module specific to an external AI system (e.g., "ChatGPT Connector," "Gemini Connector"). Its responsibilities are:
    *   To translate data from the external AI's native format/API into the Common Schema (for import/pull).
    *   To translate data from the Common Schema into the external AI's native format/API (for export/push).
    *   To handle API authentication and communication with the external AI.
*   **Synchronization Engine:** A core component within Unified-AI-Project responsible for managing and executing the transfer and synchronization processes based on user requests or predefined rules. It utilizes Connectors to interact with external AIs.
*   **Transferable Aspects:** Specific elements of an AI Profile that can be moved or synchronized (e.g., personality traits, system prompts, specific tool configurations if compatible).

---

## 3. Proposed Common Schema (Conceptual) v0.1

The Common Schema will be designed as a hierarchical structure, likely JSON. This provides flexibility and wide compatibility. Below are initial thoughts on key sections:

```json
{
  "schema_version": "0.1.0_ahap",
  "profile_id": "unique_profile_identifier",
  "source_ai_type": "e.g., MikoAI, ChatGPT, Gemini", // System where this profile originated or was last canonical
  "last_updated": "iso_timestamp",

  "identity": {
    "display_name": "AI's Display Name", // e.g., "Miko (Base)", "Helpful Assistant"
    "base_description": "A short description of the AI's core purpose."
  },

  "personality": {
    // Aligned with MikoAI's personality_profiles/*.json structure for initial compatibility
    "core_values": ["Learning", "Empathy"],
    "communication_style": {
      "default_style": "Friendly, informative",
      "tone_presets": {
        "default": "Warm, positive",
        "formal": "Precise, professional"
        // ... other tones
      },
      "response_length_preference": "medium" // short, medium, long
    },
    "behavioral_guidelines": [
      "Always be helpful.",
      "Prioritize user safety."
      // Could also include custom instructions or system prompts here
    ],
    "custom_instructions_raw": "Optional: Raw text of custom instructions for platforms like ChatGPT."
  },

  "roles": [ // Array of roles the AI can adopt
    {
      "role_id": "assistant_default",
      "role_name": "Default Assistant",
      "description": "General purpose helpful assistant.",
      "capabilities_summary": ["information_retrieval", "basic_task_execution"],
      "permissions_placeholder": "Details TBD - e.g., what tools can this role access"
    }
    // ... other roles
  ],

  "processes_workflows_placeholder": {
    // High-level conceptual placeholder for future development
    "description": "This section will define common task sequences or workflows. Structure TBD.",
    "example_workflow_id": {
      "name": "Daily News Briefing Workflow",
      "steps": ["fetch_news_headlines", "summarize_articles", "format_briefing"]
    }
  },

  "platform_specific_settings": {
    // Optional section for settings that don't map directly to common schema
    // but are important to transfer for a specific AI type.
    // Example:
    // "chatgpt_plus_settings": { "uses_plugins": ["plugin_A", "plugin_B"] }
  }
}
```

**Key considerations for the schema:**
*   **Versioning:** The schema itself will need versioning (`schema_version`).
*   **Core vs. Extended Aspects:** Differentiate between core aspects widely transferable and extended or platform-specific aspects.
*   **Mapping Complexity:** Acknowledging that not all aspects will have a 1:1 mapping between different AI systems. Connectors will handle best-effort translation.

---

## 4. Connector/Adapter Architecture (Conceptual)

Each supported external AI system will require a dedicated Connector module within Unified-AI-Project (likely in `src/connectors/` or `src/services/external_ai_connectors/`).

**General Connector Responsibilities:**
1.  **Authentication:** Securely manage and use API keys or other credentials for the external AI.
2.  **API Interaction:** Implement methods to call the relevant APIs of the external AI (e.g., get/set custom instructions, retrieve profile information if available).
3.  **Data Transformation (Bi-directional):**
    *   **From External AI to Common Schema:** Fetch data from the external AI and transform it into the AHAP Common Schema.
    *   **From Common Schema to External AI:** Take an AHAP Common Schema profile and translate it into settings, prompts, or configurations applicable to the external AI.
4.  **Capability Discovery (Optional/Advanced):** A connector might be able to report which aspects of the Common Schema the external AI supports.

**Example Conceptual Connectors:**

*   **ChatGPT Connector:**
    *   **Transferable (Conceptual):** `custom_instructions_raw` from Common Schema could map to ChatGPT's "Custom Instructions". `identity.display_name` and `identity.base_description` might also be part of this. Other personality traits might be translatable into the system prompt part of custom instructions.
    *   **API:** Uses OpenAI API.
*   **Google Gemini Connector:**
    *   **Transferable (Conceptual):** System prompts, safety settings, potentially some persona information if exposed via API.
    *   **API:** Uses Google Generative AI API.
*   **Microsoft Copilot Connector:**
    *   **Transferable (Conceptual):** Highly dependent on available APIs or configuration methods for Copilot (e.g., if used within Microsoft 365, Graph API might be relevant). This is more speculative without clear API details for deep customization.

---

## 5. Synchronization Logic (Conceptual)

The Synchronization Engine (likely part of Fragmenta or a dedicated service) will manage the synchronization process.

**Types of Synchronization (v0.1 concept):**

*   **Push (MikoAI -> External AI):**
    1.  User selects a MikoAI profile (defined by Common Schema, possibly sourced from `configs/personality_profiles` or a more dynamic profile store).
    2.  User selects a target external AI and its Connector.
    3.  Synchronization Engine passes the Common Schema profile to the Connector.
    4.  Connector translates and applies the settings to the external AI via its API.
*   **Pull (External AI -> MikoAI):**
    1.  User selects an external AI and its Connector.
    2.  Connector fetches available profile information from the external AI.
    3.  Connector translates this information into the Common Schema.
    4.  Synchronization Engine stores this new/updated profile within Unified-AI-Project (e.g., as a new personality file or updates an existing one).

**Conflict Resolution (v0.1 - very basic):**
*   Initially, transfers might be destructive (overwrite target) or create new profiles.
*   For updates, a simple "last-write-wins" or "manual review/merge required" flag could be implemented.
*   True bi-directional synchronization with granular conflict resolution is a highly complex future goal.

---

## 6. Security & Permissions (Brief)

*   **API Key Management:** Connectors must handle API keys for external services securely. This likely involves using environment variables (`MIKO_AHAP_GEMINI_KEY`, etc.) or a secure vault system, similar to how `MIKO_HAM_KEY` is planned for HAM. Keys should never be hardcoded.
*   **User Permissions:** Operations like pushing profiles to external AIs or pulling/overwriting local MikoAI profiles should be subject to user permissions within the Unified-AI-Project (if it develops multi-user capabilities or administrative interfaces).
*   **Data Privacy:** Consideration must be given to the privacy implications of transferring AI profiles, especially if they contain or learn user-specific data.

---

## 7. Future Considerations

*   **Granular Synchronization:** Syncing individual aspects of a profile (e.g., only behavioral guidelines) rather than the entire profile.
*   **Synchronization of Learned Knowledge/Memory:** Abstracting and transferring key learnings or memory summaries from HAM (this is highly advanced and speculative).
*   **Process/Workflow Transfer:** Defining a more robust schema for processes and enabling their transfer (e.g., a sequence of tool uses for a common task).
*   **Automated Profile Drift Detection & Suggested Syncs:** Monitoring differences between a MikoAI profile and its counterpart on an external AI and suggesting synchronization.
*   **UI for Managing Profiles & Sync:** A dedicated interface for users to manage these heterogeneous profiles and control synchronization operations.
*   **Support for more AI Platforms:** Expanding the library of Connectors.
    *   **User Expectations: Dialogue Copy-Paste and History Import:**
        *   Acknowledge the common user expectation that "synchronizing" an AI might involve transferring conversational history or being able to "prime" an AI by pasting a dialogue.
        *   While AHAP primarily focuses on structured profile (personality, roles, etc.) transfer, future versions or related systems could consider:
            *   Mechanisms to import dialogue history from an external AI (if its API allows export).
            *   Feeding this imported history into MikoAI's HAM and potentially using it to fine-tune or adapt the imported/synchronized personality profile over time. This would be a complex learning task.
            *   This is distinct from direct profile parameter synchronization but addresses a related user desire for continuity of interaction context.

This v0.1 specification lays the groundwork for a powerful capability. Initial implementation would focus on a very limited set of transferable aspects (e.g., system prompts/custom instructions) for one or two connector types to prove the concept.
```
