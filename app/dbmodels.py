import enum
import uuid as uuids
import datetime

from typing import Any, Literal, Optional, TypedDict, Union
from sqlalchemy import Column
from sqlmodel import JSON, Enum, Field, SQLModel, Column


class BaseTable(SQLModel):
    id: int = Field(default=None, primary_key=True)


class Person(BaseTable, table=True):
    uuid: uuids.UUID = Field(
        default_factory=uuids.uuid4,
        unique=True,
    )
    name: str
    height_cm: int


class Scan(BaseTable, table=True):
    uuid: uuids.UUID = Field(
        default_factory=uuids.uuid4,
        unique=True,
    )
    person_id: Optional[int] = Field(default=None, foreign_key="person.id")
    result: Optional[Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime.datetime


class Status(str, enum.Enum):
    new = "new"
    done = "done"


class Photo(BaseTable, table=True):
    scan_id: int = Field(default=None, foreign_key="scan.id", unique=True)
    status: Status = Field(sa_column=Column(Enum(Status)))
    process_result: Optional[Any] = Field(default=None, sa_column=Column(JSON))


class Video(BaseTable, table=True):
    scan_id: int = Field(default=None, foreign_key="scan.id", unique=True)
    status: Status = Field(sa_column=Column(Enum(Status)))
    process_result: Optional[Any] = Field(default=None, sa_column=Column(JSON))


class PhotoResult(TypedDict):
    width: int
    height: int
    data: tuple[int, int]  # Maximum, minimum


type FacingDirection = Union[Literal["left"], Literal["right"]]


class Frame(TypedDict):
    knee_angle: float
    elbow_angle: float
    joints: Any


class VideoData(TypedDict):
    frames: list[Frame]
    facing_direction: FacingDirection


class VideoResult(TypedDict):
    width: int
    height: int
    data: VideoData


class ScanResult(TypedDict):
    saddle_x_cm: float
    saddle_y_cm: float
