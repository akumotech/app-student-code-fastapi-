import os
from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    DATABASE_ECHO_SQL: bool = True
    WAKATIME_CLIENT_ID: str
    WAKATIME_CLIENT_SECRET: str
    FRONTEND_DOMAIN: str
    FERNET_KEY: str
    REDIRECT_URI: str

    ENVIRONMENT: str = "development"  # "development", "production"

    ACCESS_TOKEN_COOKIE_NAME: str = "access_token_cookie"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def fernet(self) -> Fernet:
        return Fernet(self.FERNET_KEY.encode("utf-8"))

settings = Settings()