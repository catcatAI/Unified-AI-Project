# Heterogeneous Synchronization Protocol (HSP) Specification

This directory contains the detailed specification for the Heterogeneous
Synchronization Protocol (HSP), broken down into manageable sections.

## Core Specification

1.  **[Overview and Core Concepts](01-overview-and-concepts.md)**
    - Introduces the purpose, goals, and guiding principles of HSP.
    - Defines core concepts like HSP Participant AI (HPA).

2.  **[Message Envelope and Communication Patterns](02-message-envelope-and-patterns.md)**
    - Details the standard HSP message envelope.
    - Describes the primary communication patterns (Pub/Sub, Req/Rep).

3.  **[Interaction Logic and Network Services](03-interaction-logic-and-services.md)**
    - Explains higher-level logic, including AI discovery, trust, and conflict
      resolution.

4.  **[Transport and Future Considerations](04-transport-and-future.md)**
    - Discusses transport-agnosticism and future versioning.

## Message Payloads

The detailed structure of data payloads is in the
[message-payloads](message-payloads/README.md) directory. This includes
definitions for:

- `Fact` and `Belief`
- `CapabilityAdvertisement` and `TaskRequest`/`TaskResult`
- `EnvironmentalState` and `AIStateSynchronization`
