"""Storage service for document originals"""
import io
import os
from pathlib import Path
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Handle storage of original documents (MinIO or local FS)"""

    def __init__(self):
        self.use_minio = settings.minio_endpoint.startswith("http")
        if self.use_minio:
            self.client = self._init_minio()
        else:
            self.local_path = Path(settings.storage_local_path)
            self.local_path.mkdir(parents=True, exist_ok=True)

    def _init_minio(self) -> Minio:
        """Initialize MinIO client"""
        endpoint = settings.minio_endpoint.replace("http://", "").replace("https://", "")
        secure = settings.minio_endpoint.startswith("https")
        client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )
        # Ensure bucket exists
        try:
            if not client.bucket_exists(settings.minio_bucket):
                client.make_bucket(settings.minio_bucket)
                logger.info(f"Created MinIO bucket: {settings.minio_bucket}")
        except S3Error as e:
            logger.error(f"MinIO error: {e}")
        return client

    def store(self, sha256: str, content: bytes, mime_type: str) -> str:
        """Store document and return storage key"""
        key = f"{sha256[:2]}/{sha256}"
        if self.use_minio:
            try:
                # Wrap bytes in BytesIO for MinIO
                data_stream = io.BytesIO(content)
                self.client.put_object(
                    settings.minio_bucket,
                    key,
                    data=data_stream,
                    length=len(content),
                    content_type=mime_type,
                )
                logger.info(f"Stored document in MinIO: {key}")
            except S3Error as e:
                logger.error(f"MinIO store error: {e}")
                raise
        else:
            file_path = self.local_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            logger.info(f"Stored document locally: {file_path}")
        return key

    def retrieve(self, sha256: str) -> Optional[bytes]:
        """Retrieve document by sha256"""
        key = f"{sha256[:2]}/{sha256}"
        if self.use_minio:
            try:
                response = self.client.get_object(settings.minio_bucket, key)
                return response.read()
            except S3Error as e:
                logger.error(f"MinIO retrieve error: {e}")
                return None
        else:
            file_path = self.local_path / key
            if file_path.exists():
                return file_path.read_bytes()
            return None

    def delete(self, sha256: str):
        """Delete document by sha256"""
        key = f"{sha256[:2]}/{sha256}"
        if self.use_minio:
            try:
                self.client.remove_object(settings.minio_bucket, key)
                logger.info(f"Deleted document from MinIO: {key}")
            except S3Error as e:
                logger.error(f"MinIO delete error: {e}")
        else:
            file_path = self.local_path / key
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted document locally: {file_path}")


storage_service = StorageService()
