import os
from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet
from pydantic import validator

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    DATABASE_ECHO_SQL: bool = False  # Default to False for production security
    WAKATIME_CLIENT_ID: str
    WAKATIME_CLIENT_SECRET: str
    FRONTEND_DOMAIN: str
    FERNET_KEY: str
    REDIRECT_URI: str

    ENVIRONMENT: str = "production"  # Default to production for safety

    ACCESS_TOKEN_COOKIE_NAME: str = "access_token_cookie"
    COOKIE_SECURE: bool = True  # Default to True for production security
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str = ".akumotechnology.com"

    # Video Platform Configuration
    # Meeting links are now entered manually through the admin interface
    
    # Slack API Configuration
    SLACK_BOT_TOKEN: str = ""
    SLACK_CHANNEL: str = ""  # Channel ID or name where notifications will be sent

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables

    @validator('COOKIE_SECURE')
    def validate_cookie_secure_in_production(cls, v, values):
        """Ensure secure cookies in production"""
        if values.get('ENVIRONMENT') == 'production' and not v:
            raise ValueError('COOKIE_SECURE must be True in production')
        return v

    @validator('DATABASE_ECHO_SQL')
    def validate_db_echo_in_production(cls, v, values):
        """Ensure SQL logging is disabled in production"""
        if values.get('ENVIRONMENT') == 'production' and v:
            raise ValueError('DATABASE_ECHO_SQL must be False in production')
        return v

    @property
    def fernet(self) -> Fernet:
        return Fernet(self.FERNET_KEY.encode("utf-8"))

settings = Settings()