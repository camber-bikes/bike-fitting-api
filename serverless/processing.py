import asyncio
from typing import Literal, Union
import runpod
import logging
from minio import Minio
import os
from dotenv import load_dotenv  # DEV purposes only
from httpx import AsyncClient, AsyncHTTPTransport

load_dotenv()

type ProcessType = Union[Literal["photo"], Literal["video"]]

RETRIES = 3

transport = AsyncHTTPTransport(retries=RETRIES)

backend_url = os.getenv("BACKEND_URL") or ""
if backend_url == "":
    raise Exception("BACKEND_URL environment varable not set")

# client = Minio(
#     os.getenv("S3_ENDPOINT") or "localhost:9000",
#     access_key=os.getenv("S3_CLIENT_ID"),
#     secret_key=os.getenv("S3_CLIENT_SECRET"),
#     secure=os.getenv("ENV") != "DEV",
# )
#
# bucket_name = os.getenv("S3_BUCKET") or ""
# if bucket_name == "":
#     raise Exception("S3_BUCKET environment varable not set")
#
# found = client.bucket_exists(bucket_name)
# if not found:
#     client.make_bucket(bucket_name)
#     logging.info(f"created bucket '{bucket_name}'")


async def call_callback(scan_uuid: str, process_type: ProcessType):
    async with AsyncClient(transport=transport) as client:
        content = {
            "process_type": process_type,
            "joints": {"some": "sample", "data": 123},
        }
        result = await client.post(
            backend_url + f"/api/scans/{scan_uuid}/callback",
            json=content,
        )
        if result.status_code != 200:
            raise Exception(result)


async def process(scan_uuid: str, process_type: ProcessType):
    await asyncio.sleep(3)
    await call_callback(scan_uuid, process_type)


async def process_body_photo(job):
    print(job)
    process_type = job["input"]["process_type"]
    scan_uuid = job["input"]["scan_uuid"]
    asyncio.create_task(process(scan_uuid, process_type))

    return "Hello world"


# Configure and start the RunPod serverless function
runpod.serverless.start(
    {
        "handler": process_body_photo,
    }
)
