from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EntityOut(BaseModel):
    id: str
    entity_type: str
    label: str
    description: str
    extra_data: dict
    model_config = ConfigDict(from_attributes=True)


class ReportRequest(BaseModel):
    title: str = Field(default="Synthetic network review", min_length=1, max_length=160)
    entity_ids: list[str] = Field(default_factory=list, max_length=100)


class AnomalyRequest(BaseModel):
    contamination: float = Field(default=0.05, ge=0.01, le=0.3)
