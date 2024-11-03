import logging
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import httpx
from typing import Optional, Generator

from config import APIConfig
from constants import ProcessType, Result
from media import PhotoProcessor
from storage import StorageClient
from media import VideoProcessor


@dataclass
class VideoFile:
    """Represents a video file in the system."""

    scan_uuid: str
    extension: str
    local_path: Path

    @property
    def output_path(self) -> Path:
        """Path for processed output file."""
        return Path(f"{self.scan_uuid}.mp4")

    @property
    def converted_path(self) -> Path:
        """Path for FFmpeg converted file."""
        return Path(f"{self.scan_uuid}_ffmpeg.mp4")

    @property
    def remote_path(self) -> str:
        """Path in remote storage."""
        return f"{self.scan_uuid}.{self.extension}"

    @property
    def content_type(self) -> str:
        """Content type for upload."""
        return "video/mp4"


@dataclass
class PhotoFile:
    """Represents a photo file in the system."""

    scan_uuid: str
    local_path: Path

    @property
    def remote_path(self) -> str:
        """Path in remote storage."""
        return f"{self.scan_uuid}.jpg"


class ProcessingHandler:
    """Handles both videos and photos"""

    def __init__(
        self,
        storage_client: StorageClient,
        video_processor: VideoProcessor,
        photo_processor: PhotoProcessor,
        api_config: APIConfig,
    ):
        self.storage_client = storage_client
        self.video_processor = video_processor
        self.photo_processor = photo_processor
        self.api_config = api_config
        self.transport = httpx.AsyncHTTPTransport(retries=api_config.retries)

    @contextmanager
    def _manage_temp_files(self, *files: Path) -> Generator[None, None, None]:
        """
        A context manager for managing and cleaning up temporary files.

        This context manager yields control to the block of code that uses it,
        ensuring that specified temporary files are removed after the block
        is executed, regardless of whether an error occurred.

        Args:
            *files (Path): One or more paths to temporary files that will be cleaned up
            after use.

        Yields:
            None: Control is passed to the context block.
        """
        try:
            yield
        finally:
            for file in files:
                try:
                    os.remove(file)
                    logging.debug(f"Cleaned up temporary file: {file}")
                except FileNotFoundError:
                    pass

    def _convert_if_mov(self, video: VideoFile) -> Path:
        """
        Converts a MOV video file to MP4 format if the file extension is MOV.

        If the provided video file does not have a 'mov' extension, the function
        returns the original local path. If the extension is 'mov', the function
        converts the file to MP4 format and returns the path of the converted file.

        Args:
            video (VideoFile): The video file object containing the local path and
            converted path.

        Returns:
            Path: The path of the converted MP4 file or the original local path
            if no conversion was necessary.
        """
        if video.extension.lower() != "mov":
            return video.local_path

        logging.info(f"Converting MOV file: {video.local_path}")
        self.video_processor.mov_to_mp4(video.local_path, video.converted_path)
        return video.converted_path

    async def process_file(
        self, scan_uuid: str, process_type: ProcessType, file_extension: str
    ) -> None:
        """
        Processes a file based on its type and extension.

        This asynchronous method handles the processing of a file identified
        by its scan UUID, process type, and file extension. If processing is
        successful, a callback is sent with the results.

        Args:
            scan_uuid (str): The unique identifier for the scan associated with the file.
            process_type (ProcessType): The type of processing to be applied to the file.
            file_extension (str): The file extension of the input file.

        Raises:
            Exception: If an error occurs during the file processing or callback sending.
        """
        try:
            result = await self._handle_processing(
                scan_uuid, process_type, file_extension
            )
            if result:
                await self._send_callback(scan_uuid, process_type, result)
        except Exception as e:
            logging.error(f"Error processing file: {str(e)}")
            raise

    async def _handle_processing(
        self, scan_uuid: str, process_type: ProcessType, file_extension: str
    ) -> Optional[Result]:
        """
        Handles the processing of a file based on its type.

        This asynchronous method determines the appropriate processing function
        to call based on the specified process type (video or photo). It returns
        the result of the processing.

        Args:
            scan_uuid (str): The unique identifier for the scan associated with the file.
            process_type (ProcessType): The type of processing to be applied (video or photo).
            file_extension (str): The file extension of the input file (used for video processing).

        Returns:
            Optional[Result]: The result of the processing, or None if the process type
            is unrecognized.
        """
        if process_type == "video":
            return await self._handle_video(scan_uuid, file_extension)
        elif process_type == "photo":
            return await self._handle_photo(scan_uuid)
        return None

    async def _send_callback(
        self, scan_uuid: str, process_type: ProcessType, result: Result
    ) -> None:
        """
        Sends a callback to the backend with processing results.

        This asynchronous method sends a POST request to the backend API,
        notifying it of the processing results associated with a specific scan
        UUID and process type. It raises an exception if the callback fails.

        Args:
            scan_uuid (str): The unique identifier for the scan associated with the callback.
            process_type (ProcessType): The type of processing that was performed.
            result (Result): The result of the processing, which will be sent in the callback.

        Raises:
            RuntimeError: If the callback fails with a non-200 status code.
        """
        async with httpx.AsyncClient(transport=self.transport) as client:
            response = await client.post(
                f"{self.api_config.backend_url}/api/scans/{scan_uuid}/callback",
                json={"process_type": process_type, "result": result.dict()},
                timeout=300,
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Callback failed with status {response.status_code}"
                )
            logging.info("Successfully called callback")

    async def _handle_video(self, scan_uuid: str, file_extension: str) -> Result:
        """
        Process video files with proper cleanup and error handling.

        Args:
            scan_uuid: Unique identifier for the video
            file_extension: File extension of the video

        Returns:
            Result object with processing results

        Raises:
            RuntimeError: If video processing fails
        """
        local_path = Path(f"{uuid.uuid4()}.{file_extension.lower()}")
        video = VideoFile(scan_uuid, file_extension, local_path)
        storage_path = f"{self.storage_client.video_path}{video.remote_path}"
        try:
            with self._manage_temp_files(
                video.local_path, video.output_path, video.converted_path
            ):
                self.storage_client.download_file(storage_path, video.local_path)
                logging.info(f"Downloaded video: {storage_path}")

                process_path = self._convert_if_mov(video)

                result = self.video_processor.process_video(
                    process_path, video.output_path
                )
                if not result:
                    raise RuntimeError(f"Video processing failed for {scan_uuid}")

                upload_path = storage_path.replace(file_extension, "mp4")
                logging.info(f"Uploading processed video to: {upload_path}")
                self.storage_client.upload_file(
                    upload_path, video.output_path, video.content_type
                )

                return result

        except Exception as e:
            logging.error(f"Error processing video {scan_uuid}: {str(e)}")
            raise

    async def _handle_photo(self, scan_uuid: str) -> Result:
        """
        Handles the processing of a photo file associated with a specific scan UUID.

        This asynchronous method downloads the photo from storage, processes it,
        and returns the result. It manages temporary file cleanup to ensure no
        leftover files remain.

        Args:
            scan_uuid (str): The unique identifier for the scan associated with the photo.

        Returns:
            Result: The result of processing the photo.

        Raises:
            Exception: If an error occurs during file download or processing.
        """

        local_path = Path(f"{uuid.uuid4()}.jpg")
        photo = PhotoFile(scan_uuid, local_path)
        storage_path = f"{self.storage_client.photo_path}{photo.remote_path}"
        try:
            with self._manage_temp_files(photo.local_path):
                self.storage_client.download_file(storage_path, photo.local_path)
                result = self.photo_processor.process_photo(photo)
                return result

        except Exception as e:
            logging.error(f"Error processing video {scan_uuid}: {str(e)}")
            raise
