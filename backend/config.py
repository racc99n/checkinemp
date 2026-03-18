from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./attendance.db"

    FACE_TOLERANCE: float = 0.5
    FACE_DATA_DIR: str = "./face_data"

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ADMIN_CHAT_ID: Optional[str] = None

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    LATE_THRESHOLD_MINUTES: int = 15
    SHIFT_START_TIME: str = "09:00"
    SHIFT_END_TIME: str = "18:00"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

os.makedirs(settings.FACE_DATA_DIR, exist_ok=True)
