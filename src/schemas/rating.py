from typing import List

from pydantic import BaseModel, ConfigDict, Field


class UserRating(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    login: str
    fullname: str | None
    group: str | None
    total_score: int
    place: int
    achievement_icons: List[str] = Field(default_factory=list)


class RatingResponse(BaseModel):
    top_users: list[UserRating]
