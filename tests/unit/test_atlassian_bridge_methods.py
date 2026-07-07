"""Tests for AtlassianBridge method implementations"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


def _try_import():
    try:
        from integrations.atlassian_bridge import AtlassianBridge
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

        connector = EnhancedRovoDevConnector(config={
            "atlassian": {
                "confluence": {"url": "https://test.atlassian.net/wiki"},
                "jira": {"url": "https://test.atlassian.net"},
                "bitbucket": {"url": "https://api.bitbucket.org"},
            }
        })
        return AtlassianBridge(connector=connector)
    except Exception as e:
        pytest.skip(f"AtlassianBridge not available: {e}")


async def _make_bridge():
    bridge = _try_import()
    session = MagicMock()
    resp_mock = MagicMock()
    resp_mock.json = AsyncMock(return_value={})
    resp_mock.status = 200
    session.request.return_value.__aenter__.return_value = resp_mock
    bridge._session = session
    return bridge


def _set_response(bridge, data, status=200):
    bridge._session.request.return_value.__aenter__.return_value.json = AsyncMock(
        return_value=data
    )
    bridge._session.request.return_value.__aenter__.return_value.status = status


# (method_name, args, kwargs, mock_data, status, assertions_fn)
_SUCCESS_CASES = [
    ("get_confluence_page", ("123",), {}, {"id": "123", "title": "Test"}, 200,
     lambda r: (r.get("success") and r["data"]["id"] == "123")),
    ("update_confluence_page", ("123", "Updated Title", "New content"), {}, {"id": "123", "version": {"number": 2}}, 200,
     lambda r: r.get("success")),
    ("create_jira_issue", ("TEST", "Test issue", "Description"), {}, {"id": "10001", "key": "TEST-1"}, 201,
     lambda r: (r.get("success") and r["data"]["key"] == "TEST-1")),
    ("get_jira_issue", ("TEST-1",), {}, {"key": "TEST-1", "fields": {"summary": "Test"}}, 200,
     lambda r: (r.get("success") and r["data"]["key"] == "TEST-1")),
    ("update_jira_issue", ("TEST-1", {"summary": "Updated"}), {}, {"key": "TEST-1"}, 200,
     lambda r: r.get("success")),
    ("transition_jira_issue", ("TEST-1", "31"), {}, {}, 200,
     lambda r: r.get("success")),
]

_LIST_CASES = [
    ("search_confluence_pages", ("DEV", "text ~ test"), {},
     {"results": [{"id": "1", "title": "Page 1"}]}, "results", "id", "1"),
    ("search_jira_issues", ("project = TEST",), {},
     {"issues": [{"key": "TEST-1", "fields": {"summary": "Test"}}]}, "issues", "key", "TEST-1"),
    ("get_bitbucket_repositories", ("myworkspace",), {},
     {"values": [{"slug": "repo1", "name": "Repo 1"}]}, "values", "slug", "repo1"),
    ("get_bitbucket_pull_requests", ("myworkspace", "repo1"), {},
     {"values": [{"id": 1, "title": "PR 1"}]}, "values", "id", 1),
    ("get_confluence_spaces", (), {},
     {"results": [{"key": "DEV", "name": "Development"}]}, "results", "key", "DEV"),
    ("get_jira_projects", (), {},
     {"values": [{"key": "TEST", "name": "Test Project"}]}, "values", "key", "TEST"),
]

_EMPTY_CASES = [
    ("search_confluence_pages", ("DEV", "text ~ nothing"), {}),
    ("search_jira_issues", ("project = NONE",), {}),
    ("get_bitbucket_repositories", ("empty",), {}),
    ("get_confluence_spaces", (), {}),
    ("get_jira_projects", (), {}),
]


class TestAtlassianBridgeMethods:
    """Verify each bridge method via mocked HTTP session"""

    @pytest.mark.parametrize("method,args,kwargs,mock_data,status,check_fn", _SUCCESS_CASES)
    async def test_success_methods(self, method, args, kwargs, mock_data, status, check_fn):
        bridge = await _make_bridge()
        _set_response(bridge, mock_data, status)
        result = await getattr(bridge, method)(*args, **kwargs)
        assert check_fn(result)

    @pytest.mark.parametrize("method,args,kwargs,mock_data,result_key,field,expected", _LIST_CASES)
    async def test_list_methods(self, method, args, kwargs, mock_data, result_key, field, expected):
        bridge = await _make_bridge()
        _set_response(bridge, mock_data)
        results = await getattr(bridge, method)(*args, **kwargs)
        assert len(results) == 1
        assert results[0][field] == expected

    @pytest.mark.parametrize("method,args,kwargs", _EMPTY_CASES)
    async def test_empty_results(self, method, args, kwargs):
        bridge = await _make_bridge()
        _set_response(bridge, {})
        results = await getattr(bridge, method)(*args, **kwargs)
        assert results == []

    async def test_get_jira_projects_list_response(self):
        bridge = await _make_bridge()
        _set_response(bridge, [{"key": "TEST", "name": "Test Project"}])
        results = await bridge.get_jira_projects()
        assert len(results) == 1
        assert results[0]["key"] == "TEST"
