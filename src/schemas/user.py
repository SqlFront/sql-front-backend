from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints


class UserBase(BaseModel):
    login: str
    email: str
    fullname: str
    group: str


class UserCreate(UserBase):
    password: Annotated[str, StringConstraints(min_length=8)]


class UserInDB(UserBase):
    user_id: int
    total_score: int | None = None

    class Config:
        from_attributes = True


class UserPublic(UserBase):
    user_id: int
    total_score: int | None = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    login: str
    password: str


class PasswordResetRequest(BaseModel):
    login: str
    email: EmailStr
    new_password: Annotated[str, StringConstraints(min_length=8)]
