import subprocess
from typing import Union, Literal

from pydantic import BaseModel, Field
from pathlib import Path
import os
from dotenv import load_dotenv

type FacingDirection = Union[Literal["left"], Literal["right"]]


class MinioConfig(BaseModel):
    endpoint: str = Field()
    access_key: str = Field()
    secret_key: str = Field()
    bucket_name: str = Field()
    secure: bool = Field(default=True)
    video_path: str = Field(default="videos/pedalling/")
    photo_path: str = Field(default="photos/body/")


class APIConfig(BaseModel):
    backend_url: str = Field()
    retries: int = Field(default=3)


class ProcessingConfig(BaseModel):
    landmarker_path: Path = Field(default=Path("models/pose_landmarker.task"))
    segmenter_path: Path = Field(default=Path("models/selfie_segmenter.tflite"))
    gpu_enabled: bool = Field(default=True)
    min_pose_confidence: float = Field(default=0.8)
    min_tracking_confidence: float = Field(default=0.8)


class Config(BaseModel):
    minio: MinioConfig
    api: APIConfig
    processing: ProcessingConfig
    environment: str = Field(default="production")


def get_config() -> Config:
    """
    Loads the configuration from environment variables.

    Uses `load_dotenv` to load the environment variables and returns an instance of
    the `Config` class populated with settings for MinIO, API configuration,
    processing options, and the environment.

    Returns:
        Config: An instance of the Config class containing the loaded configuration.
    """
    load_dotenv()

    return Config(
        minio=MinioConfig(
            endpoint=os.getenv("S3_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("S3_CLIENT_ID", ""),
            secret_key=os.getenv("S3_CLIENT_SECRET", ""),
            bucket_name=os.getenv("S3_BUCKET", ""),
            secure=os.getenv("ENV", "PROD").upper() != "DEV",
        ),
        api=APIConfig(
            backend_url=os.getenv("BACKEND_URL", ""),
            retries=int(os.getenv("API_RETRIES", "3")),
        ),
        processing=ProcessingConfig(gpu_enabled=check_gpu_availability()),
        environment=os.getenv("ENV", "production"),
    )


def check_gpu_availability():
    """
    Checks the availability of a GPU encoder for video processing.

    This function uses `ffmpeg` to list available encoders and checks if the
    'h264_nvenc' encoder is present in the output.

    Returns:
       bool: True if the 'h264_nvenc' encoder is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"], capture_output=True, text=True, check=True
        )
        return "h264_nvenc" in result.stdout
    except:
        return False
