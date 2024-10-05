import uuid
from fastapi import APIRouter
from app.api.deps import SessionDep
from app.apimodels import (
    CreatePersonInformation,
    CreatePersonInformationResponse,
)
from app.dbmodels import Person


router = APIRouter()


@router.put("/information", response_model=CreatePersonInformationResponse)
async def create_person(
    session: SessionDep, body: CreatePersonInformation
) -> CreatePersonInformationResponse:
    """
    Create person with given information
    """

    person = Person(uuid=uuid.uuid4(), name=body.name, height_cm=body.height_cm)
    session.add(person)
    await session.commit()
    await session.refresh(person)

    return CreatePersonInformationResponse(
        uuid=person.uuid, name=person.name, height_cm=person.height_cm
    )
