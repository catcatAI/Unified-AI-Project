# HSP: 4. Transport and Future Considerations

## 4.1. Network & Transport

HSP v0.1 is **transport-agnostic**. The protocol defines the data structures
(messages and envelopes), but not how they are physically transmitted over a
network.

### 4.1.1. Potential Transports

Implementers can choose the transport that best fits their needs. Common choices
include:

- **WebSockets:** For persistent, bidirectional connections suitable for
  real-time interaction.
- **HTTP/2 or HTTP/3:** For efficient Request/Response patterns.
- **gRPC:** For high-performance, cross-language services using Protocol
  Buffers.
- **MQTT:** For lightweight, broker-based Publish/Subscribe, ideal for IoT or
  decentralized systems.

For a detailed analysis of MQTT broker options, see the
[MQTT Broker Alternatives Analysis](../../../../07-research/experimental/mqtt-broker-analysis.md).

## 4.2. Versioning

A robust versioning strategy is essential for the evolution of the protocol.

- **Envelope Version:** The `hsp_envelope_version` field tracks changes to the
  envelope structure itself.
- **Protocol Version:** The `protocol_version` field in the envelope refers to
  the overall HSP specification version.
- **Message Type Version:** Message types should be versioned directly in their
  name string (e.g., `HSP::Fact_v0.1`, `HSP::Fact_v0.2`).

Semantic versioning (MAJOR.MINOR.PATCH) is recommended for all version numbers.

## 4.3. Future Enhancements

Future versions of the HSP specification may include:

- **Advanced Security:** End-to-end encryption, granular access control
  policies, and standardized identity management.
- **Semantic Mapping Services:** A dedicated network service for translating
  between different AI ontologies.
- **Formal Consensus Algorithms:** Standardized protocols for reaching agreement
  on conflicting information.
- **Distributed Ledger Integration:** For tracking critical transactions or AI
  reputations in a tamper-proof manner.
- **Standardized Error Ontology:** A comprehensive dictionary of error codes and
  their meanings.
