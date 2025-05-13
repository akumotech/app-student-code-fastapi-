import requests, os
from datetime import datetime, timedelta

from app.auth.models import User
from sqlmodel import Session
from app.config import settings

def refresh_wakatime_token(user: User, session: Session) -> str:
    """Refresh WakaTime access token using refresh token."""
    refresh_token = settings.fernet.decrypt(user.wakatime_refresh_token_encrypted.encode()).decode()

    data = {
        "client_id": WAKATIME_CLIENT_ID,
        "client_secret": WAKATIME_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post("https://wakatime.com/oauth/token", data=data)

    if response.status_code != 200:
        raise Exception(f"Failed to refresh token: {response.text}")

    token_data = response.json()

    user.wakatime_access_token_encrypted = settings.fernet.encrypt(token_data["access_token"].encode()).decode()

    if "refresh_token" in token_data:
        user.wakatime_refresh_token_encrypted = settings.fernet.encrypt(token_data["refresh_token"].encode()).decode()

    session.add(user)
    session.commit()

    return token_data["access_token"]


def wakatime_api_request(user: User, session: Session, method: str, url: str, **kwargs):
    """Make an authenticated WakaTime API request, auto-refreshing if needed."""
    access_token = settings.fernet.decrypt(user.wakatime_access_token_encrypted.encode()).decode()
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {access_token}"

    response = requests.request(method, url, headers=headers, **kwargs)

    if response.status_code == 401:
        # Token expired → refresh and retry
        access_token = refresh_wakatime_token(user, session)
        headers["Authorization"] = f"Bearer {access_token}"
        response = requests.request(method, url, headers=headers, **kwargs)

    response.raise_for_status()
    return response


def fetch_today_data(user: User, session: Session):
    """Fetch today's WakaTime summary for user."""
    url = "https://wakatime.com/api/v1/users/current/status_bar/today"
    response = wakatime_api_request(user, session, "GET", url)
    return response.json()


def fetch_stats_data(user: User, session: Session):
    """Fetch WakaTime last 7 days stats for user."""
    url = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
    response = wakatime_api_request(user, session, "GET", url)
    return response.json()

def fetch_stats_range(user: User, session: Session):
    """Fetch WakaTime stats for today and the 6 days before."""
    end_date = datetime.utcnow().date()  # today
    start_date = end_date - timedelta(days=6)

    url = (
        f"https://wakatime.com/api/v1/users/current/stats"
        f"?start={start_date}&end={end_date}"
    )

    response = wakatime_api_request(user, session, "GET", url)
    return response.json()
