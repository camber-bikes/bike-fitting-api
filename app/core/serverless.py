from httpx import AsyncClient, AsyncHTTPTransport
import os

from app.apimodels import ProcessType

lambda_url = os.getenv("LAMBDA_URL") or ""
if lambda_url == "":
    raise Exception("LAMBDA_URL environment varable not set")

RETRIES = 3

transport = AsyncHTTPTransport(retries=RETRIES)


async def call_lambda(scan_uuid: str, process_type: ProcessType) -> None:
    async with AsyncClient(transport=transport) as client:
        content = {"input": {"process_type": process_type, "scan_uuid": scan_uuid}}
        result = await client.post(
            lambda_url + "/runsync",
            json=content,
        )
        if result.status_code != 200:
            raise Exception(result)


# FIXME: use this code when processing the information to wait until the joints are calculated

# import asyncio
#
# from sqlmodel import select
# from sqlmodel.ext.asyncio.session import AsyncSession
#
# from app.core.db import engine
# from app.dbmodels import Photo, Scan, Status


# async def get_photo_status(session: AsyncSession, scan_id: int) -> Status:
#     statement = select(Photo.status).where(Photo.scan_id == scan_id)
#     photo_status = await session.exec(statement)
#     photo_status = photo_status.first()
#     if photo_status == None:
#         raise Exception("could not find photo")
#     return Status[photo_status]


# TIMEOUT_AFTER_S = 120
# async with AsyncSession(engine) as session:
#     statement = select(Scan.id).where(Scan.uuid == scan_uuid)
#     scan_id = await session.exec(statement)
#     scan_id = scan_id.first()
#     if scan_id == None:
#         raise Exception("could not find scan")
#
#     # Check every second if processing is ready
#     timeout_checker = 0
#     status = await get_photo_status(session, scan_id)
#     while status != Status.done:
#         if timeout_checker >= TIMEOUT_AFTER_S:
#             raise Exception(
#                 f"timeout reached, for checking status of scan with id: {scan_id}"
#             )
#
#         await asyncio.sleep(1)
#         status = await get_photo_status(session, scan_id)
#         timeout_checker += 1
