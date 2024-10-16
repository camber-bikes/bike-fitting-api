import uuid

import cv2
from minio.api import Minio

import constants

def download_image(
    minio_client: Minio,
    bucket_name: str,
    scan_uuid: str,
    process_type: constants.ProcessType,
) -> str:
    """
    Download the file from the URL and store it in a temporary file.

    Args:
        minio_client (Minio): Minio client to download the file with.
        bucket_name (str): name of the bucket.
        scan_uuid (str): uuid of the scan as a string.
        process_type (ProcessType): either "photo" or "video".

    Returns:
        str: The path to the downloaded temporary file.
    """

    temp_file_name = str(uuid.uuid4()) + ".jpg"

    file_name = object_name(scan_uuid, process_type)
    file = minio_client.get_object(bucket_name, file_name)
    with open(temp_file_name, "wb") as temp_file:
        temp_file.write(file.data)

    img = cv2.imread(temp_file_name)
    if img is None:
        raise Exception(f"Downloaded file is not a valid image: {temp_file.name}")

    return temp_file_name

def object_name(scan_uuid: str, original_extension: str) -> str:
    """
    Gets the name of the object (photo or video) based on the provided extension.
    Args:
        scan_uuid (str): uuid of the scan as a string.
        original_extension (str): file extension.

    Returns:
        str: name of the object
    """

    if original_extension in ["jpg", "jpeg", "png"]:
        file_name = f"photos/body/{scan_uuid}.{original_extension}"
    elif original_extension in [".mp4", ".mov"]:
        file_name = f"videos/pedalling/{scan_uuid}{original_extension}"
    else:
        raise Exception(f"Unsupported file extension: {original_extension}")

    return file_name
