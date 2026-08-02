"""mcp.fallback.mcp_fallback_protocols MCP 備選協議測試"""

import asyncio

import pytest

from apps.backend.src.mcp.connector import (
    get_mcp_fallback_manager,
    initialize_mcp_fallback_protocols,
)
from apps.backend.src.mcp.fallback.mcp_fallback_protocols import (
    FallbackProtocol,
    FallbackProtocolType,
    initialize_fallback_protocols,
)


class TestFallbackProtocolType:
    def test_enum_members(self):
        assert FallbackProtocolType.IN_PROCESS.value == "in_process"
        assert FallbackProtocolType.SHARED_MEMORY.value == "shared_memory"
        assert FallbackProtocolType.FILE_BASED.value == "file_based"
        assert FallbackProtocolType.LOOPBACK.value == "loopback"


class TestFallbackProtocol:
    @pytest.mark.asyncio
    async def test_send_and_process(self):
        proto = FallbackProtocol(FallbackProtocolType.IN_PROCESS)
        received = []

        async def handler(payload):
            received.append(payload)

        proto.register_handler("cmd", handler)
        await proto.send_message("target", "cmd", {"x": 1})
        count = await proto.process_messages()
        assert count == 1
        assert received == [{"x": 1}]

    @pytest.mark.asyncio
    async def test_unregistered_command_skipped(self):
        proto = FallbackProtocol(FallbackProtocolType.IN_PROCESS)
        await proto.send_message("target", "unknown_cmd", {"x": 1})
        count = await proto.process_messages()
        assert count == 0


class TestInitializeFallbackProtocols:
    @pytest.mark.asyncio
    async def test_returns_protocol_map(self):
        protocols = await initialize_fallback_protocols(is_multiprocess=False)
        assert FallbackProtocolType.IN_PROCESS.value in protocols
        assert isinstance(protocols[FallbackProtocolType.IN_PROCESS.value], FallbackProtocol)

    @pytest.mark.asyncio
    async def test_multiprocess_adds_shared_memory(self):
        protocols = await initialize_fallback_protocols(is_multiprocess=True)
        assert FallbackProtocolType.SHARED_MEMORY.value in protocols


class TestConnectorWiring:
    @pytest.mark.asyncio
    async def test_initialize_mcp_fallback_protocols_wires_protocols(self):
        ok = await initialize_mcp_fallback_protocols(is_multiprocess=False)
        assert ok is True
        mgr = get_mcp_fallback_manager()
        assert len(mgr._fallback_protocols) == 1
        assert FallbackProtocolType.IN_PROCESS.value in mgr._fallback_protocols

    @pytest.mark.asyncio
    async def test_send_command_routes_to_protocol(self):
        await initialize_mcp_fallback_protocols(is_multiprocess=False)
        mgr = get_mcp_fallback_manager()
        received = []

        async def handler(payload):
            received.append(payload)

        mgr.register_command_handler("cmd", handler)
        await mgr.send_command("s1", "r1", "cmd", {"hello": "world"}, 1)
        for proto in mgr._fallback_protocols.values():
            await proto.process_messages()
        assert received == [{"hello": "world"}]
