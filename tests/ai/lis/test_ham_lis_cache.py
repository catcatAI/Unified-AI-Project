import pytest
from unittest.mock import AsyncMock, MagicMock
try:
    from ai.lis.lis_cache_interface import HAMLISCache
    from ai.lis.types import LIS_IncidentRecord, NarrativeAntibodyObject, LIS_AnomalyType
except ImportError:
    pytest.skip("Required modules not available (stub modules)", allow_module_level=True)


@pytest.fixture
def ham_manager_mock():
    hm = MagicMock()
    hm.store_experience = AsyncMock(return_value="mem_id_123")
    hm.query_core_memory = AsyncMock(return_value=[])
    return hm


@pytest.fixture
def cache(ham_manager_mock):
    return HAMLISCache(ham_manager_mock)
async def test_store_incident_success(cache):
    incident = LIS_IncidentRecord(
        incident_id="test_001",
        status="OPEN",
        anomaly_event={
            "anomaly_id": "anom_001",
            "anomaly_type": "REPETITION_ECHO",
            "severity_score": 0.9,
            "description": "Test repetition",
            "context_snippet": "hello world",
            "timestamp_detected": "2025-01-01T00:00:00Z",
            "metadata": {},
        },
        intervention_reports=[],
        tags=["test"],
        timestamp_logged="2025-01-01T00:00:00Z",
    )
    result = await cache.store_incident(incident)
    assert result is True
async def test_query_incidents_empty(cache):
    results = await cache.query_incidents()
    assert results == []
async def test_query_incidents_by_type_empty(cache):
    results = await cache.query_incidents(anomaly_type="REPETITION_ECHO", limit=5)
    assert results == []
async def test_store_antibody_success(cache):
    antibody = NarrativeAntibodyObject(
        antibody_id="ab_001",
        target_anomaly_types=["REPETITION_ECHO"],
        trigger_conditions={},
        response_pattern={},
        effectiveness_score=0.8,
        usage_count=0,
        timestamp_created="2025-01-01T00:00:00Z",
        version="1.0",
    )
    result = await cache.store_antibody(antibody)
    assert result is True
async def test_get_learned_antibodies_empty(cache):
    results = await cache.get_learned_antibodies(for_anomaly_type="REPETITION_ECHO", limit=5)
    assert results == []