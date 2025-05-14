import os
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.integrations.wakatime import fetch_today_data, fetch_stats_range
from pydantic import BaseModel
from sqlmodel import Session, select
from app.auth.models import User
from app.auth.database import engine
from app.auth.utils import get_current_active_user
from app.auth.crud import get_user_by_email
from app.integrations.model import WakaTimeCallbackPayload, WakaTimeUsageRequest
from app.config import settings

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/wakatime/today")
def wakatime_today(data: WakaTimeUsageRequest, session: Session = Depends(get_session)):
    user = get_user_by_email(session, data.email)
    if not user or not user.wakatime_access_token_encrypted:
        raise HTTPException(status_code=404, detail="User or WakaTime token not found")

    try:
        return fetch_today_data(user, session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wakatime/usage")
def wakatime_usage(data: WakaTimeUsageRequest, session: Session = Depends(get_session)):
    user = get_user_by_email(session, data.email)
    if not user or not user.wakatime_access_token_encrypted:
        raise HTTPException(status_code=404, detail="User or WakaTime token not found")

    try:
        return fetch_stats_range(user, session) ##fetch_stats_data(user, session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wakatime/authorize")
def wakatime_authorize(email: str):
    # Store email using state parameter
    url = (
        "https://wakatime.com/oauth/authorize"
        f"?client_id={settings.WAKATIME_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={settings.REDIRECT_URI}"
        f"&state={email}"
        "&scope=read_logged_time"
    )
    return url

@router.post("/wakatime/callback")
async def wakatime_callback(
    payload: WakaTimeCallbackPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    code = payload.code
    state = payload.state

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://wakatime.com/oauth/token",
            headers={"Accept": "application/json"},  # 🚀 Ask for JSON response
            data={
                "client_id": settings.WAKATIME_CLIENT_ID,
                "client_secret": settings.WAKATIME_CLIENT_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "authorization_code",
                "code": code,
            },
        )

        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to retrieve WakaTime access token: {response.status_code}, {response.text}",
            )

        token_data = response.json()
        print(f"Token data: {token_data}")

        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token not found in response")

        # Encrypt & save
        current_user.wakatime_access_token_encrypted = settings.fernet.encrypt(access_token.encode()).decode()
        session.merge(current_user)
        session.commit()

        return {"message": "WakaTime access token saved for user."}