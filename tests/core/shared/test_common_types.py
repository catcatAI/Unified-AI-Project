"""core.shared.types.common_types 共享型別定義測試"""

from apps.backend.src.core.shared.types.common_types import (
    CritiqueResult,
    DialogueMemoryEntryMetadata,
    DialogueTurn,
    HAMDataPackageInternal,
    HAMMemoryResult,
    LLMConfig,
    LLMModelInfo,
    LLMProviderOllamaConfig,
    LLMProviderOpenAIConfig,
    OperationalConfig,
    OverwriteDecision,
    ParsedToolIODetails,
    PendingHSPTaskInfo,
    ServiceAdvertisement,
    ServiceInstanceHealth,
    ServiceQuery,
    ServiceStatus,
    ServiceType,
    ToolDispatcherResponse,
)


class TestServiceStatus:
    def test_enum_members(self):
        assert ServiceStatus.HEALTHY.value == 2
        assert ServiceStatus.UNHEALTHY.value == 3
        assert ServiceStatus.DEGRADED.value == 6

    def test_all_states(self):
        names = {s.name for s in ServiceStatus}
        assert names == {
            "UNKNOWN",
            "STARTING",
            "HEALTHY",
            "UNHEALTHY",
            "STOPPING",
            "STOPPED",
            "DEGRADED",
        }


class TestServiceType:
    def test_enum_members(self):
        assert ServiceType.HSP_NODE.value == "hsp_node"
        assert ServiceType.CORE_AI_COMPONENT.value == "core_ai_component"
        assert ServiceType.EXTERNAL_API.value == "external_api"


class TestServiceTypes:
    def test_service_advertisement_fields(self):
        for field in (
            "service_id",
            "service_name",
            "service_type",
            "service_version",
            "endpoint_url",
            "metadata",
            "status",
            "last_seen_timestamp",
            "ttl",
        ):
            assert field in ServiceAdvertisement.__annotations__

    def test_service_query_fields(self):
        for field in ("service_type", "service_name", "min_version", "status_filter"):
            assert field in ServiceQuery.__annotations__

    def test_service_instance_health_fields(self):
        for field in ("service_id", "instance_id", "status", "last_heartbeat"):
            assert field in ServiceInstanceHealth.__annotations__


class TestToolDispatcherResponse:
    def test_status_literal(self):
        assert "success" in ToolDispatcherResponse.__annotations__["status"].__args__
        assert "failure_tool_not_found" in ToolDispatcherResponse.__annotations__["status"].__args__
        assert "payload" in ToolDispatcherResponse.__annotations__


class TestLLMConfig:
    def test_fields(self):
        for field in ("model_name", "api_key", "base_url", "temperature", "max_tokens"):
            assert field in LLMConfig.__annotations__


class TestDialogueTypes:
    def test_dialogue_turn_fields(self):
        for field in ("speaker", "text", "timestamp", "metadata"):
            assert field in DialogueTurn.__annotations__

    def test_pending_hsp_task_info_fields(self):
        for field in (
            "user_id",
            "session_id",
            "original_query_text",
            "request_timestamp",
            "capability_id",
            "target_ai_id",
            "expected_callback_topic",
            "request_type",
        ):
            assert field in PendingHSPTaskInfo.__annotations__

    def test_operational_config_fields(self):
        for field in ("timeouts", "learning_thresholds", "max_dialogue_history"):
            assert field in OperationalConfig.__annotations__


class TestDialogueMemoryTypes:
    def test_critique_result_fields(self):
        for field in ("score", "reason", "suggested_alternative"):
            assert field in CritiqueResult.__annotations__

    def test_memory_entry_metadata_fields(self):
        for field in (
            "speaker",
            "timestamp",
            "user_input_ref",
            "sha256_checksum",
            "critique",
            "user_feedback_explicit",
            "learning_weight",
        ):
            assert field in DialogueMemoryEntryMetadata.__annotations__

    def test_parsed_tool_io_fields(self):
        for field in ("suggested_method_name", "parameters", "return_type"):
            assert field in ParsedToolIODetails.__annotations__


class TestOverwriteDecision:
    def test_enum_members(self):
        assert OverwriteDecision.PREVENT_OVERWRITE.value == "prevent_overwrite"
        assert OverwriteDecision.OVERWRITE_EXISTING.value == "overwrite_existing"
        assert OverwriteDecision.MERGE_IF_APPLICABLE.value == "merge_if_applicable"


class TestLLMInterfaceTypes:
    def test_ollama_config_requires_base_url(self):
        assert "base_url" in LLMProviderOllamaConfig.__required_keys__

    def test_openai_config_requires_api_key(self):
        assert "api_key" in LLMProviderOpenAIConfig.__required_keys__

    def test_llm_model_info_fields(self):
        for field in ("id", "provider", "name", "description", "size_bytes"):
            assert field in LLMModelInfo.__annotations__


class TestHAMMemoryTypes:
    def test_ham_memory_result_dataclass(self):
        result = HAMMemoryResult(
            memories=[{"id": "m1"}],
            confidence_scores=[0.9],
            total_count=1,
            query_metadata={"query": "q"},
        )
        assert result.total_count == 1
        assert result.memories[0]["id"] == "m1"

    def test_ham_data_package_fields(self):
        for field in (
            "package_id",
            "data_type",
            "content",
            "metadata",
            "timestamp",
            "source_ai_id",
            "confidence_score",
        ):
            assert field in HAMDataPackageInternal.__annotations__
