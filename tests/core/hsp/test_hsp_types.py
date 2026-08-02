"""core.hsp.types 協定類型定義測試"""

from apps.backend.src.core.hsp.types import (
    HSPCapability,
    HSPCommandPayload,
    HSPDiscoveryPayload,
    HSPEnvironmentalStatePayload,
    HSPEventPayload,
    HSPFactPayload,
    HSPHeartbeatPayload,
    HSPMessageEnvelope,
    HSPMessageEnvelopeBase,
    HSPNegativeAcknowledgementPayload,
    HSPNotificationPayload,
    HSPTask,
    HSPTaskRequestPayload,
    HSPTaskResultPayload,
)


class TestHSPEnvelopeBase:
    def test_has_protocol_fields(self):
        assert HSPMessageEnvelopeBase.__annotations__ is not None
        for field in (
            "payload",
            "message_type",
            "sender_ai_id",
            "recipient_ai_id",
            "timestamp_sent",
            "correlation_id",
        ):
            assert field in HSPMessageEnvelopeBase.__annotations__

    def test_message_envelope_has_all_required(self):
        for field in (
            "hsp_envelope_version",
            "message_id",
            "sender_ai_id",
            "recipient_ai_id",
            "message_type",
            "protocol_version",
            "communication_pattern",
        ):
            assert field in HSPMessageEnvelope.__annotations__


class TestHSPPayloadTypes:
    def test_fact_payload_fields(self):
        assert "statement_type" in HSPFactPayload.__annotations__
        assert "confidence_score" in HSPFactPayload.__annotations__
        assert "timestamp_created" in HSPFactPayload.__annotations__

    def test_heartbeat_payload_fields(self):
        assert "status" in HSPHeartbeatPayload.__annotations__

    def test_discovery_payload_fields(self):
        assert "capabilities" in HSPDiscoveryPayload.__annotations__

    def test_event_payload_fields(self):
        assert "event_type" in HSPEventPayload.__annotations__

    def test_command_payload_fields(self):
        assert "command_type" in HSPCommandPayload.__annotations__

    def test_notification_payload_fields(self):
        assert "notification_type" in HSPNotificationPayload.__annotations__

    def test_environmental_payload_fields(self):
        assert "phenomenon_type" in HSPEnvironmentalStatePayload.__annotations__

    def test_nack_payload_fields(self):
        assert "nack_timestamp" in HSPNegativeAcknowledgementPayload.__annotations__

    def test_capability_fields(self):
        assert "name" in HSPCapability.__annotations__

    def test_task_fields(self):
        assert "task_id" in HSPTask.__annotations__

    def test_task_request_fields(self):
        assert "request_id" in HSPTaskRequestPayload.__annotations__

    def test_task_result_fields(self):
        assert "result_id" in HSPTaskResultPayload.__annotations__
