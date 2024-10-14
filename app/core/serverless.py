from httpx import AsyncClient, AsyncHTTPTransport
import os

from app.apimodels import ProcessType

serverless_url = os.getenv("SERVERLESS_URL") or ""
if serverless_url == "":
    raise Exception("SERVERLESS_URL environment varable not set")

RETRIES = 3

transport = AsyncHTTPTransport(retries=RETRIES)


async def call_serverless(scan_uuid: str, process_type: ProcessType) -> None:
    async with AsyncClient(transport=transport) as client:
        content = {"input": {"process_type": process_type, "scan_uuid": scan_uuid}}
        result = await client.post(
            serverless_url + "/runsync",
            json=content,
            headers={"Authorization": f"Bearer {os.getenv("SERVERLESS_TOKEN")}"},
        )
        if result.status_code != 200:
            raise Exception(result)
