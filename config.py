from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Настройки приложения"""

    # Telegram Bot
    BOT_TOKEN: str

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/restoran_bot"

    # Google Sheets
    GOOGLE_SHEETS_ID: str = ""
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"
    AUTO_SYNC_HOUR: int = 6  # час автосинхронизации (по МСК)

    # App Settings
    DEBUG: bool = False

    # Default branch for pilot
    DEFAULT_BRANCH: str = 'Бистро "ГАВРОШ" (Пушкинская 36/69)'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
