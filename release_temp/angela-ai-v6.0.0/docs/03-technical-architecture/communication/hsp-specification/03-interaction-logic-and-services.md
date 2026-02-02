# HSP: 3. Interaction Logic and Network Services

This section describes higher-level interaction patterns and conceptual network
services that facilitate a functional HSP ecosystem.

## 3.1. AI Registration & Discovery

- **Mechanism (v0.1 Proposal):**
  1.  AIs publish their `CapabilityAdvertisement` messages to a well-known topic
      (e.g., `hsp/capabilities/advertisements/all`).
  2.  A network "directory" service (itself an HPA) subscribes to this topic,
      collecting all advertisements.
  3.  Other AIs can query this directory service to find AIs with specific
      capabilities.
- **Discovery Query Example:**
  - `message_type`: `HSP::CapabilityDiscoveryQuery_v0.1`
  - `payload`:
    `{"capability_tags": ["nlp", "translation"], "min_trust_score": 0.7}`
- **Discovery Response Example:**
  - `message_type`: `HSP::CapabilityDiscoveryResponse_v0.1`
  - `payload`: `{"capabilities": [CapabilityAdvertisement_object_1, ...]}`

## 3.2. Trust Establishment & Management (Conceptual)

Trust is critical but complex. Version 0.1 outlines the basic hooks for a trust
system, which will be expanded in future versions.

- **Sender Authenticity:** The `security_parameters.signature` field in the
  message envelope can be used to verify the sender's identity, assuming a
  public key infrastructure (e.g., a DID registry) is available.
- **Reputation:** While not formally part of the protocol, AIs are expected to
  implement their own local reputation tracking based on the history of their
  interactions with other AIs.
- **Verifiable Credentials (VCs):** Future versions may incorporate VCs to allow
  AIs to present cryptographically verifiable claims about their capabilities or
  identity.

## 3.3. Conflict Resolution & Consensus

HSP's role is to _facilitate_ conflict resolution by providing the necessary
metadata, not to _enforce_ a specific resolution method. The final logic resides
within each AI.

- **Provided Metadata:** HSP messages for `Fact`s and `Belief`s include
  `source_ai_id`, `timestamp_created`, and `confidence_score`.
- **AI's Responsibility:** Each AI must implement its own logic for handling
  conflicting information (e.g., preferring newer data, data from more trusted
  sources, or data with higher confidence).
- **Future Support:** A `KnowledgePollRequest` message type may be introduced in
  the future for explicit consensus-seeking among a group of AIs.

### 3.3.1. Recommended Practices for Conflict Resolution

When an AI receives information, it should store it with additional internal
metadata to aid its reasoning process. This is internal to the AI and not part
of the HSP payload.

- **Key Internal Metadata:**
  - `hsp_sender_ai_id`: The peer who sent the message (for trust calculations).
  - `effective_confidence`: A calculated score combining the original confidence
    with trust in the sender.
  - `resolution_strategy_applied`: A record of how a conflict was resolved
    (e.g., "NEWEST_WINS", "TRUST_WEIGHTED_MERGE").
  - `conflicts_with_internal_ids`: Links to other pieces of information in the
    AI's memory that this data contradicts.
