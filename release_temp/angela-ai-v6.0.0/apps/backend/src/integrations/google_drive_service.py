import os
import logging
from typing import Optional, List, Dict, Any
import ray

from apps.backend.src.integrations.google_drive_service_actor import GoogleDriveServiceActor # Import the Actor

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """
    Client for the GoogleDriveServiceActor.
    Delegates calls to the remote GoogleDriveServiceActor instance.
    """
    
    def __init__(self, credentials_path: str = "apps/backend/config/credentials.json", token_path: str = "apps/backend/data/google_tokens.json"):
        # Initialize Ray if not already done (for safety)
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        self.actor = GoogleDriveServiceActor.remote(credentials_path, token_path) # Create the remote actor
        logger.info("GoogleDriveService client initialized, GoogleDriveServiceActor created.")
        
    def authenticate(self) -> bool:
        return ray.get(self.actor.authenticate.remote())
    
    def is_authenticated(self) -> bool:
        return ray.get(self.actor.is_authenticated.remote())
    
    async def list_files(self, folder_id: Optional[str] = None, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
        return await self.actor.list_files.remote(folder_id, page_size, page_token)
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        return await self.actor.get_file_metadata.remote(file_id)
    
    async def download_file(self, file_id: str, output_path: str) -> bool:
        return await self.actor.download_file.remote(file_id, output_path)
