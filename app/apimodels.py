from pydantic import BaseModel, Field


class CreatePersonInformation(BaseModel):
    name: str = Field(default=None, min_length=1)
    height_cm: int = Field(default=None, ge=50, le=300)


class CreatePersonInformationResponse(BaseModel):
    id: int
    name: str = Field(default=None, min_length=1)
    height_cm: int = Field(default=None, ge=50, le=300)
