import logging
from minio import Minio
import os

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
