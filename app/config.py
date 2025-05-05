from pydantic import BaseSettings

class Settings(BaseSettings):
        SECRET_KEY: str
        ALGORITHM: str
        ACCESS_TOKEN_EXPIRE_MINUTES: str
        DATABASE_URL: str
        WAKATIME_CLIENT_ID: str
        WAKATIME_CLIENT_SECRET: str
        FRONTEND_DOMAIN: str

    class Config:
        env_file = ".env"

settings = Settings()