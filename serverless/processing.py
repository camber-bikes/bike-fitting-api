import asyncio
import logging
import os
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
    async with AsyncClient(transport=transport) as client:
        response = await client.post(
            backend_url + f"/api/scans/{scan_uuid}/callback",
            content=f'{{"process_type": "{process_type}", "result": {result.model_dump_json()}}}'.encode(),
            headers={"content_type": "application/json"},
        )
        if response.status_code != 200:
            raise Exception(result)


async def process(scan_uuid: str, process_type: ProcessType):
    content_type = ""
    if process_type == "photo":
        content_type = "image/jpg"
    elif process_type == "video":
        content_type = "video/mp4"

    file_name = file_operations.object_name(scan_uuid, process_type)
    url = minio_client.presigned_get_object(bucket_name, file_name)

    result = Result(height=0, width=0, data=None)

    if process_type == "video":
        base_options = mp_py.BaseOptions(
            model_asset_path=POSE_LANDMARKER_TASK,
            delegate=mp.tasks.BaseOptions.Delegate.GPU,
        )
        options = mp_py.vision.PoseLandmarkerOptions(
            running_mode=VisionTaskRunningMode.VIDEO,
            min_pose_detection_confidence=0.8,
            min_tracking_confidence=0.8,
            base_options=base_options,
            output_segmentation_masks=True,
        )

        detector = mp_py.vision.PoseLandmarker.create_from_options(options)
        cap = cv2.VideoCapture(url)

        if not cap.isOpened():
            raise Exception("Could not open video")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        output_filename = str(uuid.uuid4()) + ".mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
        out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))
        landmarks = []

        timestamp_ms = 0
        facing_direction: FacingDirection = "left"
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Reached end of video or encountered an error.")
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

            single_frame = Frame(
                knee_angle=knee_angle, elbow_angle=elbow_angle, joints=pose_landmarks
            )
            frames.append(single_frame)

        video_data = VideoData(
            frames=frames,
            facing_direction=facing_direction,
        )

        result = Result(height=height, width=width, data=video_data)
        cap.release()
        out.release()

        minio_client.fput_object(
            bucket_name,
            file_name,
            output_filename,
            content_type=content_type,
        )

    elif process_type == "photo":
        temp_file_path = file_operations.download_file(
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

        result = Result(height=height, width=width, data=(highest_point, lowest_point))
        os.remove(temp_file_path)

    await call_callback(scan_uuid, process_type, result)


async def serverless_job(job):
    process_type = job["input"]["process_type"]
    scan_uuid = job["input"]["scan_uuid"]
    asyncio.create_task(process(scan_uuid, process_type))

    return "Started processing"


# Configure and start the RunPod serverless function
runpod.serverless.start(
    {
        "handler": serverless_job,
    }
)
