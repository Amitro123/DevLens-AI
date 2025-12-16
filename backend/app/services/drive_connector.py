"""
Google Drive integration service for DocuFlow AI
"""

import re
import io
import logging
from typing import Optional
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class DriveError(Exception):
    """Custom exception for Drive operations"""
    pass


class DriveConnector:
    """Service to interact with Google Drive API"""

    def __init__(self):
        pass

    def extract_file_id(self, url: str) -> Optional[str]:
        """
        Extract file ID from various Google Drive URL formats.
        
        Args:
            url: The Google Drive URL
            
        Returns:
            Extracted file ID or None if not found
        """
        # Patterns for different Drive URL formats
        patterns = [
            r"drive\.google\.com\/file\/d\/([-_\w]+)",  # Standard /file/d/ID
            r"drive\.google\.com\/open\?id=([-_\w]+)",  # Legacy open?id=ID
            r"docs\.google\.com\/presentation\/d\/([-_\w]+)", # Slides
            r"docs\.google\.com\/document\/d\/([-_\w]+)", # Docs
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def download_file(self, file_id: str, destination: Path, access_token: Optional[str] = None) -> Path:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: The ID of the file to download
            destination: Path where the file should be saved
            access_token: Optional OAuth2 access token for private files
            
        Returns:
            Path to the downloaded file
            
        Raises:
            DriveError: If download fails
        """
        try:
            # Build service
            if access_token:
                creds = Credentials(token=access_token)
                service = build('drive', 'v3', credentials=creds)
            else:
                # Public access (API key would be better here for reliability, but trying no-auth first)
                # Note: 'drive' API usually requires auth. For public files, we might need an API key.
                # However, for this implementation request, we follow the "if access_token is provided... else try public"
                # A fully unauthenticated discovery.build might fail without developerKey.
                # We'll use a placeholder or assume the user provides a token for now effectively, 
                # or rely on the environment having ADC if configured.
                # As a fallback for public URLs without tokens, standard requests.get on the 'export=download' link is often easier 
                # than the API client which enforces auth.
                # But to stick to the requirement of using googleapiclient:
                service = build('drive', 'v3') 

            request = service.files().get_media(fileId=file_id)
            
            # Streaming download
            fh = io.FileIO(destination, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}%.")
            
            logger.info(f"Downloaded Drive file {file_id} to {destination}")
            return destination
            
        except Exception as e:
            # Clean up partial download
            if destination.exists():
                destination.unlink()
            raise DriveError(f"Failed to download file {file_id}: {str(e)}")
