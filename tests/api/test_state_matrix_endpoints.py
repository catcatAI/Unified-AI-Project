"""
ANGELA-MATRIX: [L4] [β] [B] [L3]
The state-matrix HTTP endpoints must act on real objects.

Five endpoints answered ``{"status": "not_implemented"}`` (or an empty
port list) because the underlying capability was never attached:
the port registry did not exist on the matrix, the ripple engine was not
called, and the allocation decision had no implementation. A client that
calls them got a 200 with a "not implemented" body — a lie in the shape of
a success.

These tests pin the corrected behaviour.
"""

import pytest

from services.api.state_matrix_api import (
    AllocationRequest,
    RippleRequest,
    allocation_decide,
    apply_ripple,
    list_ports,
    register_port,
    unregister_port,
)


@pytest.fixture(autouse=True)
def _clean_ports():
    """Keep the shared matrix's port registry clean between tests."""
    from services.api.state_matrix_api import get_state_matrix

    matrix = get_state_matrix()
    registry = getattr(matrix, "ports", None)
    yield
    if registry is not None:
        for port in list(registry.list_ports()):
            registry.unregister_port(port.get("axis") or port.get("name"))


@pytest.mark.asyncio
class TestStateMatrixPortEndpoints:
    async def test_register_list_unregister_roundtrip(self):
        result = await register_port({"axis": "alpha", "config": {"direction": "IO"}})
        assert result["status"] == "registered"
        assert result["axis"] == "alpha"
        assert result["port"]["direction"] == "IO"

        listing = await list_ports()
        assert any(p["axis"] == "alpha" for p in listing["ports"])

        removed = await unregister_port("alpha")
        assert removed["status"] == "unregistered"

        listing = await list_ports()
        assert not any(p["axis"] == "alpha" for p in listing["ports"])

    async def test_unregistering_an_unknown_axis_is_reported(self):
        result = await unregister_port("no_such_axis")
        assert result["status"] == "not_found"

    async def test_register_without_an_axis_is_rejected(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as excinfo:
            await register_port({"config": {}})
        assert excinfo.value.status_code == 400


@pytest.mark.asyncio
class TestStateMatrixRippleAndAllocation:
    async def test_ripple_is_applied_to_the_matrix(self):
        from services.api.state_matrix_api import get_state_matrix

        matrix = get_state_matrix()
        before = matrix.beta.values.get("focus", 0.5)
        result = await apply_ripple(
            RippleRequest(
                source_axis="alpha",
                source_value=0.9,
                target_axes=["beta"],
                strength=0.5,
            )
        )
        assert result["status"] == "applied"
        # The ripple must actually reach the target axis.
        assert matrix.beta.values.get("focus", 0.5) != before

    async def test_allocation_returns_a_decision(self):
        result = await allocation_decide(
            AllocationRequest(candidates=[{"alpha": 0.7}], dimension="alpha")
        )
        assert "action" in result["decision"]
        assert result["decision"]["action"]

    async def test_allocation_without_candidates_is_rejected(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as excinfo:
            await allocation_decide(AllocationRequest(candidates=[], dimension="alpha"))
        assert excinfo.value.status_code == 400
