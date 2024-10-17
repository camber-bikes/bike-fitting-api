import asyncio
import datetime
import logging

from fastapi import APIRouter, Response, UploadFile
from fastapi.exceptions import HTTPException
from sqlmodel import select
from app.core.analysis import run_analysis
from app.core.s3 import client, bucket_name
import uuid

from app.api.deps import SessionDep
from app.core.serverless import call_serverless
from app.apimodels import (
    VIDEO_CONTENT_TYPE,
    CreateScan,
    CreateScanResponse,
    ProcessResults,
    UploadResponse,
    ResultResponse,
)
from app.dbmodels import Photo, Person, Scan, ScanResult, Status, Video

router = APIRouter()


@router.post("/")
async def create_scan(session: SessionDep, body: CreateScan) -> CreateScanResponse:
    """
    Create new scan
    """

    person = await session.exec(select(Person).where(Person.uuid == body.person_uuid))
    person = person.first()
    if person is None:
        raise HTTPException(400, "person not found")

    scan = Scan(
        uuid=uuid.uuid4(), person_id=person.id, created_at=datetime.datetime.now()
    )
    session.add(scan)
    await session.commit()

    await session.refresh(scan)
    await session.refresh(person)

    return CreateScanResponse(person_uuid=person.uuid, scan_uuid=scan.uuid)


@router.post("/{scan_uuid}/photos/body")
async def upload_body_photo(
    session: SessionDep,
    file: UploadFile,
    scan_uuid: uuid.UUID,
) -> UploadResponse:
    """
    Upload a JPG photo of your body and start the processing in the background.
    Returns true if the upload was successfull
    """

    if not (
        file.content_type == "image/jpg" or file.content_type == "image/jpeg"
    ) or not (
        (file.filename or "").endswith(".jpg")
        or (file.filename or "").endswith(".jpeg")
    ):
        raise HTTPException(400, "must upload a photo in format jpg")

    scan = await session.exec(select(Scan).where(Scan.uuid == scan_uuid))
    scan = scan.first()
    if scan is None:
        raise HTTPException(400, "scan not found")

    try:
        client.put_object(
            bucket_name,
            f"photos/body/{scan.uuid}.jpg",
            data=file.file,
            length=file.size or -1,
            content_type="image/jpg",
        )
    except Exception as e:
        logging.error(e)
        raise HTTPException(500, "could not upload file")

    res = await session.exec(select(Photo).where(Photo.scan_id == scan.id))
    photo = res.first()
    if photo is None:
        photo = Photo(scan_id=scan.id, status=Status.new)
    else:
        photo.status = Status.new

    session.add(photo)
    await session.commit()

    extension = (file.filename or "").split(".")[-1]

    asyncio.create_task(
        call_serverless(str(scan_uuid), process_type="photo", file_extension=extension)
    )

    return UploadResponse(successful=True)


@router.get(
    "/{scan_uuid}/photos/body.jpg", responses={200: {"content": {"image/jpg": {}}}}
)
async def get_body_photo(
    session: SessionDep,
    scan_uuid: uuid.UUID,
) -> Response:
    """
    Get photo of body.
    """

    scan = await session.exec(select(Scan).where(Scan.uuid == scan_uuid))
    scan = scan.first()
    if scan is None:
        raise HTTPException(400, "scan not found")

    try:
        file = client.get_object(
            bucket_name,
            f"photos/body/{scan.uuid}.jpg",
        )
        return Response(content=file.read(), media_type="image/jpg")
    except Exception as e:
        logging.error(e)
        raise HTTPException(500, "could not download file")


@router.post("/{scan_uuid}/videos/pedalling")
async def upload_pedalling_video(
    session: SessionDep,
    file: UploadFile,
    scan_uuid: uuid.UUID,
) -> UploadResponse:
    """
    Upload a mp4 video of you pedalling and start the processing in the background.
    Returns true if the upload was successful.
    """

    if not (file.content_type or "").startswith(VIDEO_CONTENT_TYPE) or not (
        file.filename or ""
    ).lower().endswith((".mp4", ".mov")):
        raise HTTPException(400, "must upload a video in format mp4 or mov")
    extension = (file.filename or "").split(".")[-1]

    scan = await session.exec(select(Scan).where(Scan.uuid == scan_uuid))
    scan = scan.first()
    if scan is None:
        raise HTTPException(400, "scan not found")

    try:
        client.put_object(
            bucket_name,
            f"videos/pedalling/{scan.uuid}.{extension}",
            data=file.file,
            length=file.size or -1,
            content_type=VIDEO_CONTENT_TYPE,
        )
    except Exception as e:
        logging.error(e)
        raise HTTPException(500, "could not upload file")

    res = await session.exec(select(Video).where(Video.scan_id == scan.id))
    video = res.first()
    if video is None:
        video = Video(scan_id=scan.id, status=Status.new)
    else:
        video.status = Status.new

    session.add(video)
    await session.commit()

    asyncio.create_task(
        call_serverless(str(scan_uuid), process_type="video", file_extension=extension)
    )

    return UploadResponse(successful=True)


@router.get(
    "/{scan_uuid}/videos/pedalling.mp4", responses={200: {"content": {"video/mp4": {}}}}
)
async def get_pedalling_video(
    session: SessionDep,
    scan_uuid: uuid.UUID,
) -> Response:
    """
    Get video of pedalling.
    """

    scan = await session.exec(select(Scan).where(Scan.uuid == scan_uuid))
    scan = scan.first()
    if scan is None:
        raise HTTPException(400, "scan not found")

    try:
        file = client.get_object(
            bucket_name,
            f"videos/pedalling/{scan.uuid}.mp4",
        )
        return Response(content=file.read(), media_type=VIDEO_CONTENT_TYPE)
    except Exception as e:
        logging.error(e)
        raise HTTPException(500, "could not download file")


@router.post("/{scan_uuid}/callback", tags=["callback"])
async def process_body_photo_results(
    session: SessionDep,
    body: ProcessResults,
    scan_uuid: uuid.UUID,
) -> None:
    """
    Change the status to processed and upload the results to postgres
    """

    scan_id = await session.exec(select(Scan.id).where(Scan.uuid == scan_uuid))
    scan_id = scan_id.first()
    if scan_id is None:
        raise Exception("could not find scan")

    if body.process_type == "photo":
        photo = await session.exec(select(Photo).where(Photo.scan_id == scan_id))
        photo = photo.first()
        if photo is None:
            raise Exception("could not find photo")

        photo.status = Status.done
        photo.process_result = body.result

        session.add(photo)
    elif body.process_type == "video":
        video = await session.exec(select(Video).where(Video.scan_id == scan_id))
        video = video.first()
        if video is None:
            raise Exception("could not find video")

        video.status = Status.done
        video.process_result = body.result

        session.add(video)

    await session.commit()

    if body.process_type == "video":
        asyncio.create_task(run_analysis(scan_uuid))


@router.get("/{scan_uuid}/result")
async def get_result(
    session: SessionDep,
    scan_uuid: uuid.UUID,
) -> ResultResponse:
    """
    Args:
        session:
        scan_uuid:

    Returns:
        ResultResponse: containing a boolean if the scan is done and optionally the change parameters of the saddle
    """

    res = await session.exec(select(Scan.result).where(Scan.uuid == scan_uuid))
    result: ScanResult | None = res.first()
    if result is None or result == {}:
        return ResultResponse(done=False)

    saddle_x = result["saddle_x_cm"]
    saddle_y = result["saddle_y_cm"]
    return ResultResponse(done=True, saddle_x_cm=saddle_x, saddle_y_cm=saddle_y)
