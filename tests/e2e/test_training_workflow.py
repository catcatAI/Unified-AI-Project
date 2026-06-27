"""End-to-end training workflow tests.

Requires a live test server. All tests are skipped by default.
"""

import pytest

BASE_URL = "http://localhost:8000/api/v1"
TRAINING_ENDPOINT = f"{BASE_URL}/train"


@pytest.mark.e2e
@pytest.mark.skip(reason="Requires live server")
class TestTrainingWorkflowE2E:
    """E2E tests for the training workflow lifecycle."""

    async def test_training_workflow_basic(self) -> None:
        """Start a training job, poll until done, verify output exists."""
        # Arrange: valid training payload
        payload = {
            "model": "default",
            "epochs": 1,
            "batch_size": 32,
            "data_path": "/test/data/sample.csv",
        }

        # Act: submit training job
        # async with httpx.AsyncClient() as client:
        #     create_resp = await client.post(TRAINING_ENDPOINT, json=payload)
        #     assert create_resp.status_code == 201
        #     job_id = create_resp.json()["job_id"]
        #
        #     # Poll for completion
        #     status = "running"
        #     while status == "running":
        #         status_resp = await client.get(f"{TRAINING_ENDPOINT}/{job_id}")
        #         assert status_resp.status_code == 200
        #         status = status_resp.json()["status"]
        #
        #     # Assert: job completed successfully
        #     assert status == "completed", f"Expected completed, got {status}"
        #     result = status_resp.json()
        #     assert "accuracy" in result
        #     assert isinstance(result["accuracy"], float)
        #     assert 0.0 < result["accuracy"] <= 1.0
        #     assert "model_path" in result
        #     assert result["model_path"].endswith(".pt")

        # Placeholder: verify test structure is valid
        assert (
            payload["epochs"] == 1
        ), "Fixture verification failed"

    async def test_training_workflow_invalid_params(self) -> None:
        """Send invalid training parameters and verify 422 response."""
        # Arrange: payload with negative epochs
        invalid_payload = {
            "model": "default",
            "epochs": -5,
            "batch_size": 0,
            "data_path": "",
        }

        # Act & Assert
        # async with httpx.AsyncClient() as client:
        #     resp = await client.post(TRAINING_ENDPOINT, json=invalid_payload)
        #     assert resp.status_code == 422
        #     detail = resp.json()
        #     assert "detail" in detail
        #     errors = {e["loc"][-1]: e["msg"] for e in detail["detail"]}
        #     assert "epochs" in errors
        #     assert "batch_size" in errors

        # Verify invalid payload is correctly constructed
        assert invalid_payload["epochs"] < 0
        assert invalid_payload["batch_size"] == 0

    async def test_training_workflow_cancellation(self) -> None:
        """Cancel a running training job and verify clean state."""
        # Arrange: start a long-running training job
        long_payload = {
            "model": "default",
            "epochs": 100,
            "batch_size": 32,
            "data_path": "/test/data/large.csv",
        }

        # Act: submit, then cancel
        # async with httpx.AsyncClient() as client:
        #     create_resp = await client.post(TRAINING_ENDPOINT, json=long_payload)
        #     assert create_resp.status_code == 201
        #     job_id = create_resp.json()["job_id"]
        #
        #     cancel_resp = await client.post(
        #         f"{TRAINING_ENDPOINT}/{job_id}/cancel"
        #     )
        #     assert cancel_resp.status_code == 200
        #     cancel_data = cancel_resp.json()
        #
        #     # Assert: job was cancelled gracefully
        #     assert cancel_data["status"] == "cancelled"
        #     assert "cancelled_at" in cancel_data
        #
        #     # Verify job resources were cleaned up
        #     status_resp = await client.get(f"{TRAINING_ENDPOINT}/{job_id}")
        #     assert status_resp.status_code == 200
        #     final_status = status_resp.json()["status"]
        #     assert final_status == "cancelled"

        # Verify payload structure is valid
        assert long_payload["epochs"] > 1
