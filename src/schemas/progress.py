from pydantic import BaseModel, ConfigDict


class UserProgressBase(BaseModel):
    easy_tasks_solved: int
    medium_tasks_solved: int
    hard_tasks_solved: int


class UserProgresCreate(UserProgressBase):
    user_id: int


class UserProgressInDB(UserProgressBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
