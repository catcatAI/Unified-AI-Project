import pytest
import json
import asyncio
import tempfile
from pathlib import Path
try:
    from ai.token.token_validator import (
        TokenGenerationInfo,
        AttentionInfo,
        TokenTraceRecord,
        TokenValidator,
        TokenGenerationMonitor,
        validate_token_generation_real,
    )
except ImportError:
    pytest.skip("TokenGenerationInfo not available (stub module)", allow_module_level=True)


class TestTokenGenerationInfo:
    def test_create_minimal(self):
        info = TokenGenerationInfo(token="hello", position=0, probability=0.9)
        assert info.token == "hello"
        assert info.position == 0
        assert info.probability == 0.9
        assert info.attention_weights is None
        assert info.source_model == ""

    def test_create_full(self):
        info = TokenGenerationInfo(
            token="world",
            position=1,
            probability=0.8,
            attention_weights={"input": 0.5},
            source_model="gpt-4",
        )
        assert info.token == "world"
        assert info.attention_weights == {"input": 0.5}
        assert info.source_model == "gpt-4"


class TestAttentionInfo:
    def test_create_minimal(self):
        info = AttentionInfo(layer=0, head=0)
        assert info.layer == 0
        assert info.head == 0

    def test_create_full(self):
        info = AttentionInfo(
            layer=1, head=2, attention_weights={"a": 0.3, "b": 0.7}
        )
        assert info.layer == 1
        assert info.head == 2
        assert len(info.key_tokens) == 0


class TestTokenTraceRecord:
    def test_create_minimal(self):
        record = TokenTraceRecord(input_text="hello")
        assert record.input_text == "hello"
        assert record.total_tokens == 0
        assert record.generation_time == 0.0

    def test_create_with_tokens(self):
        tokens = [
            TokenGenerationInfo(token="a", position=0, probability=0.9),
            TokenGenerationInfo(token="b", position=1, probability=0.8),
        ]
        record = TokenTraceRecord(
            input_text="test", output_tokens=tokens, total_tokens=2
        )
        assert len(record.output_tokens) == 2
        assert record.total_tokens == 2


class TestTokenValidator:
    @pytest.mark.asyncio
    async def test_validate_valid_tokens(self):
        validator = TokenValidator()
        tokens = ["hello", "world"]
        probs = [0.9, 0.8]
        record = await validator.validate_token_generation(
            input_text="hi", generated_tokens=tokens, token_probabilities=probs
        )
        assert record.total_tokens == 2
        assert len(record.output_tokens) == 2
        assert "overall_valid" in record.metadata

    @pytest.mark.asyncio
    async def test_validate_low_probability_token(self):
        validator = TokenValidator()
        tokens = ["rare"]
        probs = [0.001]
        record = await validator.validate_token_generation(
            input_text="test", generated_tokens=tokens, token_probabilities=probs
        )
        assert len(validator.trace_records) == 1

    @pytest.mark.asyncio
    async def test_validate_with_attention(self):
        validator = TokenValidator()
        tokens = ["hello", "world"]
        probs = [0.9, 0.8]
        attention = [
            {"input_0": 0.4, "input_1": 0.6},
            {"input_0": 0.3, "input_1": 0.7},
        ]
        record = await validator.validate_token_generation(
            input_text="hi",
            generated_tokens=tokens,
            token_probabilities=probs,
            attention_weights=attention,
        )
        assert record.total_tokens == 2

    @pytest.mark.asyncio
    async def test_validate_single_token_below_threshold(self):
        validator = TokenValidator()
        info = TokenGenerationInfo(token="rare", position=0, probability=0.0001)
        valid = await validator._validate_single_token(info)
        assert valid is False

    @pytest.mark.asyncio
    async def test_validate_single_token_above_threshold(self):
        validator = TokenValidator()
        info = TokenGenerationInfo(token="common", position=0, probability=0.5)
        valid = await validator._validate_single_token(info)
        assert valid is True

    @pytest.mark.asyncio
    async def test_validate_single_token_high_attention_variance(self):
        validator = TokenValidator()
        info = TokenGenerationInfo(
            token="test",
            position=0,
            probability=0.5,
            attention_weights={"a": 10.0, "b": 0.0, "c": 0.0, "d": 0.0, "e": 0.0},
        )
        valid = await validator._validate_single_token(info)
        assert valid is False

    def test_probability_distribution_valid(self):
        validator = TokenValidator()
        trace = TokenTraceRecord(
            input_text="test",
            output_tokens=[
                TokenGenerationInfo(token="a", position=0, probability=0.5),
                TokenGenerationInfo(token="b", position=1, probability=0.6),
            ],
            total_tokens=2,
        )
        score = validator._validate_probability_distribution(trace)
        assert score == 1.0

    def test_probability_distribution_low_mean(self):
        validator = TokenValidator()
        trace = TokenTraceRecord(
            input_text="test",
            output_tokens=[
                TokenGenerationInfo(token="a", position=0, probability=0.01),
                TokenGenerationInfo(token="b", position=1, probability=0.02),
            ],
            total_tokens=2,
        )
        score = validator._validate_probability_distribution(trace)
        assert score == 0.3

    def test_probability_distribution_extreme_values(self):
        validator = TokenValidator()
        trace = TokenTraceRecord(
            input_text="test",
            output_tokens=[
                TokenGenerationInfo(token="a", position=0, probability=1.0),
                TokenGenerationInfo(token="b", position=1, probability=0.0),
            ],
            total_tokens=2,
        )
        score = validator._validate_probability_distribution(trace)
        assert score == 1.0  # std=0.5 doesn't exceed threshold

    def test_get_validation_report_empty(self):
        validator = TokenValidator()
        report = validator.get_validation_report()
        assert report["total_records"] == 0

    def test_get_validation_report_with_records(self):
        validator = TokenValidator()
        record = TokenTraceRecord(input_text="hi", total_tokens=2, generation_time=0.5)
        record.metadata["overall_valid"] = True
        validator.trace_records.append(record)
        report = validator.get_validation_report()
        assert report["total_records"] == 1
        assert report["valid_records"] == 1
        assert report["avg_generation_time"] == 0.5

    def test_get_validation_report_partial_valid(self):
        validator = TokenValidator()
        r1 = TokenTraceRecord(input_text="a", total_tokens=1, generation_time=0.1)
        r1.metadata["overall_valid"] = True
        r2 = TokenTraceRecord(input_text="b", total_tokens=1, generation_time=0.2)
        r2.metadata["overall_valid"] = False
        validator.trace_records.extend([r1, r2])
        report = validator.get_validation_report()
        assert report["validation_rate"] == 0.5

    def test_export_trace_data_success(self):
        validator = TokenValidator()
        record = TokenTraceRecord(
            input_text="hi",
            output_tokens=[
                TokenGenerationInfo(
                    token="hello", position=0, probability=0.9, source_model="test"
                )
            ],
            total_tokens=1,
            model_name="test-model",
        )
        record.metadata["overall_valid"] = True
        validator.trace_records.append(record)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            temp_path = f.name
        try:
            result = validator.export_trace_data(temp_path)
            assert result is True
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["total_tokens"] == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_trace_data_invalid_path(self):
        validator = TokenValidator()
        record = TokenTraceRecord(input_text="hi", total_tokens=0)
        validator.trace_records.append(record)
        result = validator.export_trace_data("/invalid/path/export.json")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_empty_tokens(self):
        validator = TokenValidator()
        record = await validator.validate_token_generation(
            input_text="", generated_tokens=[], token_probabilities=[]
        )
        assert record.total_tokens == 0

    @pytest.mark.asyncio
    async def test_validate_model_name_tracking(self):
        validator = TokenValidator()
        tokens = ["a", "b", "c"]
        probs = [0.7, 0.8, 0.9]
        record = await validator.validate_token_generation(
            input_text="x",
            generated_tokens=tokens,
            token_probabilities=probs,
            model_name="llama-3",
        )
        assert record.model_name == "llama-3"
        for t in record.output_tokens:
            assert t.source_model == "llama-3"

    @pytest.mark.asyncio
    async def test_semantic_coherence_empty(self):
        validator = TokenValidator()
        trace = TokenTraceRecord(input_text="")
        score = await validator._calculate_semantic_coherence(trace)
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_attention_patterns_no_maps(self):
        validator = TokenValidator()
        trace = TokenTraceRecord(input_text="test")
        score = await validator._validate_attention_patterns(trace)
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_attention_patterns_concentrated(self):
        validator = TokenValidator()
        info = AttentionInfo(
            layer=0, head=0, attention_weights={"a": 0.95, "b": 0.03, "c": 0.02}
        )
        trace = TokenTraceRecord(input_text="test", attention_maps=[info])
        score = await validator._validate_attention_patterns(trace)
        assert score < 1.0

    @pytest.mark.asyncio
    async def test_full_pipeline_valid(self):
        validator = TokenValidator()
        tokens = ["the", "quick", "brown", "fox"]
        probs = [0.9, 0.8, 0.85, 0.75]
        attention = [
            {"t0": 0.25, "t1": 0.25, "t2": 0.25, "t3": 0.25},
            {"t0": 0.3, "t1": 0.4, "t2": 0.2, "t3": 0.1},
            {"t0": 0.2, "t1": 0.2, "t2": 0.4, "t3": 0.2},
            {"t0": 0.1, "t1": 0.2, "t2": 0.3, "t3": 0.4},
        ]
        record = await validator.validate_token_generation(
            input_text="start",
            generated_tokens=tokens,
            token_probabilities=probs,
            attention_weights=attention,
            model_name="test-model",
        )
        assert record.total_tokens == 4
        assert "overall_valid" in record.metadata


@pytest.mark.asyncio
class TestTokenGenerationMonitor:
    async def test_start_stop(self):
        validator = TokenValidator()
        monitor = TokenGenerationMonitor(validator)
        assert monitor.is_monitoring is False
        await monitor.start_monitoring(interval=0.1)
        assert monitor.is_monitoring is True
        await asyncio.sleep(0.05)
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    async def test_double_start(self):
        validator = TokenValidator()
        monitor = TokenGenerationMonitor(validator)
        await monitor.start_monitoring(interval=0.5)
        await monitor.start_monitoring(interval=0.5)
        assert monitor.is_monitoring is True
        await monitor.stop_monitoring()

    async def test_stop_without_start(self):
        validator = TokenValidator()
        monitor = TokenGenerationMonitor(validator)
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    async def test_monitoring_generates_report(self):
        validator = TokenValidator()
        record = TokenTraceRecord(input_text="test", total_tokens=2, generation_time=0.1)
        record.metadata["overall_valid"] = True
        validator.trace_records.append(record)
        monitor = TokenGenerationMonitor(validator)
        await monitor.start_monitoring(interval=0.05)
        await asyncio.sleep(0.1)
        report = validator.get_validation_report()
        assert report["total_records"] >= 1
        await monitor.stop_monitoring()


@pytest.mark.asyncio
class TestValidateTokenGenerationReal:
    async def test_basic_usage(self):
        result = await validate_token_generation_real(
            input_text="Hello world", generated_text="Hi there", model_name="test"
        )
        assert result.input_text == "Hello world"
        assert result.total_tokens == 2

    async def test_empty_generation(self):
        result = await validate_token_generation_real(
            input_text="", generated_text="", model_name="test"
        )
        assert result.total_tokens == 0

    async def test_model_name_tracking(self):
        result = await validate_token_generation_real(
            input_text="ping", generated_text="pong", model_name="gpt-4"
        )
        assert result.model_name == "gpt-4"
