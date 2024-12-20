from typing import Any, Literal, Union, Optional
import uuid
import datetime
from pydantic import BaseModel, Field

VIDEO_CONTENT_TYPE = "video/"


class CreatePersonInformation(BaseModel):
    name: str = Field(default=None, min_length=1)
    height_cm: int = Field(default=None, ge=50, le=300)


class PersonInformationResponse(BaseModel):
    uuid: uuid.UUID
    name: str = Field(default=None, min_length=1)
    height_cm: int = Field(default=None, ge=50, le=300)


class ScanResponse(BaseModel):
    scan_uuid: uuid.UUID
    created_at: datetime.datetime


class CreateScan(BaseModel):
    person_uuid: uuid.UUID


class CreateScanResponse(BaseModel):
    person_uuid: uuid.UUID
    scan_uuid: uuid.UUID


class UploadResponse(BaseModel):
    successful: bool


type ProcessType = Union[Literal["photo"], Literal["video"]]


class ProcessResults(BaseModel):
    process_type: ProcessType
    result: Any


class ResultResponse(BaseModel):
    done: bool
    saddle_x_cm: Optional[float] = None
    saddle_y_cm: Optional[float] = None
