import os
import logging
from typing import Optional, List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import ray

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

@ray.remote
class GoogleDriveServiceActor:
    """Handles Google Drive OAuth authentication and file operations, as a Ray Actor."""
    
    def __init__(self, credentials_path: str = "apps/backend/config/credentials.json", token_path: str = "apps/backend/data/google_tokens.json"):
        # Convert to absolute paths
        self.credentials_path = os.path.abspath(credentials_path)
        self.token_path = os.path.abspath(token_path)
        self.creds: Optional[Credentials] = None
        self.service = None
        
        # Ensure token directory exists
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        
        logger.info(f"GoogleDriveServiceActor initialized:")
        logger.info(f"  Credentials: {self.credentials_path}")
        logger.info(f"  Token: {self.token_path}")
        
    def authenticate(self) -> bool:
        """
        Authenticates with Google Drive using OAuth 2.0.
        Returns True if authentication successful.
        """
        logger.debug("Attempting Google Drive authentication...")
        try:
            # Load existing token if available
            if os.path.exists(self.token_path):
                logger.debug(f"Loading token from {self.token_path}")
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
            # Refresh or get new token
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired token...")
                    self.creds.refresh(Request())
                else:
                    logger.info("Starting OAuth flow...")
                    # Ensure credentials.json exists
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"Credentials file not found at: {self.credentials_path}")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save token for future use
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info(f"Token saved to {self.token_path}")
            
            # Build service
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("Google Drive service authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True) # Log full traceback
            return False
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        logger.debug("Checking Google Drive authentication status...")
        try:
            # Check if service object exists and if credentials are valid (optional, but robust)
            if self.service is not None and self.creds is not None and self.creds.valid:
                logger.debug("Google Drive is authenticated and credentials are valid.")
                return True
            logger.debug("Google Drive is not authenticated or credentials are not valid.")
            return False
        except Exception as e:
            logger.error(f"Error checking authentication status: {e}", exc_info=True)
            return False
    
    def list_files(self, folder_id: Optional[str] = None, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Lists files from Google Drive.
        
        Args:
            folder_id: Optional folder ID to list files from
            page_size: Number of files per page
            page_token: Token for pagination
            
        Returns:
            Dict with 'files' list and 'nextPageToken' if more pages exist
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            query = "trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=page_size,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            next_page_token = results.get('nextPageToken')
            
            logger.info(f"Listed {len(files)} files from Drive")
            return {
                "files": files,
                "nextPageToken": next_page_token
            }
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise
    
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get metadata for a specific file."""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, webViewLink, md5Checksum"
            ).execute()
            
            return file_metadata
            
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise
    
    def download_file(self, file_id: str, output_path: str) -> bool:
        """
        Downloads a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            output_path: Local path to save the file
            
        Returns:
            True if download successful
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Get file metadata first
            file_metadata = self.get_file_metadata(file_id)
            mime_type = file_metadata.get('mimeType', '')
            
            # Handle Google Docs export
            if mime_type.startswith('application/vnd.google-apps'):
                return self._export_google_doc(file_id, mime_type, output_path)
            
            # Regular file download
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Downloaded file to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def _export_google_doc(self, file_id: str, mime_type: str, output_path: str) -> bool:
        """Export Google Docs/Sheets/Slides to downloadable format."""
        try:
            # Map Google MIME types to export formats
            export_formats = {
                'application/vnd.google-apps.document': 'text/plain',  # Google Docs -> Plain text
                'application/vnd.google-apps.spreadsheet': 'text/csv',  # Google Sheets -> CSV
                'application/vnd.google-apps.presentation': 'text/plain'  # Google Slides -> Plain text
            }
            
            export_mime = export_formats.get(mime_type, 'text/plain')
            
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType=export_mime
            )
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Exported Google Doc to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Google Doc: {e}")
            return False
