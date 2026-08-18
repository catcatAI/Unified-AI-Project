"""Regression tests for DocumentRouter intent routing.

Previously ``google_drive`` intents were routed into the document processor,
so a message like "列出雲端硬碟的檔案" was hijacked into a local-filesystem
"list" task and answered with "請指定要處理的目錄路徑" — a misleading
response for a Drive request. Drive has its own dedicated API endpoints, so
google_drive must NOT be intercepted here.
"""

import pytest

from services.document_router import try_intent_routing


class _FakeChatService:
    """Minimal stand-in: document routing never needs real generation in these tests."""

    async def generate_text(self, *args, **kwargs):
        return "generated"


@pytest.mark.asyncio
async def test_google_drive_intent_not_hijacked():
    """google_drive intents must fall through (return None), not be processed as docs."""
    for msg in ("列出雲端硬碟的檔案", "谷歌硬碟", "打開雲端"):
        result = await try_intent_routing(msg, _FakeChatService())
        assert result is None, f"drive intent '{msg}' must not be routed to document processing"


@pytest.mark.asyncio
async def test_document_intent_still_routes():
    """Document intents must still be processed by the tiered pipeline."""
    result = await try_intent_routing("整理 data/docs/ 裡的文件", _FakeChatService())
    assert result is not None
    assert result.get("route") == "document_router"
