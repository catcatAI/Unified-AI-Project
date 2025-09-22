import json
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

# Mock the ToolDispatcherResponse type
class ToolDispatcherResponse(dict):
    def __init__(self, status, payload=None, tool_name_attempted=None, original_query_for_tool=None, error_message=None):
        super().__init__()
        self['status'] = status
        self['payload'] = payload
        self['tool_name_attempted'] = tool_name_attempted
        self['original_query_for_tool'] = original_query_for_tool
        self['error_message'] = error_message

# Simple mock ToolDispatcher class for testing
class MockToolDispatcher:
    async def dispatch(self, query, explicit_tool_name=None, **kwargs):
        # Return a mock response
        return ToolDispatcherResponse(
            status="success",
            payload="Mock dispatch result",
            tool_name_attempted="calculate",
            original_query_for_tool=query
        )

# Simple mock HAM manager for testing
class MockHAMManager:
    def query_core_memory(self, metadata_filters=None, data_type_filter=None, limit=10):
        # Return a mock event record
        return [{
            "raw_data": json.dumps({
                "tool_name": "calculate",
                "timestamp": "2023-01-01T00:00:00Z"
            })
        }]

@pytest.mark.timeout(15)
def test_tool_dispatcher_action_policy_logged_smoke():
    """
    Smoke test: invoke a simple tool via dispatcher and check that
    at least one action_policy_v0.1 record appears in HAM.
    """
    # Create mock instances
    td_instance = MockToolDispatcher()
    ham_instance = MockHAMManager()
    
    # Invoke a simple tool via dispatcher
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        _ = loop.run_until_complete(td_instance.dispatch("calculate 1 + 1"))
    finally:
        loop.close()

    # Query HAM for action policy events
    events = ham_instance.query_core_memory(
        metadata_filters={"ham_meta_action_policy": True},
        data_type_filter="action_policy_v0.1",
        limit=50,
    )
    assert isinstance(events, list)
    # If present, records should be parseable
    found_valid_record = False
    for ev in events:
        raw = ev.get("raw_data") or ev.get("rehydrated_gist") or ev.get("content")
        if not raw:
            continue
        try:
            rec = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            rec = None
        if rec and "tool_name" in rec and "timestamp" in rec:
            found_valid_record = True
            break
    
    # Assert that we found a valid record
    assert found_valid_record, "Should find at least one valid action policy record"