import asyncio
import logging
from typing import Any, Dict
import runpod

from config import get_config
from media import PhotoProcessor
from storage import StorageClient
from media import MediaPipeProcessor, VideoProcessor
from handlers import ProcessingHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def initialize_services() -> ProcessingHandler:
    """
    Initializes and configures the processing services for handling video and photo files.

    Returns:
        ProcessingHandler: An instance of ProcessingHandler with configured storage,
        video, and photo processors.
    """
    config = get_config()

    storage_client = StorageClient(config.minio)

    mediapipe_processor = MediaPipeProcessor(
        model_path=config.processing.landmarker_path,
        gpu_enabled=config.processing.gpu_enabled,
        min_pose_confidence=config.processing.min_pose_confidence,
        min_tracking_confidence=config.processing.min_tracking_confidence,
    )

    video_processor = VideoProcessor(mediapipe_processor, config.processing.gpu_enabled)
    photo_processor = PhotoProcessor(config.processing.segmenter_path)
    processing_handler = ProcessingHandler(
        storage_client=storage_client,
        video_processor=video_processor,
        photo_processor=photo_processor,
        api_config=config.api,
    )

    return processing_handler


async def process_job(job: Dict[str, Any]) -> str:
    """
    Processes a job by initializing services and executing file processing tasks.

    Args:
        job (Dict[str, Any]): A dictionary containing job details, with 'input'
            specifying 'process_type' (str), 'scan_uuid' (str), and 'file_extension' (str).

    Returns:
        str: A message indicating successful processing.

    Raises:
        Exception: If an error occurs during job processing.
    """
    try:
        handler = initialize_services()

        process_type = job["input"]["process_type"]
        scan_uuid = job["input"]["scan_uuid"]
        file_extension = job["input"]["file_extension"]

        await handler.process_file(scan_uuid, process_type, file_extension)
        return "Processing completed successfully"
    except Exception as e:
        logging.error(f"Job processing failed: {str(e)}")
        raise


def serverless_handler(job: Dict[str, Any]) -> str:
    """RunPod serverless handler."""
    asyncio.create_task(process_job(job))
    return "Started processing"


def main():
    """Main entry point for the application."""
    runpod.serverless.start(
        {
            "handler": serverless_handler,
        }
    )


if __name__ == "__main__":
    main()
