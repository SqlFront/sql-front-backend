import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


def get_env(*names: str):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


class Settings(BaseSettings):
    DATABASE_URL: str = get_env("DATABASE_URL", "DB_URL")
    GAME_DATABASE_URL: str = get_env("GAME_DATABASE_URL")
    QUEST_DATABASE_URL: str = get_env("QUEST_DATABASE_URL")
    SECRET_KEY: str = get_env("SECRET_KEY", "ACCESS_TOKEN_SECRET") or "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TASK_POINTS: list = [100, 300, 500, 300, 500, 500]
    ADMIN_USERNAME: str = get_env("ADMIN_USERNAME") or "admin"
    ADMIN_PASSWORD: str = get_env("ADMIN_PASSWORD") or "admin"
    FRONTEND_URL: str = get_env("FRONTEND_URL")
    BACKEND_URL: str = get_env("BACKEND_URL")
    CORS_ORIGINS: str = get_env("CORS_ORIGINS") or ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
