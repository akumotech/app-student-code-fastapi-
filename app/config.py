from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    WAKATIME_CLIENT_ID: str
    WAKATIME_CLIENT_SECRET: str
    FRONTEND_DOMAIN: str
    FERNET_KEY: str
    REDIRECT_URI: str

    class Config:
        env_file = ".env"

    @property
    def fernet(self) -> Fernet:
        return Fernet(self.FERNET_KEY)


settings = Settings()
