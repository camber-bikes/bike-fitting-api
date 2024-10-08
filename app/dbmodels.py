import enum
import uuid

from typing import Any, Dict, Optional
from sqlalchemy import Column
from sqlmodel import JSON, Enum, Field, SQLModel, Column


class BaseTable(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)


class Person(BaseTable, table=True):
    uuid: uuid.UUID
    name: str
    height_cm: int


class Scan(BaseTable, table=True):
    uuid: uuid.UUID
    person_id: Optional[int] = Field(foreign_key="person.id")


class Status(str, enum.Enum):
    new = "new"
    done = "done"


class Photo(BaseTable, table=True):
    scan_id: Optional[int] = Field(default=None, foreign_key="scan.id")
    status: Status = Field(sa_column=Column(Enum(Status)))
    joints: Optional[Dict[Any, Any]] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )


class Video(BaseTable, table=True):
    scan_id: Optional[int] = Field(default=None, foreign_key="scan.id")
    status: Status = Field(sa_column=Column(Enum(Status)))
    joints: Optional[list[Dict[Any, Any]]] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
