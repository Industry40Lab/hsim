"""
Azure Blob Storage utility module for handling file operations.

This module provides a unified interface for storing and retrieving files
from Azure Blob Storage, replacing local filesystem operations.
"""

import logging
import io
import os
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, AzureError

logger = logging.getLogger(__name__)


class AzureBlobStorage:
    """
    Azure Blob Storage manager for Flask application file operations.

    Container structure:
    - temp-files: Temporary simulation files (auto-cleanup)
    - user-results: Persistent user results (organized by username)
    - global-results: Leaderboard CSV and shared data
    """

    # Container names
    TEMP_CONTAINER = "temp-files"
    USER_RESULTS_CONTAINER = "user-results"
    GLOBAL_RESULTS_CONTAINER = "global-results"

    def __init__(self, connection_string: str):
        """
        Initialize Azure Blob Storage client.

        Args:
            connection_string: Azure Storage connection string
        """
        if not connection_string:
            raise ValueError("Azure Storage connection string is required")

        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self._ensure_containers_exist()
            logger.info("Azure Blob Storage client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage: {e}")
            raise

    def _ensure_containers_exist(self):
        """Create containers if they don't exist."""
        containers = [
            self.TEMP_CONTAINER,
            self.USER_RESULTS_CONTAINER,
            self.GLOBAL_RESULTS_CONTAINER
        ]

        for container_name in containers:
            try:
                container_client = self.blob_service_client.get_container_client(container_name)
                if not container_client.exists():
                    container_client.create_container()
                    logger.info(f"Created container: {container_name}")
            except Exception as e:
                logger.warning(f"Container {container_name} setup issue: {e}")

    def _get_blob_path(self, container: str, filename: str, username: Optional[str] = None) -> str:
        """
        Generate blob path with optional username subdirectory.

        Args:
            container: Container name
            filename: File name
            username: Optional username for organizing files

        Returns:
            Blob path string
        """
        if username and container == self.USER_RESULTS_CONTAINER:
            return f"{username}/{filename}"
        return filename

    def upload_file(self, file_data: bytes, filename: str,
                   container: str, username: Optional[str] = None,
                   content_type: Optional[str] = None) -> str:
        """
        Upload a file to Azure Blob Storage.

        Args:
            file_data: File content as bytes
            filename: Name of the file
            container: Target container name
            username: Optional username for organizing files
            content_type: MIME type (auto-detected if not provided)

        Returns:
            Blob URL
        """
        try:
            blob_path = self._get_blob_path(container, filename, username)
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_path
            )

            # Auto-detect content type
            if not content_type:
                if filename.endswith('.xlsx'):
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif filename.endswith('.html'):
                    content_type = 'text/html'
                elif filename.endswith('.csv'):
                    content_type = 'text/csv'
                else:
                    content_type = 'application/octet-stream'

            # Upload with content settings
            content_settings = ContentSettings(content_type=content_type)
            blob_client.upload_blob(
                file_data,
                overwrite=True,
                content_settings=content_settings
            )

            logger.info(f"Uploaded file to Azure: {blob_path}")
            return blob_client.url

        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            raise

    def download_file(self, filename: str, container: str,
                     username: Optional[str] = None) -> bytes:
        """
        Download a file from Azure Blob Storage.

        Args:
            filename: Name of the file
            container: Source container name
            username: Optional username for file organization

        Returns:
            File content as bytes
        """
        try:
            blob_path = self._get_blob_path(container, filename, username)
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_path
            )

            download_stream = blob_client.download_blob()
            return download_stream.readall()

        except ResourceNotFoundError:
            logger.error(f"File not found: {filename} in {container}")
            raise FileNotFoundError(f"File {filename} not found in Azure Storage")
        except Exception as e:
            logger.error(f"Failed to download file {filename}: {e}")
            raise

    def download_file_stream(self, filename: str, container: str,
                           username: Optional[str] = None) -> io.BytesIO:
        """
        Download a file as a BytesIO stream (useful for send_file in Flask).

        Args:
            filename: Name of the file
            container: Source container name
            username: Optional username for file organization

        Returns:
            BytesIO stream
        """
        file_data = self.download_file(filename, container, username)
        return io.BytesIO(file_data)

    def delete_file(self, filename: str, container: str,
                   username: Optional[str] = None) -> bool:
        """
        Delete a file from Azure Blob Storage.

        Args:
            filename: Name of the file
            container: Container name
            username: Optional username for file organization

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            blob_path = self._get_blob_path(container, filename, username)
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_path
            )
            blob_client.delete_blob()
            logger.info(f"Deleted file from Azure: {blob_path}")
            return True

        except ResourceNotFoundError:
            logger.warning(f"File not found for deletion: {filename}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            raise

    def list_user_files(self, username: str, container: str = None) -> List[str]:
        """
        List all files for a specific user.

        Args:
            username: Username
            container: Container name (defaults to USER_RESULTS_CONTAINER)

        Returns:
            List of filenames
        """
        if container is None:
            container = self.USER_RESULTS_CONTAINER

        try:
            container_client = self.blob_service_client.get_container_client(container)
            blob_list = container_client.list_blobs(name_starts_with=f"{username}/")

            # Extract just the filename (remove username prefix)
            files = []
            for blob in blob_list:
                filename = blob.name.replace(f"{username}/", "", 1)
                files.append(filename)

            return files

        except Exception as e:
            logger.error(f"Failed to list files for user {username}: {e}")
            return []

    def file_exists(self, filename: str, container: str,
                   username: Optional[str] = None) -> bool:
        """
        Check if a file exists in Azure Blob Storage.

        Args:
            filename: Name of the file
            container: Container name
            username: Optional username for file organization

        Returns:
            True if file exists, False otherwise
        """
        try:
            blob_path = self._get_blob_path(container, filename, username)
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_path
            )
            return blob_client.exists()

        except Exception as e:
            logger.error(f"Error checking file existence {filename}: {e}")
            return False

    def rename_file(self, old_filename: str, new_filename: str,
                   container: str, username: Optional[str] = None) -> bool:
        """
        Rename a file in Azure Blob Storage (copy + delete).

        Args:
            old_filename: Current filename
            new_filename: New filename
            container: Container name
            username: Optional username for file organization

        Returns:
            True if renamed successfully, False otherwise
        """
        try:
            # Download old file
            file_data = self.download_file(old_filename, container, username)

            # Upload with new name
            self.upload_file(file_data, new_filename, container, username)

            # Delete old file
            self.delete_file(old_filename, container, username)

            logger.info(f"Renamed file: {old_filename} -> {new_filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to rename file {old_filename}: {e}")
            return False

    def clean_user_temp_files(self, username: str):
        """
        Clean up temporary files for a specific user.

        Args:
            username: Username
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.TEMP_CONTAINER
            )
            blob_list = container_client.list_blobs(name_starts_with=f"{username}_")

            deleted_count = 0
            for blob in blob_list:
                try:
                    container_client.delete_blob(blob.name)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {blob.name}: {e}")

            logger.info(f"Cleaned up {deleted_count} temp files for user {username}")

        except Exception as e:
            logger.error(f"Failed to clean temp files for {username}: {e}")

    def cleanup_old_temp_files(self, hours: int = 24):
        """
        Clean up temporary files older than specified hours.

        Args:
            hours: Age threshold in hours (default: 24)
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.TEMP_CONTAINER
            )

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            deleted_count = 0

            for blob in container_client.list_blobs():
                if blob.last_modified.replace(tzinfo=None) < cutoff_time:
                    try:
                        container_client.delete_blob(blob.name)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete old temp file {blob.name}: {e}")

            logger.info(f"Cleaned up {deleted_count} old temp files")

        except Exception as e:
            logger.error(f"Failed to cleanup old temp files: {e}")

    def get_file_size(self, filename: str, container: str,
                     username: Optional[str] = None) -> Optional[int]:
        """
        Get the size of a file in bytes.

        Args:
            filename: Name of the file
            container: Container name
            username: Optional username for file organization

        Returns:
            File size in bytes, or None if not found
        """
        try:
            blob_path = self._get_blob_path(container, filename, username)
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_path
            )
            properties = blob_client.get_blob_properties()
            return properties.size

        except Exception as e:
            logger.error(f"Failed to get file size for {filename}: {e}")
            return None


# Global storage instance (initialized in app.py)
storage: Optional[AzureBlobStorage] = None


def init_storage(connection_string: str):
    """
    Initialize the global Azure Blob Storage instance.

    Args:
        connection_string: Azure Storage connection string
    """
    global storage
    if connection_string:
        storage = AzureBlobStorage(connection_string)
        logger.info("Azure Blob Storage initialized")
    else:
        logger.warning("Azure Storage connection string not provided - storage not initialized")


def get_storage() -> AzureBlobStorage:
    """
    Get the global storage instance.

    Returns:
        AzureBlobStorage instance

    Raises:
        RuntimeError: If storage not initialized
    """
    if storage is None:
        raise RuntimeError("Azure Blob Storage not initialized. Call init_storage() first.")
    return storage