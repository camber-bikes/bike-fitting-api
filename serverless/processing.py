import asyncio
import logging
import os
import subprocess
import uuid
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
import runpod
from dotenv import load_dotenv
from httpx import AsyncHTTPTransport, AsyncClient
from mediapipe.tasks import python as mp_py
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)
from minio import Minio
from pydantic import BaseModel

from constants import (
    POSE_LANDMARKER_TASK,
    RETRIES,
    SELFIE_SEGMENTER_TFLITE,
    FacingDirection,
    FrameObject,
    ProcessType,
)
import file_operations
from calculation import determine_facing_direction, get_knee_angle, get_elbow_angle
from drawing import draw_wireframe

load_dotenv()


class Frame(BaseModel):
    knee_angle: float
    elbow_angle: float
    joints: Any


class Result(BaseModel):
    height: int
    width: int
    data: Any


class VideoData(BaseModel):
    frames: list[Frame]
    facing_direction: FacingDirection


class PhotoData(BaseModel):
    highest_point: float
    lowest_point: float


frames: list[Frame] = []

transport = AsyncHTTPTransport(retries=RETRIES)

backend_url = os.getenv("BACKEND_URL") or ""
if backend_url == "":
    raise Exception("BACKEND_URL environment variable not set")

minio_client = Minio(
    os.getenv("S3_ENDPOINT") or "localhost:9000",
    access_key=os.getenv("S3_CLIENT_ID"),
    secret_key=os.getenv("S3_CLIENT_SECRET"),
    secure=os.getenv("ENV") != "DEV",
)

bucket_name = os.getenv("S3_BUCKET") or ""
if bucket_name == "":
    raise Exception("S3_BUCKET environment variable not set")

found = minio_client.bucket_exists(bucket_name)
if not found:
    minio_client.make_bucket(bucket_name)
    logging.info(f"created bucket '{bucket_name}'")


async def call_callback(scan_uuid: str, process_type: ProcessType, result: Result):
    logging.info("SENDING CALLBACK....")
    async with AsyncClient(transport=transport) as client:
        response = await client.post(
            backend_url + f"/api/scans/{scan_uuid}/callback",
            content=f'{{"process_type": "{process_type}", "result": {result.model_dump_json()}}}'.encode(),
            headers={"content_type": "application/json"},
        )
        if response.status_code != 200:
            raise Exception(result)
        logging.info("SUCCESSFULLY CALLED CALLBACK")


def convert_mov_to_mp4(scan_uuid, tmp_file):
    logging.info("DETECTED .MOV")
    logging.info("STARTED FFMPEG CONVERSION")
    ffmpeg_file_name = scan_uuid + "_ffmpeg" + ".mp4"
    logging.info(f"OUTPUT_NAME: {ffmpeg_file_name}")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                tmp_file,
                "-c:v",
                "libx264",
                "-crf",
                "23",
                "-preset",
                "veryfast",
                ffmpeg_file_name,
            ],
            check=True,
        )
        logging.info(f"Successfully converted {tmp_file} to {ffmpeg_file_name}")

        os.remove(tmp_file)
    except subprocess.CalledProcessError as e:
        logging.error(f"ffmpeg conversion error: {e}")
        raise Exception("Error converting mov to mp4")

    return ffmpeg_file_name

def mediapipe_processing(temp_file_name, scan_uuid):
    base_options = mp_py.BaseOptions(
        model_asset_path=POSE_LANDMARKER_TASK,
        #delegate=mp.tasks.BaseOptions.Delegate.GPU,
    )
    options = mp_py.vision.PoseLandmarkerOptions(
        running_mode=VisionTaskRunningMode.VIDEO,
        min_pose_detection_confidence=0.8,
        min_tracking_confidence=0.8,
        base_options=base_options,
        output_segmentation_masks=True,
    )

    detector = mp_py.vision.PoseLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(temp_file_name)

    if not cap.isOpened():
        raise Exception("Could not open video")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    output_filename = scan_uuid + ".mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))
    landmarks = []

    timestamp_ms = 0
    facing_direction: FacingDirection = "left"
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            logging.info("REACHED END OF VIDEO")
            break

        timestamp_ms += 1000 / fps

        dimmed_frame = cv2.addWeighted(frame, 0.4, np.zeros_like(frame), 0.4, 0)

        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)  # type: ignore
        results = detector.detect_for_video(image, int(timestamp_ms))

        if not results.pose_landmarks:
            out.write(dimmed_frame)
            continue

        pose_landmarks = results.pose_landmarks[0]
        landmarks.append(pose_landmarks)

        overlay = np.zeros_like(frame, dtype=np.uint8)

        facing_direction = determine_facing_direction(pose_landmarks)
        frame_obj = FrameObject(width=width, height=height)

        draw_wireframe(overlay, pose_landmarks, facing_direction)
        knee_angle = get_knee_angle(pose_landmarks, frame_obj, facing_direction)
        elbow_angle = get_elbow_angle(pose_landmarks, frame_obj, facing_direction)

        result_frame = cv2.addWeighted(dimmed_frame, 1, overlay, 1, 0)

        out.write(result_frame)

        single_frame = Frame(knee_angle=knee_angle, elbow_angle=elbow_angle, joints=pose_landmarks)
        frames.append(single_frame)

    cap.release()
    out.release()

    logging.info("DONE WITH DRAWING VIDEO")

    video_data = VideoData(frames=frames, facing_direction=facing_direction)

    result = Result(height=height, width=width, data=video_data)

    return result


def process_video(scan_uuid, file_extension):
    temp_uuid = str(uuid.uuid4())
    s3_url = f"videos/pedalling/{scan_uuid}.{file_extension}"
    logging.info(f"S3_URL: {s3_url}")
    file = minio_client.get_object(bucket_name, s3_url)

    temp_file_name = f"{temp_uuid}+.{file_extension}"
    with open(temp_file_name, "wb") as temp_file:
        temp_file.write(file.data)

    logging.info(f"TEMP_NAME: {temp_file_name}")
    logging.info("VIDEO")

    if temp_file_name.lower().endswith(".mov"):
        minio_client.remove_object(bucket_name, s3_url)
        s3_url = s3_url.lower().replace(".mov", ".mp4")
        ffmpeg_name = convert_mov_to_mp4(scan_uuid, temp_file_name)
        temp_file_name = ffmpeg_name

    result = mediapipe_processing(temp_file_name, scan_uuid)

    output_filename = scan_uuid + ".mp4"

    minio_client.fput_object(bucket_name, s3_url, output_filename, content_type="video/mp4")

    logging.info("UPLOADED VIDEO TO S3")

    os.remove(output_filename)
    os.remove(temp_file_name)

    logging.info("DELETED TEMPORARY FILE")

    return result


def process_photo(scan_uuid, process_type):
    logging.info("PHOTO")

    temp_file_path = file_operations.download_image(
        minio_client, bucket_name, scan_uuid, process_type
    )
    base_options = mp_py.BaseOptions(model_asset_path=SELFIE_SEGMENTER_TFLITE)
    options = mp_py.vision.ImageSegmenterOptions(
        running_mode=VisionTaskRunningMode.IMAGE,
        base_options=base_options,
        output_category_mask=True,
    )
    segmenter = mp_py.vision.ImageSegmenter.create_from_options(options)

    mp_image = mp.Image.create_from_file(temp_file_path)
    frame = cv2.imread(temp_file_path)

    segmentation_result = segmenter.segment(mp_image)

    mask = segmentation_result.category_mask

    mask_resized = cv2.resize(mask.numpy_view(), (frame.shape[1], frame.shape[0]))
    mask_normalized = mask_resized.astype(np.float32) / 255.0
    min_y = 1_000_000
    max_y = -1
    height = frame.shape[0]
    width = frame.shape[1]

    for i, x in enumerate(mask_normalized):
        for _, y in enumerate(x):
            if y == 0:
                if i < min_y:
                    min_y = i
                if i > max_y:
                    max_y = i
    highest_point = height - min_y
    lowest_point = height - max_y

    logging.info(
        "SUCCESSFULLY CALCULATED HIGHEST AND LOWEST POINT: "
        + str(highest_point)
        + " "
        + str(lowest_point)
    )

    result = Result(height=height, width=width, data=(highest_point, lowest_point))
    os.remove(temp_file_path)

    logging.info("DELETED TEMPORARY PHOTO")

    return result


async def process_file(scan_uuid: str, process_type: ProcessType, file_extension: str):
    result = Result(height=0, width=0, data=None)

    if process_type == "video":
        result = process_video(scan_uuid, file_extension)

    elif process_type == "photo":
        result = process_photo(scan_uuid, file_extension)

    await call_callback(scan_uuid, process_type, result)


async def serverless_job(job):
    process_type = job["input"]["process_type"]
    scan_uuid = job["input"]["scan_uuid"]
    file_extension = job["input"]["file_extension"]
    asyncio.create_task(process_file(scan_uuid, process_type, file_extension))

    return "Started processing"


# Configure and start the RunPod serverless function
runpod.serverless.start(
    {
        "handler": serverless_job,
    }
)
