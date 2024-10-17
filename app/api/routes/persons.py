import uuid
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.api.deps import SessionDep
from app.apimodels import (
    CreatePersonInformation,
    PersonInformationResponse,
    ScanResponse,
)
from app.dbmodels import Person, Scan


router = APIRouter()


@router.put("/information")
async def create_person_information(
    session: SessionDep, body: CreatePersonInformation
) -> PersonInformationResponse:
    """
    Create person with given information.
    """

    person = Person(uuid=uuid.uuid4(), name=body.name, height_cm=body.height_cm)
    session.add(person)
    await session.commit()
    await session.refresh(person)

    return PersonInformationResponse(
        uuid=person.uuid,
        name=person.name,
        height_cm=person.height_cm,
    )


@router.get("/{person_uuid}/information")
async def get_person_information(
    session: SessionDep, person_uuid: uuid.UUID
) -> PersonInformationResponse:
    """
    Get person information.
    """

    person = await session.exec(select(Person).where(Person.uuid == person_uuid))
    person = person.first()
    if person is None:
        raise HTTPException(400, "person not found")

    return PersonInformationResponse(
        uuid=person.uuid,
        name=person.name,
        height_cm=person.height_cm,
    )


@router.get("/{person_uuid}/scans")
async def get_scans(session: SessionDep, person_uuid: uuid.UUID) -> list[ScanResponse]:
    """
    Get all scans
    """

    person = await session.exec(select(Person).where(Person.uuid == person_uuid))
    person = person.first()
    if person is None:
        raise HTTPException(400, "person not found")

    scans = await session.exec(select(Scan).where(Scan.person_id == person.id))

    return [
        ScanResponse(scan_uuid=scan.uuid, created_at=scan.created_at) for scan in scans
    ]
