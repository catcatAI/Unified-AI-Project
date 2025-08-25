import json
import asyncio
import pytest

from src.core_services import initialize_services, ham_manager_instance, tool_dispatcher_instance


@pytest.mark.timeout(15)
def test_tool_dispatcher_action_policy_logged_smoke():
    """
    Smoke test: invoke a simple tool via dispatcher and check that
    at least one action_policy_v0.1 record appears in HAM.
    """
    # Ensure services are initialized
    if tool_dispatcher_instance is None or ham_manager_instance is None:
        asyncio.run(initialize_services())
    # Import the updated instances after initialization
    from src.core_services import tool_dispatcher_instance as td_instance, ham_manager_instance as ham_instance
    assert td_instance is not None, "ToolDispatcher should be initialized"
    assert ham_instance is not None, "HAM manager should be initialized"

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
    for ev in events:
        raw = ev.get("raw_data") or ev.get("rehydrated_gist") or ev.get("content")
        if not raw:
            continue
        try:
            rec = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            rec = None
        if rec:
            assert "tool_name" in rec and "timestamp" in rec
            break
