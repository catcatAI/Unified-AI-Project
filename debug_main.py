import logging
import sys
import os
import asyncio
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add project root to sys.path to allow imports from 'apps'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logger (basic setup for debugging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Mock/Dummy Global Instances for minimal test ---
# These are just to allow the import of local_files and its dependencies
# without needing a full SystemManager setup.
# In a real scenario, these would come from the SystemManager.
ham_memory_manager = None

# Placeholder for real HAMMemoryManager if needed for the endpoint
class MockHAMMemoryManager:
    async def store_experience(self, experience: dict):
        logger.info(f"MockHAMMemoryManager: Storing experience: {experience.get('metadata', {}).get('file_name')}")
        return "mock_memory_id"

    async def retrieve_relevant_memories(self, query: str, limit: int = 5):
        logger.info(f"MockHAMMemoryManager: Retrieving memories for query: {query}")
        return [{"content": "Mocked memory content for: " + query, "metadata": {"source": "mock"}}]

ham_memory_manager = MockHAMMemoryManager()


# Import local_files router
try:
    from apps.backend.src.api.v1.endpoints import local_files as v1_local_files_router
    logger.info("Successfully imported v1_local_files_router.")
except Exception as e:
    logger.error(f"Failed to import v1_local_files_router: {e}")
    v1_local_files_router = None


# Initialize FastAPI app
app = FastAPI(
    title="Minimal Router Debug App",
    description="App to debug local_files router registration.",
    version="0.1.0",
)

# Include the local_files router if successfully imported
if v1_local_files_router:
    app.include_router(v1_local_files_router.router, prefix="/api/v1")
    logger.info("Successfully included v1_local_files_router.")
else:
    logger.warning("v1_local_files_router was not imported, not including router.")

@app.get("/")
async def read_root():
    """Root endpoint to confirm the server is running."""
    return {"message": "Minimal Router Debug App is running"}

@app.get("/test-route")
async def test_route():
    """Test route to ensure basic routing works."""
    return {"message": "Test route works!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
