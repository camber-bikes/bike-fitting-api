from typing import Any
from fastapi import APIRouter
from sqlmodel import select
from app.api.deps import SessionDep
from app.models import Person


router = APIRouter()


@router.get("/")
async def helloworld(session: SessionDep) -> Any:
    """
    Hello world
    """

    statement = select(Person)
    return session.exec(statement)
