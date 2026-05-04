"""
Object storage integration package.

Provides the ``MinIOService`` wrapper for interacting with the MinIO
S3-compatible object storage, including bucket management, file upload /
download, deletion, and pre-signed URL generation.
"""

from app.integrations.object_storage.minio_client import MinIOService

__all__ = ["MinIOService"]
