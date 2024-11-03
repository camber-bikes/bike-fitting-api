import logging
from pathlib import Path
from typing import Optional
from minio import Minio
from config import MinioConfig


class StorageClient:
    """
    A client for interacting with MinIO storage, handling file storage, and retrieval operations.
    """

    def __init__(self, config: MinioConfig):
        self.config = config
        self.client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )
        self.video_path = config.video_path
        self.photo_path = config.photo_path
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Checks if the specified storage bucket exists in MinIO, and creates it if necessary.

        Raises:
            Exception: If there is an error during the bucket existence check or creation process.
        """
        if not self.client.bucket_exists(self.config.bucket_name):
            self.client.make_bucket(self.config.bucket_name)
            logging.info(f"Created bucket '{self.config.bucket_name}'")

    def download_file(self, object_path: str, local_path: Path) -> None:
        """
        Downloads a file from the storage bucket to a specified local path.

        Args:
            object_path (str): The path of the file in the storage bucket.
            local_path (Path): The local file path where the file will be saved.

        Raises:
            Exception: If an error occurs during the download process.
        """
        try:
            print(object_path)
            data = self.client.get_object(self.config.bucket_name, object_path)
            with open(local_path, "wb") as file_data:
                for d in data.stream(32 * 1024):
                    file_data.write(d)
        except Exception as e:
            logging.error(f"Error downloading file {object_path}: {str(e)}")
            raise

    def upload_file(
        self, object_path: str, local_path: Path, content_type: Optional[str] = None
    ) -> None:
        """
        Uploads a local file to the storage bucket.

        Args:
            object_path (str): The destination path in the storage bucket.
            local_path (Path): The path of the local file to upload.
            content_type (Optional[str]): The MIME type of the file. If not provided,
                the content type is inferred from the file extension.

        Raises:
            Exception: If an error occurs during the upload process.
        """
        try:
            self.client.fput_object(
                self.config.bucket_name,
                object_path,
                str(local_path),
                content_type=content_type,
            )
        except Exception as e:
            logging.error(f"Error uploading file {local_path}: {str(e)}")
            raise

    def delete_object(self, object_path: str) -> None:
        """
        Deletes an object from the storage bucket.

        Args:
            object_path (str): The path of the object in the storage bucket to be deleted.

        Raises:
            Exception: If an error occurs during the deletion process.
        """
        try:
            self.client.remove_object(self.config.bucket_name, object_path)
        except Exception as e:
            logging.error(f"Error deleting object {object_path}: {str(e)}")
            raise
