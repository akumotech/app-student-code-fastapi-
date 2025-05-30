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

    # Cookie Settings
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token_cookie"
    # For production, COOKIE_SECURE should ideally be True.
    # For development over HTTP, it might need to be False.
    # Consider making this environment-dependent, e.g. by reading another env var.
    COOKIE_SECURE: bool = False  # Default to False for local dev; override in prod
    COOKIE_SAMESITE: str = "lax"  # "lax" or "strict"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def fernet(self) -> Fernet:
        return Fernet(self.FERNET_KEY.encode("utf-8"))


settings = Settings()
