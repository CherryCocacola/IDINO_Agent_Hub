"""
MinIO (S3-compatible) object storage wrapper for the Document Utilization System.

Provides the ``MinIOService`` class for bucket lifecycle management,
file upload / download, deletion, and pre-signed URL generation.
"""

from __future__ import annotations

import io
import logging
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MinIOService:
    """High-level wrapper around the MinIO Python client.

    Encapsulates bucket management, file CRUD, and pre-signed URL
    generation behind a simple, application-oriented interface.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool | None = None,
    ) -> None:
        self.endpoint = endpoint or settings.minio_endpoint
        self.access_key = access_key or settings.minio_access_key
        self.secret_key = secret_key or settings.minio_secret_key
        self.secure = secure if secure is not None else settings.minio_secure
        self._client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

    # ------------------------------------------------------------------
    # Bucket management
    # ------------------------------------------------------------------

    def ensure_bucket(self, bucket_name: str) -> None:
        """Create the bucket if it does not already exist.

        Parameters
        ----------
        bucket_name:
            Name of the S3 bucket to create.
        """
        try:
            if not self._client.bucket_exists(bucket_name):
                self._client.make_bucket(bucket_name)
                logger.info("Created MinIO bucket: %s", bucket_name)
            else:
                logger.debug("Bucket '%s' already exists", bucket_name)
        except S3Error as exc:
            logger.error("Failed to ensure bucket '%s': %s", bucket_name, exc)
            raise

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: bytes | str | io.IOBase,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to MinIO.

        Accepts raw bytes, a file path string, or a file-like object.

        Parameters
        ----------
        bucket:
            Target bucket name.
        object_name:
            Object key (path) within the bucket.
        file_data:
            Raw bytes, a local file path, or a readable file-like object.
        content_type:
            MIME type for the uploaded object.

        Returns
        -------
        str
            The object name (key) of the uploaded file.
        """
        self.ensure_bucket(bucket)

        try:
            if isinstance(file_data, str):
                # Treat as a file path
                self._client.fput_object(
                    bucket_name=bucket,
                    object_name=object_name,
                    file_path=file_data,
                    content_type=content_type,
                )
            elif isinstance(file_data, bytes):
                data_stream = io.BytesIO(file_data)
                self._client.put_object(
                    bucket_name=bucket,
                    object_name=object_name,
                    data=data_stream,
                    length=len(file_data),
                    content_type=content_type,
                )
            else:
                # File-like object -- determine length
                file_data.seek(0, io.SEEK_END)
                length = file_data.tell()
                file_data.seek(0)
                self._client.put_object(
                    bucket_name=bucket,
                    object_name=object_name,
                    data=file_data,
                    length=length,
                    content_type=content_type,
                )

            logger.info(
                "Uploaded '%s' to bucket '%s' (%s)",
                object_name,
                bucket,
                content_type,
            )
            return object_name

        except S3Error as exc:
            logger.error("Upload failed for '%s/%s': %s", bucket, object_name, exc)
            raise

    def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from MinIO and return its contents as bytes.

        Parameters
        ----------
        bucket:
            Source bucket name.
        object_name:
            Object key (path) within the bucket.

        Returns
        -------
        bytes
            The raw file content.
        """
        try:
            response = self._client.get_object(
                bucket_name=bucket,
                object_name=object_name,
            )
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(
                "Downloaded '%s' from bucket '%s' (%d bytes)",
                object_name,
                bucket,
                len(data),
            )
            return data
        except S3Error as exc:
            logger.error("Download failed for '%s/%s': %s", bucket, object_name, exc)
            raise

    def get_object_bytes(self, bucket: str, object_name: str) -> bytes:
        """Return the raw object bytes for internal API proxying.

        API 프록시 다운로드 (Phase 4 S2 D10) 에서 사용하기 위한 ``download_file``
        의 의미 별칭. 호출자는 "디스크에 저장" 이 아니라 "메모리에 읽어 그대로
        스트리밍" 한다는 의도가 더 명확해진다.

        Parameters
        ----------
        bucket:
            Source bucket name.
        object_name:
            Object key (path) within the bucket.

        Returns
        -------
        bytes
            The raw file content.

        Raises
        ------
        minio.error.S3Error:
            Object 가 존재하지 않거나 권한 문제 등 S3 계열 오류.
            ``NoSuchKey`` 는 상위 서비스 레이어에서 410 (만료) 으로 매핑한다.
        """

        # 내부적으로는 ``download_file`` 과 동일한 경로. 단일 구현 원칙 (P1) 을
        # 유지하기 위해 중복 로직을 만들지 않는다.
        return self.download_file(bucket=bucket, object_name=object_name)

    def delete_file(self, bucket: str, object_name: str) -> None:
        """Delete a file from MinIO.

        Parameters
        ----------
        bucket:
            Bucket containing the object.
        object_name:
            Object key to delete.
        """
        try:
            self._client.remove_object(
                bucket_name=bucket,
                object_name=object_name,
            )
            logger.info("Deleted '%s' from bucket '%s'", object_name, bucket)
        except S3Error as exc:
            logger.error("Delete failed for '%s/%s': %s", bucket, object_name, exc)
            raise

    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """Generate a pre-signed URL for temporary access to a file.

        Parameters
        ----------
        bucket:
            Bucket containing the object.
        object_name:
            Object key to generate the URL for.
        expires:
            URL validity duration in seconds (default: 1 hour).

        Returns
        -------
        str
            Pre-signed URL.
        """
        try:
            url = self._client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(seconds=expires),
            )
            logger.debug(
                "Generated pre-signed URL for '%s/%s' (expires in %ds)",
                bucket,
                object_name,
                expires,
            )
            return url
        except S3Error as exc:
            logger.error(
                "Pre-signed URL generation failed for '%s/%s': %s",
                bucket,
                object_name,
                exc,
            )
            raise
