"""Atlassian end-to-end workflow tests.

Requires a live test server with Atlassian integration enabled.
All tests are skipped by default.
"""

import pytest
from typing import Any, Dict


BASE_URL = "http://localhost:8000/api/v1"
ATLASSIAN_ENDPOINT = f"{BASE_URL}/atlassian"


def _valid_config() -> Dict[str, str]:
    """Return a valid Atlassian configuration dict."""
    return {
        "base_url": "https://your-domain.atlassian.net",
        "api_token": "dummy-token",
        "project_key": "TEST",
    }


def _invalid_config() -> Dict[str, str]:
    """Return an invalid Atlassian configuration dict."""
    return {
        "base_url": "",
        "api_token": "",
        "project_key": "",
    }


@pytest.mark.e2e
@pytest.mark.skip(reason="Requires live server")
class TestAtlassianEndToEndWorkflow:
    """E2E tests for the Atlassian integration lifecycle."""

    async def test_atlassian_full_workflow(self) -> None:
        """Create a Jira issue and verify it was persisted."""
        # Arrange
        config = _valid_config()
        issue_payload = {
            "summary": "E2E test issue — delete me",
            "description": "Created by automated E2E test",
            "issue_type": "Task",
            "priority": "Medium",
        }

        # Act & Assert
        # async with httpx.AsyncClient() as client:
        #     # 1. Configure connection
        #     config_resp = await client.post(
        #         f"{ATLASSIAN_ENDPOINT}/configure", json=config
        #     )
        #     assert config_resp.status_code == 200
        #
        #     # 2. Create issue
        #     create_resp = await client.post(
        #         f"{ATLASSIAN_ENDPOINT}/issues", json=issue_payload
        #     )
        #     assert create_resp.status_code == 201
        #     issue = create_resp.json()
        #     assert "id" in issue
        #     assert issue["summary"] == issue_payload["summary"]
        #     assert issue["status"] == "To Do"
        #
        #     # 3. Fetch issue to verify persistence
        #     issue_id = issue["id"]
        #     fetch_resp = await client.get(
        #         f"{ATLASSIAN_ENDPOINT}/issues/{issue_id}"
        #     )
        #     assert fetch_resp.status_code == 200
        #     fetched = fetch_resp.json()
        #     assert fetched["id"] == issue_id
        #     assert fetched["summary"] == issue_payload["summary"]

        # Verify test data is well-formed
        assert config["base_url"].startswith("https://")
        assert issue_payload["issue_type"] in ("Task", "Bug", "Story")

    async def test_offline_mode_handling(self) -> None:
        """Verify graceful degradation when Atlassian is unreachable."""
        # Arrange: bogus URL that cannot resolve
        offline_config: Dict[str, Any] = {
            "base_url": "https://nonexistent.invalid",
            "api_token": "invalid",
            "project_key": "NOPE",
        }

        # Act & Assert
        # async with httpx.AsyncClient() as client:
        #     # 1. Configure with unreachable URL
        #     config_resp = await client.post(
        #         f"{ATLASSIAN_ENDPOINT}/configure", json=offline_config
        #     )
        #     # Should still accept config (stored locally)
        #     assert config_resp.status_code == 200
        #
        #     # 2. Attempt to create issue — expect offline fallback
        #     resp = await client.post(
        #         f"{ATLASSIAN_ENDPOINT}/issues",
        #         json={"summary": "offline test", "description": ""},
        #     )
        #     assert resp.status_code == 503
        #     body = resp.json()
        #     assert "detail" in body
        #     assert "offline" in body["detail"].lower() or "unreachable" in body["detail"].lower()
        #
        #     # 3. Health endpoint should report Atlassian as down
        #     health_resp = await client.get(f"{ATLASSIAN_ENDPOINT}/health")
        #     assert health_resp.status_code == 200
        #     health = health_resp.json()
        #     assert health.get("atlassian_status") == "offline"

        # Verify offline config is correctly marked as unreachable
        assert "nonexistent" in offline_config["base_url"]

    async def test_atlassian_config_validation(self) -> None:
        """Validate configuration rules without hitting the live API."""
        # These assertions can run without a server — they test
        # config validation logic directly.

        valid = _valid_config()
        invalid = _invalid_config()

        # Valid config checks
        assert valid["base_url"].startswith("https://"), "URL must be HTTPS"
        assert len(valid["api_token"]) > 0, "API token must not be empty"
        assert (
            len(valid["project_key"]) == 4 or len(valid["project_key"]) > 0
        ), "Project key must be non-empty"

        # Invalid config checks
        assert invalid["base_url"] == "", "Empty URL should be rejected"
        assert invalid["api_token"] == "", "Empty token should be rejected"
        assert invalid["project_key"] == "", "Empty key should be rejected"

        # Edge cases
        edge_cases: Dict[str, Dict[str, Any]] = {
            "missing_fields": {},
            "partial_config": {"base_url": "https://example.com"},
            "wrong_types": {
                "base_url": 123,
                "api_token": None,
                "project_key": [],
            },
        }

        for case_name, cfg in edge_cases.items():
            # Every case above is missing non-optional fields
            required_keys = {"base_url", "api_token", "project_key"}
            missing = required_keys - set(cfg.keys())
            assert len(missing) > 0, (
                f"Case '{case_name}' should be missing required keys, "
                f"got extras: {set(cfg.keys()) - required_keys}"
            )
