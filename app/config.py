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
    COOKIE_DOMAIN: str = ".akumotechnology.com"

    # Zoom API Configuration (OAuth - if you want to use it)
    ZOOM_ACCOUNT_ID: str = ""
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    ZOOM_USER_ID: str = ""
    
    # Alternative Video Platform Configuration (No OAuth Required)
    # Choose your preferred video platform
    DEFAULT_VIDEO_PLATFORM: str = "jitsi_meet"  # Options: google_meet, jitsi_meet, microsoft_teams, zoom_personal, manual
    
    # Zoom Personal Meeting Room (if using zoom_personal)
    ZOOM_PERSONAL_MEETING_ID: str = ""  # Your personal meeting room ID
    
    # Webex Personal Room (if using webex_personal)
    WEBEX_PERSONAL_ROOM: str = ""  # Your personal room name
    
    # Slack API Configuration
    SLACK_BOT_TOKEN: str = ""
    SLACK_CHANNEL: str = ""  # Channel ID or name where notifications will be sent

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def fernet(self) -> Fernet:
        return Fernet(self.FERNET_KEY.encode("utf-8"))

settings = Settings()