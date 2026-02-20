"""File storage service with Azure Blob Storage and local filesystem fallback."""

import logging
import os
import uuid
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

# Allowed MIME types and max sizes
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES | {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class StorageService:
    """Abstraction for file storage. Uses Azure Blob in production, local FS in dev."""

    def __init__(self):
        self._blob_client = None

    def _get_blob_service(self):
        if self._blob_client is None and settings.azure_storage_connection_string:
            from azure.storage.blob import BlobServiceClient

            self._blob_client = BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
        return self._blob_client

    def _generate_blob_name(self, clinic_id: uuid.UUID, category: str, filename: str) -> str:
        """Generate a unique blob name: clinic_id/category/date/uuid-filename."""
        ext = os.path.splitext(filename)[1].lower() if filename else ""
        date_prefix = datetime.utcnow().strftime("%Y/%m")
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        return f"{clinic_id}/{category}/{date_prefix}/{unique_name}"

    async def upload(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        clinic_id: uuid.UUID,
        category: str = "general",
    ) -> str:
        """Upload a file and return its URL.

        Args:
            file_data: File content bytes.
            filename: Original filename.
            content_type: MIME type.
            clinic_id: Clinic that owns the file.
            category: Storage category (e.g. 'avatars', 'attachments', 'logos').

        Returns:
            Public URL of the uploaded file.
        """
        if len(file_data) > MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

        blob_name = self._generate_blob_name(clinic_id, category, filename)

        blob_service = self._get_blob_service()
        if blob_service:
            return await self._upload_azure(blob_service, blob_name, file_data, content_type)
        else:
            return await self._upload_local(blob_name, file_data)

    async def _upload_azure(self, blob_service, blob_name: str, data: bytes, content_type: str) -> str:
        """Upload to Azure Blob Storage."""
        from azure.storage.blob import ContentSettings

        container_client = blob_service.get_container_client(settings.azure_storage_container)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )
        return blob_client.url

    async def _upload_local(self, blob_name: str, data: bytes) -> str:
        """Fallback: save to local filesystem for development."""
        upload_dir = os.path.join("uploads", os.path.dirname(blob_name))
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join("uploads", blob_name)
        with open(filepath, "wb") as f:
            f.write(data)
        return f"/static/uploads/{blob_name}"

    async def delete(self, url: str) -> None:
        """Delete a file by its URL."""
        blob_service = self._get_blob_service()
        if blob_service and settings.azure_storage_container in url:
            try:
                # Extract blob name from URL
                blob_name = url.split(f"{settings.azure_storage_container}/")[1]
                container_client = blob_service.get_container_client(
                    settings.azure_storage_container
                )
                container_client.delete_blob(blob_name)
            except Exception:
                logger.warning("Failed to delete blob: %s", url)
        elif url.startswith("/static/uploads/"):
            filepath = url.replace("/static/uploads/", "uploads/")
            if os.path.exists(filepath):
                os.remove(filepath)


# Singleton
storage_service = StorageService()
