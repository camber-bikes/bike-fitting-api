import asyncio
import uuid
import cv2
import logging
import os
from mediapipe.python.solutions import drawing_utils, pose
import runpod
import mediapipe as mp

from dotenv import load_dotenv  # DEV purposes only
from httpx import AsyncClient, AsyncHTTPTransport
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)
from mediapipe.framework.formats import landmark_pb2
from minio import Minio
from pydantic import BaseModel
from typing import Any, Literal, Union

load_dotenv()

type ProcessType = Union[Literal["photo"], Literal["video"]]


class Result(BaseModel):
    height: int
    width: int
    joints: Any


RETRIES = 3
POSE_LANDMARKER_TASK = "pose_landmarker.task"

transport = AsyncHTTPTransport(retries=RETRIES)

backend_url = os.getenv("BACKEND_URL") or ""
if backend_url == "":
    raise Exception("BACKEND_URL environment varable not set")

client = Minio(
    os.getenv("S3_ENDPOINT") or "localhost:9000",
    access_key=os.getenv("S3_CLIENT_ID"),
    secret_key=os.getenv("S3_CLIENT_SECRET"),
    secure=os.getenv("ENV") != "DEV",
)

bucket_name = os.getenv("S3_BUCKET") or ""
if bucket_name == "":
    raise Exception("S3_BUCKET environment varable not set")

found = client.bucket_exists(bucket_name)
if not found:
    client.make_bucket(bucket_name)
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

    filename = object_name(scan_uuid, process_type)
    url = client.presigned_get_object(bucket_name, filename)

    result = Result(height=0, width=0, joints=None)

    if process_type == "video":
        base_options = python.BaseOptions(model_asset_path=POSE_LANDMARKER_TASK)
        options = vision.PoseLandmarkerOptions(
            running_mode=VisionTaskRunningMode.VIDEO,
            min_pose_detection_confidence=0.8,
            min_tracking_confidence=0.8,
            base_options=base_options,
            output_segmentation_masks=True,
        )

        detector = vision.PoseLandmarker.create_from_options(options)

        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            raise Exception("could not open video")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore

        tempfilename = str(uuid.uuid4()) + ".mp4"

        out = cv2.VideoWriter(tempfilename, fourcc, fps, (width, height))

        landmarks = []

        timestamp_ms = 0
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Reached end of video or encountered an error.")
                break

            timestamp_ms = timestamp_ms + 1000 / fps

            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            results = detector.detect_for_video(image, int(timestamp_ms))

            if not results.pose_landmarks:
                continue

            pose_landmarks = results.pose_landmarks

            pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            pose_landmarks_proto.landmark.extend(
                [
                    landmark_pb2.NormalizedLandmark(
                        x=landmark.x, y=landmark.y, z=landmark.z
                    )
                    for landmark in pose_landmarks[0]
                ]
            )

            drawing_utils.draw_landmarks(
                frame,
                pose_landmarks_proto,
                pose.POSE_CONNECTIONS,  # type:ignore
                drawing_utils.DrawingSpec(
                    color=(255, 0, 0), thickness=2, circle_radius=2
                ),  # Joints
                drawing_utils.DrawingSpec(
                    color=(0, 255, 0), thickness=2, circle_radius=2
                ),  # Connections
            )

            landmarks.append(pose_landmarks[0])
            out.write(frame)

        result = Result(height=height, width=width, joints=landmarks)
        cap.release()
        out.release()
        client.fput_object(
            bucket_name,
            filename,
            tempfilename,
            content_type=content_type,
        )

        os.remove(tempfilename)

        cv2.destroyAllWindows()

    await call_callback(scan_uuid, process_type, result)


async def serverless_job(job):
    process_type = job["input"]["process_type"]
    scan_uuid = job["input"]["scan_uuid"]
    asyncio.create_task(process(scan_uuid, process_type))

    return "Started processing"


def object_name(scan_uuid: str, process_type: ProcessType) -> str:
    filename = ""
    if process_type == "photo":
        filename = f"photos/body/{scan_uuid}.jpg"
    elif process_type == "video":
        filename = f"videos/pedalling/{scan_uuid}.mp4"

    return filename


# Configure and start the RunPod serverless function
runpod.serverless.start(
    {
        "handler": serverless_job,
    }
)
