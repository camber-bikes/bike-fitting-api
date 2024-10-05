from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlmodel import select
import uuid

from app.api.deps import SessionDep
from app.apimodels import CreateScan, CreateScanResponse
from app.dbmodels import Person, Scan


router = APIRouter()


@router.post("/", response_model=CreateScanResponse)
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
