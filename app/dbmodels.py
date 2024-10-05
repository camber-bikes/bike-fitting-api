import enum
import uuid

from typing import Dict, Optional
from sqlmodel import JSON, Enum, Field, SQLModel, Column


class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID
    name: str
    height_cm: int


class Scan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID
    person_id: Optional[int] = Field(foreign_key="person.id")


class Status(str, enum.Enum):
    new = "new"
    done = "done"


class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID
    scan_id: Optional[int] = Field(default=None, foreign_key="scan.id")
    status: Status = Field(sa_column=Column(Enum(Status)))
    joints: Optional[Dict] = Field(default_factory=dict, sa_column=Column(JSON))


class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid.UUID
    scan_id: Optional[int] = Field(foreign_key="scan.id")
    status: Status = Field(sa_column=Column(Enum(Status)))
    joints: list[Optional[Dict]] = Field(default_factory=dict, sa_column=Column(JSON))
