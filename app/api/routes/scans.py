import asyncio
import logging
import random

from click.testing import Result
from fastapi import APIRouter, UploadFile
from fastapi.exceptions import HTTPException
from sqlmodel import select
from app.core.s3 import client, bucket_name
import uuid

from app.api.deps import SessionDep
from app.core.serverless import call_lambda
from app.apimodels import (
    CreateScan,
    CreateScanResponse,
    ProcessResults,
    UploadResponse,
    ResultResponse,
)
from app.dbmodels import Photo, Person, Scan, Status, Video


router = APIRouter()


@router.post("/")
async def create_scan(session: SessionDep, body: CreateScan) -> CreateScanResponse:
    """
    Create new scan
    """

    statement = select(Person).where(Person.uuid == body.person_uuid)
    person = await session.exec(statement)
    person = person.first()
    if person == None:
        raise HTTPException(400, "person not found")

    scan = Scan(uuid=uuid.uuid4(), person_id=person.id)
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
        raise HTTPException(400, "must upload a video in format jpg")

    statement = select(Scan).where(Scan.uuid == scan_uuid)
    scan = await session.exec(statement)
    scan = scan.first()
    if scan == None:
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

    photo = Photo(scan_id=scan.id, status=Status.new)
    session.add(photo)
    await session.commit()

    asyncio.create_task(call_lambda(str(scan_uuid), process_type="photo"))

    return UploadResponse(successful=True)


@router.post("/{scan_uuid}/videos/pedalling")
async def upload_pedalling_video(
    session: SessionDep,
    file: UploadFile,
    scan_uuid: uuid.UUID,
) -> UploadResponse:
    """
    Upload a mp4 photo of you pedalling and start the processing in the background.
    Returns true if the upload was successfull
    """

    if file.content_type != "video/mp4" or not (file.filename or "").endswith(".mp4"):
        raise HTTPException(400, "must upload a video in format mp4")

    statement = select(Scan).where(Scan.uuid == scan_uuid)
    scan = await session.exec(statement)
    scan = scan.first()
    if scan == None:
        raise HTTPException(400, "scan not found")

    try:
        client.put_object(
            bucket_name,
            f"videos/pedalling/{scan.uuid}.mp4",
            data=file.file,
            length=file.size or -1,
            content_type="video/mp4",
        )
    except Exception as e:
        logging.error(e)
        raise HTTPException(500, "could not upload file")

    video = Video(scan_id=scan.id, status=Status.new, process_result=None)
    session.add(video)
    await session.commit()

    asyncio.create_task(call_lambda(str(scan_uuid), process_type="video"))

    return UploadResponse(successful=True)


@router.post("/{scan_uuid}/callback")
async def process_body_photo_results(
    session: SessionDep,
    body: ProcessResults,
    scan_uuid: uuid.UUID,
) -> None:
    """
    Change the status to processed and upload the results to postgres
    """

    statement = select(Scan.id).where(Scan.uuid == scan_uuid)
    scan_id = await session.exec(statement)
    scan_id = scan_id.first()
    if scan_id == None:
        raise Exception("could not find scan")

    if body.process_type == "photo":
        statement = select(Photo).where(Photo.scan_id == scan_id)
        photo = await session.exec(statement)
        photo = photo.first()
        if photo == None:
            raise Exception("could not find photo")

        photo.status = Status.done
        photo.process_result = body.result

        session.add(photo)
    elif body.process_type == "video":
        statement = select(Video).where(Video.scan_id == scan_id)
        video = await session.exec(statement)
        video = video.first()
        if video == None:
            raise Exception("could not find video")

        video.status = Status.done
        video.process_result = body.result

        session.add(video)

    await session.commit()

    # FIXME: asynchronously run processing task if video


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
    # Commenting out the current logic for testing
    # statement = select(Scan.result).where(Scan.uuid == scan_uuid)
    # result = await session.exec(statement)
    #
    # if result == None:
    #     return ResultResponse(done=False)
    # else:
    #     saddle_x = result["saddle_x_cm"]
    #     saddle_y = result["saddle_y_cm"]
    #     return ResultResponse(done=True, saddle_x_cm=saddle_x, saddle_y_cm=saddle_y)

    # Random logic for testing purposes
    is_done = random.choice([True, False])

    if not is_done:
        return ResultResponse(done=False)
    else:
        saddle_x = random.uniform(1.0, 10.0)  # Random example value for saddle_x_cm
        saddle_y = random.uniform(1.0, 10.0)  # Random example value for saddle_y_cm
        return ResultResponse(done=True, saddle_x_cm=saddle_x, saddle_y_cm=saddle_y)
