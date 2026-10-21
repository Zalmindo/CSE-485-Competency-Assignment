from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    planned = "planned"
    learning = "learning"
    mastered = "mastered"


class SkillIn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "GraphQL",
                "category": "Backend",
                "proficiency": 2,
                "status": "learning",
                "notes": "Comparing it with REST",
            }
        },
    )

    name: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=40)
    proficiency: int = Field(ge=1, le=5)
    status: Status
    notes: str = Field("", max_length=500)


class SkillPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=80)
    category: Optional[str] = Field(None, min_length=1, max_length=40)
    proficiency: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[Status] = None
    notes: Optional[str] = Field(None, max_length=500)


class Skill(BaseModel):
    id: int
    name: str
    category: str
    proficiency: int
    status: Status
    notes: str
    created_at: datetime
    updated_at: datetime
